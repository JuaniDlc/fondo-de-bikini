"""Prueba los promedios móviles de humedad de las últimas 3, 6, 12 y 24 horas.

El modelo ve la humedad de cada hora, no si el aire lleva horas cargándose. Dos fuentes:

- GFS: humedad relativa a 2 m, el promedio de las últimas horas y la diferencia entre ahora y ese promedio.
- Aeropuerto: temperatura menos punto de rocío del reporte (menor es más húmedo), igual. Es observada.

Cada promedio termina en la hora en que se pronostica (T − k), así no usa nada del futuro. Se compara con el
modelo de la página de cada anticipación, de 1 a 6 horas. Reentrenado cada trimestre desde 2025 con lo
anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8
trimestres. Además se informa cuánto cambia en los inicios de lluvia sin rayos.

Escribe analisis/humedad_movil.md.
"""

import time

import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, CADA_10MIN, COMPLETO, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PREVIA,
                      RAYOS, VAPOR, VARIABLES, cargar, previas)
from senales_aeropuerto import inicios_sin_rayos
from viento_mar import adoptar, comparar, por_trimestres

VENTANAS = (3, 6, 12, 24)
GFS = [f'hr_media_{h}h' for h in VENTANAS] + [f'hr_menos_media_{h}h' for h in VENTANAS]
AEROPUERTO = [f'sp_media_{h}h' for h in VENTANAS] + [f'sp_menos_media_{h}h' for h in VENTANAS]


def medias(serie, prefijo):
    """Promedios que terminan en cada hora; faltando pocas horas se calculan igual, como máximo un cuarto."""
    s = serie.sort_index()
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq='h'))
    v = pd.DataFrame(index=s.index)
    for h in VENTANAS:
        media = s.rolling(h, min_periods=max(2, h * 3 // 4)).mean()
        v[f'{prefijo}_media_{h}h'] = media
        v[f'{prefijo}_menos_media_{h}h'] = s - media
    return v


def main():
    t0 = time.time()
    df, p = cargar()
    v = medias(p['relative_humidity_2m_gfs_seamless'], 'hr').join(medias(CADA_10MIN['senales']['sp'], 'sp'), how='outer')
    nuevas = GFS + AEROPUERTO
    salida = {}
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
        pb = por_trimestres(d, base, 'y_hora')
        assert comparar(te, pb, pb)['auc_base'] > 0.85, k
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        salida[nombre] = {}
        for variante, extra in (('GFS', GFS), ('Aeropuerto', AEROPUERTO), ('Ambas', nuevas)):
            pv = por_trimestres(d, base + extra, 'y_hora')
            salida[nombre][variante] = (comparar(te, pb, pv), inicios_sin_rayos(d, te, 'lluvia_previa_3h', 'y_hora', pb, pv))
        print(f'{nombre}: {time.time() - t0:.0f} s; filas {len(d):,}; base Brier {salida[nombre]["GFS"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{a} {r[0]["mejora"]:+.2f} % (inicios {r[1]["mejora"]:+.2f} %)' for a, r in salida[nombre].items()), flush=True)
    escribir(salida)


def escribir(salida):
    o = ['# Promedios móviles de humedad', '',
         'Lo escribe `analisis/humedad_movil.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
         'mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye '
         'el cero y mejora en al menos 6 de 8 trimestres.', '',
         '| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for a, (r, _) in vs.items():
            o.append(f'| {n} | {a} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] | '
                     f'{r["ganados"]}/{r["trimestres"]} | {"sí" if adoptar(r) else "no"} |')
    o += ['', '## En los inicios de lluvia sin rayos', '',
          'Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que '
          'sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o '
          'más llovió.', '',
          '| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |',
          '|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for a, (_, s) in vs.items():
            o.append(f'| {n} | {a} | {s["lluvia"]:,} | {num(s["mejora"])} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det30_antes"]:.0f} % → {s["det30_ahora"]:.0f} % | {s["acierto30"]:.0f} % ({s["alertas30"]:,}) |')
    (AQUI / 'humedad_movil.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/humedad_movil.md')


if __name__ == '__main__':
    main()
