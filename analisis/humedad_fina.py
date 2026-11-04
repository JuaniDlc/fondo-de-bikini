"""Segunda prueba de humedad, más fina: cada ventana por separado, con punto de rocío y por temporada.

Sigue a analisis/humedad_movil.py, que probó las ventanas juntas y no cumplió la regla. Aquí, para cada fuente
y cada ventana de 3, 6, 12 y 24 horas, se agregan solo dos variables: el promedio y la diferencia entre ahora y
ese promedio. Fuentes: humedad relativa de GFS, punto de rocío de GFS (mide mejor el agua en el aire que la
humedad relativa) y temperatura menos punto de rocío del aeropuerto. Cada promedio termina en la hora en que
se pronostica.

Se compara con el modelo de la página de cada anticipación, de 1 a 6 horas. Reentrenado cada trimestre desde
2025 con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos 0,5 %,
el intervalo de 99,9 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8 trimestres. Es
más estricta que otras porque son 72 comparaciones y sigue a una prueba sin señal en estos mismos datos. Una
mejora solo en la temporada lluviosa no basta para adoptar: se anotaría para revisarla con datos nuevos.

Escribe analisis/humedad_fina.md.
"""

import time

import numpy as np
import pandas as pd

from combinado import AQUI, DESDE, REMUESTREOS, num
from entrenar import (ADELANTOS, ADELANTOS_IR, CADA_10MIN, COMPLETO, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PREVIA,
                      RAYOS, VAPOR, VARIABLES, cargar, previas)
from viento_mar import comparar, por_trimestres

VENTANAS = (3, 6, 12, 24)
FUENTES = {'Humedad relativa de GFS': 'hr', 'Punto de rocío de GFS': 'td', 'Aeropuerto (T − Td)': 'sp'}


def medias(serie, prefijo):
    s = serie.sort_index()
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq='h'))
    v = pd.DataFrame(index=s.index)
    for h in VENTANAS:
        media = s.rolling(h, min_periods=max(2, h * 3 // 4)).mean()
        v[f'{prefijo}_media_{h}h'] = media
        v[f'{prefijo}_menos_media_{h}h'] = s - media
    return v


def intervalo_999(te, pb, pv):
    y = te['y'].to_numpy()
    dias = pd.factorize(te.index.floor('D'))[0]
    nb, nv = np.bincount(dias, (pb - y) ** 2), np.bincount(dias, (pv - y) ** 2)
    idx = np.random.default_rng(0).integers(0, len(nb), (REMUESTREOS, len(nb)))
    m = (1 - nv[idx].sum(axis=1) / nb[idx].sum(axis=1)) * 100
    return float(np.percentile(m, 0.05)), float(np.percentile(m, 99.95))


def mejora(y, pb, pv):
    return (1 - ((pv - y) ** 2).sum() / ((pb - y) ** 2).sum()) * 100


def main():
    t0 = time.time()
    df, p = cargar()
    v = pd.concat([medias(p['relative_humidity_2m_gfs_seamless'], 'hr'), medias(p['dew_point_2m_gfs_seamless'], 'td'),
                   medias(CADA_10MIN['senales']['sp'], 'sp')], axis=1)
    nuevas = list(v.columns)
    filas = []
    for k in ADELANTOS:
        base = (VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
                + COMPLETO.get(k, []))
        cols = list(dict.fromkeys(base + ['y_hora']))
        partes = []
        for m in MINUTOS:
            d = previas(df, k, m)[cols].copy()
            d[nuevas] = v.reindex(d.index - pd.Timedelta(hours=k))[nuevas].to_numpy()
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        y = te['y'].to_numpy()
        lluviosa = np.isin(te.index.month, [1, 2, 3, 4])
        pb = por_trimestres(d, base, 'y_hora')
        assert comparar(te, pb, pb)['auc_base'] > 0.85, k
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        for fuente, prefijo in FUENTES.items():
            for h in VENTANAS:
                pv = por_trimestres(d, base + [f'{prefijo}_media_{h}h', f'{prefijo}_menos_media_{h}h'], 'y_hora')
                r = comparar(te, pb, pv)
                bajo, alto = intervalo_999(te, pb, pv)
                filas.append({'pronostico': nombre, 'fuente': fuente, 'ventana': h, 'mejora': r['mejora'], 'bajo': bajo, 'alto': alto,
                              'ganados': r['ganados'], 'trimestres': r['trimestres'],
                              'lluviosa': mejora(y[lluviosa], pb[lluviosa], pv[lluviosa]), 'seca': mejora(y[~lluviosa], pb[~lluviosa], pv[~lluviosa])})
        mejor = max((f for f in filas if f['pronostico'] == nombre), key=lambda f: f['mejora'])
        print(f'{nombre}: {time.time() - t0:.0f} s; mejor {mejor["fuente"]} {mejor["ventana"]} h {mejor["mejora"]:+.2f} %', flush=True)
    escribir(filas)


def cumple(f):
    return f['mejora'] >= 0.5 and f['bajo'] > 0 and f['ganados'] >= 6


def escribir(filas):
    o = ['# Humedad, prueba fina', '',
         'Lo escribe `analisis/humedad_fina.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
         'mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99,9 % no incluye '
         'el cero y mejora en al menos 6 de 8 trimestres. Temporada lluviosa: enero a abril.', '',
         f'De {len(filas)} comparaciones, cumplen la regla: {sum(cumple(f) for f in filas)}.', '',
         '| Pronóstico | Fuente | Ventana | Mejora (%) | Intervalo de 99,9 % | Trimestres | Lluviosa (%) | Seca (%) | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|---|']
    for f in filas:
        o.append(f'| {f["pronostico"]} | {f["fuente"]} | {f["ventana"]} h | {num(f["mejora"])} | [{num(f["bajo"])}; {num(f["alto"])}] | '
                 f'{f["ganados"]}/{f["trimestres"]} | {num(f["lluviosa"])} | {num(f["seca"])} | {"sí" if cumple(f) else "no"} |')
    (AQUI / 'humedad_fina.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/humedad_fina.md')


if __name__ == '__main__':
    main()
