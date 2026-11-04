"""Prueba las ráfagas del reporte del aeropuerto y los cambios de presión en otros plazos.

- Ráfagas: si hubo en la última hora y en las últimas 3, la mayor en nudos y la velocidad media del viento.
  El modelo lee el viento del reporte, pero ignora las ráfagas.
- Presión: cambio en 1, 6, 12 y 24 horas, y diferencia con el promedio de esa misma hora en los 7 días
  anteriores. El de 24 horas y esa diferencia quitan el ciclo diario de la presión.

Todo es del reporte de la última hora terminada (T − k), como en vivo. Se compara con el modelo de la página
de cada anticipación, de 1 a 6 horas. Reentrenado cada trimestre desde 2025 con lo anterior, los seis minutos
de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8
trimestres. Además se informa cuánto cambia en los inicios de lluvia sin rayos.

Escribe analisis/rafagas_presion.md.
"""

import re
import time

import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, COMPLETO, DATOS, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PREVIA, RAYOS,
                      VAPOR, VARIABLES, cargar, leer_reporte, previas)
from senales_aeropuerto import inicios_sin_rayos
from viento_mar import adoptar, comparar, por_trimestres

RAFAGAS = ['rafaga', 'rafaga_3h', 'rafaga_kt', 'viento_kt']
PRESION = ['pres_cambio_1h', 'pres_cambio_6h', 'pres_cambio_12h', 'pres_cambio_24h', 'pres_anomalia_7d']
VIENTO = re.compile(r'\b\d{3}(\d{2,3})(?:G(\d+))?KT\b')


def leer_viento(metar):
    cuerpo = re.split(r'\s(?=NOSIG|TEMPO|BECMG|RMK)', str(metar))[0]
    m = VIENTO.search(cuerpo)
    return (float(m[1]), float(m[2]) if m[2] else 0.0) if m else (0.0, 0.0)


def reporte_por_hora():
    m = pd.read_csv(DATOS / 'metar_segu.csv')
    hora = pd.to_datetime(m['valid']).dt.ceil('h')
    f = pd.DataFrame([leer_viento(x) for x in m['metar']], columns=['viento_kt', 'rafaga_kt'], index=hora)
    f['pres'] = [leer_reporte(x)['pres'] for x in m['metar']]
    g = f.groupby(level=0)
    h = pd.DataFrame({'viento_kt': g['viento_kt'].mean(), 'rafaga_kt': g['rafaga_kt'].max(), 'pres': g['pres'].mean()})
    h = h.reindex(pd.date_range(h.index.min(), h.index.max(), freq='h'))
    h['pres'] = h['pres'].ffill(limit=2)
    h['rafaga'] = (h['rafaga_kt'] > 0).astype(float).where(h['rafaga_kt'].notna())
    h['rafaga_3h'] = h['rafaga'].rolling(3, min_periods=1).max()
    for n in (1, 6, 12, 24):
        h[f'pres_cambio_{n}h'] = h['pres'] - h['pres'].shift(n)
    misma = pd.concat([h['pres'].shift(24 * d) for d in range(1, 8)], axis=1).mean(axis=1)
    h['pres_anomalia_7d'] = h['pres'] - misma
    return h[RAFAGAS + PRESION]


def main():
    t0 = time.time()
    df, _ = cargar()
    v = reporte_por_hora()
    print('Horas con ráfagas:', round(float(v['rafaga'].mean()) * 100, 2), '%', flush=True)
    nuevas = RAFAGAS + PRESION
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
        for variante, extra in (('Ráfagas', RAFAGAS), ('Presión', PRESION), ('Ambas', nuevas)):
            pv = por_trimestres(d, base + extra, 'y_hora')
            salida[nombre][variante] = (comparar(te, pb, pv), inicios_sin_rayos(d, te, 'lluvia_previa_3h', 'y_hora', pb, pv))
        print(f'{nombre}: {time.time() - t0:.0f} s; filas {len(d):,}; base Brier {salida[nombre]["Ráfagas"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{a} {r[0]["mejora"]:+.2f} % (inicios {r[1]["mejora"]:+.2f} %)' for a, r in salida[nombre].items()), flush=True)
    escribir(salida)


def escribir(salida):
    o = ['# Ráfagas y cambios de presión', '',
         'Lo escribe `analisis/rafagas_presion.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
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
    (AQUI / 'rafagas_presion.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/rafagas_presion.md')


if __name__ == '__main__':
    main()
