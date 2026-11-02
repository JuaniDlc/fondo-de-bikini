"""Prueba las nubes bajas de GOES (analisis/nubes_bajas_historial.py), para la lluvia sin rayos.

Canales 3, 7, 13 y 15: cuánta nube tibia hay, la diferencia 13 − 7 de noche (nubes bajas), la 13 − 15
(nube gruesa o alta delgada) y, de día, la luz que refleja la nube corregida por la altura del sol.

Se compara el modelo de la página con: las nubes bajas; las nubes bajas sumadas a las señales del
aeropuerto y las nubes tibias (analisis/senales_aeropuerto.py); y esa suma frente a las señales y
las nubes tibias sin las nubes bajas, para ver cuánto agregan. Reentrenado cada trimestre desde 2025
con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8
trimestres. Es la misma de senales_aeropuerto.py, para comparar con ella.

Escribe analisis/nubes_bajas.md.
"""

import time

import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, BAJAS, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PERSISTENCIA, PREVIA,
                      RAYOS, SENALES, TIBIAS, VAPOR, VARIABLES, bajas_cada_10min, cargar, previas, senales_por_hora,
                      tibias_cada_10min)
from senales_aeropuerto import agregar, inicios_sin_rayos
from viento_mar import adoptar, comparar, por_trimestres, recalibrado

OTRAS = SENALES + TIBIAS


def variantes(base):
    return {'Nubes bajas': (base, base + BAJAS), 'Señales, tibias y nubes bajas': (base, base + OTRAS + BAJAS),
            'Lo que agregan las nubes bajas': (base + OTRAS, base + OTRAS + BAJAS)}


def main():
    t0 = time.time()
    df, p = cargar()
    senales, tibias, bajas = senales_por_hora(), tibias_cada_10min(), bajas_cada_10min()
    print('Datos por variable:', bajas.notna().mean().round(3).min(), 'desde', bajas.index.min(), 'hasta', bajas.index.max(), flush=True)
    temperatura = p['temperature_2m_gfs_seamless']
    salida = {}
    for k in ADELANTOS:
        base = VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
        cols = list(dict.fromkeys(base + ['y_hora']))
        partes = []
        for m in MINUTOS:
            d = agregar(previas(df, k, m)[cols], senales, tibias, temperatura, k, m)
            d[BAJAS] = bajas.reindex(d.index - pd.Timedelta(hours=k) + pd.Timedelta(minutes=m))[BAJAS].to_numpy()
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        cache = {}
        pred = lambda c: cache.setdefault(tuple(c), por_trimestres(d, c, 'y_hora'))  # noqa: E731, B023
        salida[nombre] = {}
        for v, (a, b) in variantes(base).items():
            pa, pb = pred(a), pred(b)
            salida[nombre][v] = (comparar(te, pa, pb), inicios_sin_rayos(d, te, 'lluvia_previa_3h', 'y_hora', pa, pb))
        assert comparar(te, pred(base), pred(base))['auc_base'] > 0.85, nombre
        print(f'{nombre}: {time.time() - t0:.0f} s; base Brier {salida[nombre]["Nubes bajas"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{v} {r[0]["mejora"]:+.2f} %' for v, r in salida[nombre].items()), flush=True)
    base = VARIABLES['6h'] + PERSISTENCIA + RAYOS + VAPOR
    d = agregar(df, senales, tibias, temperatura, 0)
    d[BAJAS] = bajas.reindex(d.index)[BAJAS].to_numpy()
    d = d.dropna(subset=base + OTRAS + BAJAS + ['y_6h']).sort_index(kind='stable')
    te = d.loc[d.index >= DESDE, ['y_6h']].rename(columns={'y_6h': 'y'})
    cache = {}
    pred = lambda c: cache.setdefault(tuple(c), recalibrado(d, c, 'y_6h'))  # noqa: E731
    salida['Próximas 6 h'] = {}
    for v, (a, b) in variantes(base).items():
        pa, pb = pred(a), pred(b)
        salida['Próximas 6 h'][v] = (comparar(te, pa, pb), inicios_sin_rayos(d, te, 'lluvia_3h', 'y_6h', pa, pb))
    print('Próximas 6 h: ' + '; '.join(f'{v} {r[0]["mejora"]:+.2f} %' for v, r in salida['Próximas 6 h'].items()), flush=True)
    escribir(salida)


def escribir(salida):
    o = ['# Nubes bajas de GOES, para la lluvia sin rayos', '',
         'Lo escribe `analisis/nubes_bajas.py`. Mejora: cuánto baja el Brier (positivo es mejor). «Lo que agregan las '
         'nubes bajas» compara con las señales del aeropuerto y las nubes tibias; las otras dos, con el modelo de la '
         'página. Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye '
         'el cero y mejora en al menos 6 de 8 trimestres.', '',
         '| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (r, _) in vs.items():
            o.append(f'| {n} | {v} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | '
                     f'[{num(r["bajo"])}; {num(r["alto"])}] | {r["ganados"]}/{r["trimestres"]} | {"sí" if adoptar(r) else "no"} |')
    o += ['', '## En los inicios de lluvia sin rayos', '',
          'Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que '
          'sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o '
          'más llovió.', '',
          '| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |',
          '|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (_, s) in vs.items():
            o.append(f'| {n} | {v} | {s["lluvia"]:,} | {num(s["mejora"])} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det30_antes"]:.0f} % → {s["det30_ahora"]:.0f} % | {s["acierto30"]:.0f} % ({s["alertas30"]:,}) |')
    (AQUI / 'nubes_bajas.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/nubes_bajas.md')


if __name__ == '__main__':
    main()
