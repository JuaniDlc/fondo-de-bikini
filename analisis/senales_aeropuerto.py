"""Prueba más señales del reporte del aeropuerto y la temperatura de las nubes tibias, para la lluvia sin rayos.

- Reporte del aeropuerto (METAR): chubascos o tormenta cerca (VCSH, VCTS, TS), nubes de tormenta (CB),
  altura de las nubes, visibilidad, temperatura menos punto de rocío, presión, viento y la tendencia
  con lluvia que anuncia el observador (TEMPO, BECMG). De la última hora que ya pasó, como en vivo.
- Nubes tibias (canal 13): la temperatura sobre el aeropuerto y a 15 km, sin el tope de 270 K que usa
  el modelo, y cuánto más fría que el aire. Las nubes bajas son tibias: el modelo actual no las ve.

Reentrenado cada trimestre desde 2025 con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8
trimestres. El intervalo es de 99 % porque la señal de VCSH se vio antes en estos mismos datos.
Además se informa cuánto cambia en los inicios de lluvia sin rayos, que es lo que se quiere mejorar.

Escribe analisis/senales_aeropuerto.md.
"""

import time

import numpy as np
import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PERSISTENCIA, PREVIA, RAYOS,
                      SENALES, TIBIAS, VAPOR, VARIABLES, cargar, previas, senales_por_hora, tibias_cada_10min)
from viento_mar import adoptar, comparar, por_trimestres, recalibrado

VARIANTES = {'Señales del aeropuerto': SENALES, 'Nubes tibias': TIBIAS, 'Ambas': SENALES + TIBIAS}


def agregar(d, senales, tibias, temperatura, k, m=0):
    """Datos de T − k + m minutos para las nubes y de la última hora terminada (T − k) para el reporte."""
    t = d.index - pd.Timedelta(hours=k)
    d = d.copy()
    d[SENALES] = senales.reindex(t).to_numpy()
    d[['tb_centro', 'tb_15']] = tibias.reindex(t + pd.Timedelta(minutes=m))[['tb_centro', 'tb_15']].to_numpy()
    d['t_menos_tb'] = temperatura.reindex(d.index).to_numpy() + 273.15 - d['tb_centro']
    return d


def inicios_sin_rayos(d, te, previa, y, pb, pv):
    """Horas secas antes, sin rayos a menos de 60 km: qué tanto cambia y cuánto se detecta."""
    d = d[d.index >= DESDE]
    sin = (d[previa].to_numpy() == 0) & (d[['rayos_15_1h', 'rayos_30_1h', 'rayos_60_1h']].sum(axis=1).to_numpy() == 0)
    llovio = te['y'].to_numpy() == 1
    eb, ev = (pb[sin] - te['y'].to_numpy()[sin]) ** 2, (pv[sin] - te['y'].to_numpy()[sin]) ** 2
    con = sin & llovio
    alto = sin & (pv >= 0.3)
    return {'filas': int(sin.sum()), 'lluvia': int(con.sum()), 'mejora': (1 - ev.sum() / eb.sum()) * 100,
            'p_antes': float(np.median(pb[con])) * 100, 'p_ahora': float(np.median(pv[con])) * 100,
            'det30_antes': float((pb[con] >= 0.3).mean()) * 100, 'det30_ahora': float((pv[con] >= 0.3).mean()) * 100,
            'acierto30': float(te['y'].to_numpy()[alto].mean()) * 100 if alto.any() else float('nan'), 'alertas30': int(alto.sum())}


def main():
    t0 = time.time()
    df, p = cargar()
    senales, tibias = senales_por_hora(), tibias_cada_10min()
    temperatura = p['temperature_2m_gfs_seamless']
    nuevas = list(dict.fromkeys(SENALES + TIBIAS))
    salida = {}
    for k in ADELANTOS:
        base = VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
        cols = list(dict.fromkeys(base + ['y_hora']))
        d = pd.concat([agregar(previas(df, k, m)[cols], senales, tibias, temperatura, k, m) for m in MINUTOS])
        d = d.dropna().sort_index(kind='stable')
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        pb = por_trimestres(d, base, 'y_hora')
        salida[nombre] = {}
        for v, extra in VARIANTES.items():
            pv = por_trimestres(d, base + extra, 'y_hora')
            salida[nombre][v] = (comparar(te, pb, pv), inicios_sin_rayos(d, te, 'lluvia_previa_3h', 'y_hora', pb, pv))
        assert salida[nombre]['Ambas'][0]['auc_base'] > 0.85, nombre
        print(f'{nombre}: {time.time() - t0:.0f} s; ' + '; '.join(
            f'{v} {r[0]["mejora"]:+.2f} %' for v, r in salida[nombre].items()), flush=True)
    base = VARIABLES['6h'] + PERSISTENCIA + RAYOS + VAPOR
    d = agregar(df, senales, tibias, temperatura, 0).dropna(subset=base + nuevas + ['y_6h']).sort_index(kind='stable')
    te = d.loc[d.index >= DESDE, ['y_6h']].rename(columns={'y_6h': 'y'})
    pb = recalibrado(d, base, 'y_6h')
    salida['Próximas 6 h'] = {}
    for v, extra in VARIANTES.items():
        pv = recalibrado(d, base + extra, 'y_6h')
        salida['Próximas 6 h'][v] = (comparar(te, pb, pv), inicios_sin_rayos(d, te, 'lluvia_3h', 'y_6h', pb, pv))
    print(f'Próximas 6 h: {time.time() - t0:.0f} s; ' + '; '.join(
        f'{v} {r[0]["mejora"]:+.2f} %' for v, r in salida['Próximas 6 h'].items()), flush=True)
    escribir(salida)


def escribir(salida):
    o = ['# Señales del aeropuerto y nubes tibias, para la lluvia sin rayos', '',
         'Lo escribe `analisis/senales_aeropuerto.py`. Mejora: cuánto baja el Brier frente al modelo de la página '
         '(positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de '
         '99 % no incluye el cero y mejora en al menos 6 de 8 trimestres.', '',
         '| Pronóstico | Variante | Brier página | Brier nuevo | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |',
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
    (AQUI / 'senales_aeropuerto.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/senales_aeropuerto.md')


if __name__ == '__main__':
    main()
