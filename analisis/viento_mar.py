"""Prueba solo el viento y la temperatura del mar, sin la presión de vapor, de 1 a 6 horas.

Sigue a analisis/combinado.py, con lo que allí quedó como límite: usa los seis minutos de la hora
como la página, agrega las horas 5 y 6 con su modelo (sin infrarrojo ni vapor de GOES) y recalibra
las próximas 6 h con Platt.

La idea salió de los resultados del combinado, sobre estas mismas horas, así que la regla es más
estricta. Fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al
menos 0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos 6 de
los 8 trimestres.

Necesita analisis/combinado_descargar.py. Escribe analisis/viento_mar.md.
"""

import os
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score

from combinado import AQUI, DESDE, MAR, REMUESTREOS, VIENTO, agregar_variables, num, predecir
from entrenar import (ADELANTOS, ADELANTOS_IR, CALIBRA_DESDE, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PERSISTENCIA,
                      PREVIA, RAYOS, VAPOR, VARIABLES, cargar, fuera_de_muestra, platt, previas)

NUEVAS = VIENTO + MAR


def comparar(te, base, variante):
    y = te['y'].to_numpy()
    eb, ev = (base - y) ** 2, (variante - y) ** 2
    dias = pd.factorize(te.index.floor('D'))[0]
    nb, nv = np.bincount(dias, eb), np.bincount(dias, ev)
    idx = np.random.default_rng(0).integers(0, len(nb), (REMUESTREOS, len(nb)))
    mejoras = (1 - nv[idx].sum(axis=1) / nb[idx].sum(axis=1)) * 100
    trimestres = te.index.to_period('Q')
    ganados = [ev[trimestres == q].sum() < eb[trimestres == q].sum() for q in trimestres.unique()]
    return {'mejora': (1 - ev.sum() / eb.sum()) * 100, 'bajo': np.percentile(mejoras, 0.5),
            'alto': np.percentile(mejoras, 99.5), 'ganados': int(sum(ganados)), 'trimestres': len(ganados),
            'brier_base': eb.mean(), 'brier': ev.mean(), 'auc_base': roc_auc_score(y, base), 'auc': roc_auc_score(y, variante)}


def adoptar(r):
    return r['mejora'] >= 0.5 and r['bajo'] > 0 and r['ganados'] >= 6


def por_trimestres(d, cols, y):
    inicios = pd.date_range(DESDE, d.index.max(), freq='QS')
    fines = [*inicios[1:], d.index.max() + pd.Timedelta(hours=1)]
    partes = Parallel(n_jobs=os.cpu_count(), backend='threading')(
        delayed(predecir)(d, cols, y, a, b) for a, b in zip(inicios, fines))
    return np.concatenate(partes)


def recalibrado(d, cols, y):
    """Como la página: Platt ajustado con predicciones fuera de muestra, solo de antes de cada trimestre."""
    z, ys, indice = fuera_de_muestra(d, cols, y, CALIBRA_DESDE)
    z, indice = np.asarray(z), pd.DatetimeIndex(indice)
    salida = []
    for inicio in pd.date_range(DESDE, d.index.max(), freq='QS'):
        fin = inicio + pd.offsets.QuarterBegin(startingMonth=1)
        antes, ahora = indice < inicio, (indice >= inicio) & (indice < fin)
        a, b = platt(z[antes], ys[antes])
        salida.append(1 / (1 + np.exp(-(a * z[ahora] + b))))
    return np.concatenate(salida)


def main():
    t0 = time.time()
    df, p = cargar()
    df, futuro = agregar_variables(df, p)
    resultados, detalle = {}, []
    columnas_nuevas = list(futuro.columns)
    for k in ADELANTOS:
        base = VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
        cols = list(dict.fromkeys(base + NUEVAS + ['y_hora', 'mes']))
        d = pd.concat([previas(df, k, m)[cols] for m in MINUTOS]).dropna().sort_index(kind='stable')
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        pb, pv = por_trimestres(d, base, 'y_hora'), por_trimestres(d, base + NUEVAS, 'y_hora')
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        resultados[nombre] = comparar(te, pb, pv)
        lluviosa = np.isin(te.index.month, [1, 2, 3, 4])
        for sub, sel in (('Temporada lluviosa', lluviosa), ('Temporada seca', ~lluviosa)):
            detalle.append((nombre, sub, int(sel.sum()), comparar(te[sel], pb[sel], pv[sel])))
        print(f'{nombre}: {time.time() - t0:.0f} s; base AUC {resultados[nombre]["auc_base"]:.3f}; '
              f'mejora {resultados[nombre]["mejora"]:+.2f} %', flush=True)
        # El modelo de la página ya se validó: si aquí sale mucho peor, la prueba está mal.
        assert resultados[nombre]['auc_base'] > 0.85, nombre

    seis = df.drop(columns=columnas_nuevas).join(futuro)
    base = VARIABLES['6h'] + PERSISTENCIA + RAYOS + VAPOR
    d = seis.dropna(subset=base + NUEVAS + ['y_6h']).sort_index(kind='stable')
    te = d.loc[d.index >= DESDE, ['y_6h']].rename(columns={'y_6h': 'y'})
    pb, pv = recalibrado(d, base, 'y_6h'), recalibrado(d, base + NUEVAS, 'y_6h')
    resultados['Próximas 6 h'] = comparar(te, pb, pv)
    lluviosa = np.isin(te.index.month, [1, 2, 3, 4])
    for sub, sel in (('Temporada lluviosa', lluviosa), ('Temporada seca', ~lluviosa)):
        detalle.append(('Próximas 6 h', sub, int(sel.sum()), comparar(te[sel], pb[sel], pv[sel])))
    assert resultados['Próximas 6 h']['auc_base'] > 0.85
    print(f'Próximas 6 h: {time.time() - t0:.0f} s; mejora {resultados["Próximas 6 h"]["mejora"]:+.2f} %', flush=True)
    escribir(resultados, detalle)


def escribir(resultados, detalle):
    o = ['# Solo viento y temperatura del mar, de 1 a 6 horas', '',
         'Lo escribe `analisis/viento_mar.py`. Reentrenado cada trimestre desde 2025 solo con lo anterior, sobre las '
         'mismas horas y con todos los minutos. Mejora: cuánto baja el Brier frente al modelo de la página (positivo '
         'es mejor).', '',
         'Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el '
         'cero y mejora en al menos 6 de 8 trimestres. Es más estricta que en `combinado.py` porque la idea salió de '
         'esas mismas horas.', '',
         '| Pronóstico | Brier página | Brier con viento y mar | Mejora (%) | Intervalo de 99 % | Trimestres | AUC página | AUC nuevo | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|---|']
    for n, r in resultados.items():
        o.append(f'| {n} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] | '
                 f'{r["ganados"]}/{r["trimestres"]} | {r["auc_base"]:.3f} | {r["auc"]:.3f} | {"sí" if adoptar(r) else "no"} |')
    o += ['', '## Por temporada', '', '| Pronóstico | Temporada | Predicciones | Mejora (%) | Intervalo de 99 % |', '|---|---|---|---|---|']
    for n, sub, filas, r in detalle:
        o.append(f'| {n} | {sub} | {filas:,} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] |')
    (AQUI / 'viento_mar.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/viento_mar.md')


if __name__ == '__main__':
    main()
