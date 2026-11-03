"""Prueba que los rayos no bajen de más la probabilidad cuando hay una tormenta cerca.

La madrugada del 2026-11-03, la hora 02-03 pasó de 63 a 31 % mientras los rayos bajaban, y llovió. Tres
versiones, comparadas con el modelo de la página de cada anticipación, de 1 a 5 horas:

- Rayos solo suman: los coeficientes de los rayos a menos de 60 km, también los que dependen del minuto,
  no pueden ser negativos.
- Rayos de 20 minutos suavizados: esas variables toman el máximo de los últimos 30 minutos, para que un
  rayo que sale de la ventana no mueva tanto el número.
- No baja tanto: el mismo modelo de la página, pero en una hora seca con rayos a menos de 60 km, la
  probabilidad es el promedio entre la de ese minuto y la más alta de los minutos anteriores de esa hora.

Reentrenado cada trimestre desde 2025 con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero, mejora en al menos 6 de los 8
trimestres y además mejora en las horas secas con rayos a menos de 60 km. Como solo cambia esas pocas
horas, también se informa cuánto mejora ahí, pero no reemplaza a la regla.

Escribe analisis/rayos_suaves.md.
"""

import os
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import minimize

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, CADA_10MIN, COMPLETO, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PREVIA,
                      RAYOS, VAPOR, VARIABLES, cargar, logistica, pesos, previas)
from movimiento import resumen_franja
from viento_mar import adoptar, comparar, por_trimestres

CERCA = ['rayos_15_1h', 'rayos_30_1h', 'rayos_60_1h', 'rayos_60_20m', 'cercania_20m', 'cercania_1h']
SOLO_SUMAN = CERCA + [f'{c}_x_fr' for c in CERCA]
VEINTE = ['rayos_60_20m', 'cercania_20m']
PASOS_SUAVE = 3  # 30 minutos en pasos de 10


def con_cotas(tr, te, cols, y, hasta, C=0.5):
    """La misma regresión de entrenar.logistica, con los coeficientes de SOLO_SUMAN mayores o iguales a 0."""
    m, s = tr[cols].mean().to_numpy(), tr[cols].std(ddof=0).to_numpy().copy()
    s[s == 0] = 1
    X, Xt = (tr[cols].to_numpy() - m) / s, (te[cols].to_numpy() - m) / s
    yy, w = tr[y].to_numpy(), pesos(tr.index, hasta)
    signo = 2 * yy - 1

    def costo(b):
        z = X @ b[1:] + b[0]
        margen = signo * z
        perdida = np.logaddexp(0, -margen)
        g = -signo * w / (1 + np.exp(margen))
        return C * (w * perdida).sum() + 0.5 * b[1:] @ b[1:], np.r_[C * g.sum(), C * (X.T @ g) + b[1:]]

    cotas = [(None, None)] + [(0, None) if c in SOLO_SUMAN else (None, None) for c in cols]
    b = minimize(costo, np.zeros(len(cols) + 1), jac=True, method='L-BFGS-B', bounds=cotas, options={'maxiter': 2000}).x
    return 1 / (1 + np.exp(-(Xt @ b[1:] + b[0])))


def trimestres_con_cotas(d, cols, y):
    inicios = pd.date_range(DESDE, d.index.max(), freq='QS')
    fines = [*inicios[1:], d.index.max() + pd.Timedelta(hours=1)]

    def uno(a, b):
        return con_cotas(d[d.index < a], d[(d.index >= a) & (d.index < b)], cols, y, a)

    return np.concatenate(Parallel(n_jobs=os.cpu_count(), backend='threading')(
        delayed(uno)(a, b) for a, b in zip(inicios, fines)))


def seco_con_rayos(t):
    return (t['lluvia_previa_3h'].to_numpy() == 0) & (t['cercania_1h'].to_numpy() >= np.exp(-2))


def no_baja_tanto(t, p):
    """Promedio con la más alta de los minutos anteriores de la misma hora, en las horas secas con rayos."""
    mayor = pd.Series(p, index=t.index).groupby(level=0).cummax().to_numpy()
    return np.where(seco_con_rayos(t), (p + mayor) / 2, p)


def caidas(t, te, pb, pv):
    """Horas secas con 40 % o más al minuto 0 que bajaron 10 puntos o más al minuto 50, en la página."""
    f = pd.DataFrame({'fr': t['fraccion'].to_numpy(), 'pb': pb, 'pv': pv, 'y': te['y'].to_numpy(),
                      'seco': t['lluvia_previa_3h'].to_numpy() == 0}, index=t.index)
    a, z = f[f['fr'] == 0], f[np.isclose(f['fr'], 5 / 6)]
    u = a.join(z[['pb', 'pv']], rsuffix='_50', how='inner')
    u = u[u['seco'] & (u['pb'] >= 0.4) & (u['pb_50'] <= u['pb'] - 0.1)]
    if u.empty:
        return {'horas': 0, 'antes': float('nan'), 'ahora': float('nan'), 'llovio': float('nan')}
    return {'horas': len(u), 'antes': u['pb_50'].mean() * 100, 'ahora': u['pv_50'].mean() * 100, 'llovio': u['y'].mean() * 100}


def main():
    t0 = time.time()
    df, _ = cargar()
    rayos = CADA_10MIN['rayos']
    suave = rayos[VEINTE].reindex(pd.date_range(rayos.index.min(), rayos.index.max(), freq='10min')).rolling(PASOS_SUAVE, min_periods=1).max()
    salida = {}
    for k in ADELANTOS:
        if k == 6:
            continue
        base = (VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
                + COMPLETO.get(k, []))
        cols = list(dict.fromkeys(base + ['y_hora']))
        partes = []
        for m in MINUTOS:
            d = previas(df, k, m)[cols].copy()
            hay = suave.reindex(d.index - pd.Timedelta(hours=k) + pd.Timedelta(minutes=m)).to_numpy()
            for i, c in enumerate(VEINTE):
                d[f'{c}_suave'] = hay[:, i]
                d[f'{c}_suave_x_fr'] = hay[:, i] * (m / 60)
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        cambio = {c: f'{c}_suave' for c in VEINTE} | {f'{c}_x_fr': f'{c}_suave_x_fr' for c in VEINTE}
        suaves = [cambio.get(c, c) for c in base]
        t = d[d.index >= DESDE]
        te = t[['y_hora']].rename(columns={'y_hora': 'y'})
        sel = seco_con_rayos(t)
        pb = por_trimestres(d, base, 'y_hora')
        assert comparar(te, pb, pb)['auc_base'] > 0.85, k
        if k == 1:
            # Sin ninguna cota activa debe dar lo mismo que el modelo de siempre, o la regresión está mal.
            a = pd.Timestamp('2026-01-01')
            ref = logistica(d[d.index < a], base, 'y_hora', a).predict_proba(d[(d.index >= a) & (d.index < a + pd.Timedelta(days=30))][base])[:, 1]
            libre = globals()['SOLO_SUMAN']
            globals()['SOLO_SUMAN'] = []
            prueba = con_cotas(d[d.index < a], d[(d.index >= a) & (d.index < a + pd.Timedelta(days=30))], base, 'y_hora', a)
            globals()['SOLO_SUMAN'] = libre
            print('Diferencia media con la regresión de siempre:', round(float(np.abs(ref - prueba).mean()), 5), flush=True)
            assert np.abs(ref - prueba).mean() < 0.002
        versiones = {'Rayos solo suman': trimestres_con_cotas(d, base, 'y_hora'),
                     'Rayos de 20 minutos suavizados': por_trimestres(d, suaves, 'y_hora'),
                     'No baja tanto': no_baja_tanto(t, pb)}
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        salida[nombre] = {v: (comparar(te, pb, p), resumen_franja(te, sel, pb, p), caidas(t, te, pb, p)) for v, p in versiones.items()}
        print(f'{nombre}: {time.time() - t0:.0f} s; base Brier {salida[nombre]["No baja tanto"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{v} {r[0]["mejora"]:+.2f} % (secas con rayos {r[1]["mejora"]:+.2f} %)' for v, r in salida[nombre].items()), flush=True)
    escribir(salida)


def cumple(r, s):
    return adoptar(r) and s['mejora'] > 0


def escribir(salida):
    o = ['# Que los rayos no bajen de más la probabilidad', '',
         'Lo escribe `analisis/rayos_suaves.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
         'mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye '
         'el cero, mejora en al menos 6 de 8 trimestres y mejora en las horas secas con rayos a menos de 60 km.', '',
         '| Pronóstico | Versión | Brier antes | Brier con la versión | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en secas con rayos (%) | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (r, s, _) in vs.items():
            o.append(f'| {n} | {v} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] | '
                     f'{r["ganados"]}/{r["trimestres"]} | {num(s["mejora"])} | {"sí" if cumple(r, s) else "no"} |')
    o += ['', '## Horas que caen', '',
          'Horas secas que marcaban 40 % o más al minuto 0 y bajaron 10 puntos o más al minuto 50 en el modelo de la '
          'página. Valores al minuto 50. Son pocas horas: es una pista, no una prueba.', '',
          '| Pronóstico | Versión | Horas | Marcaba la página | Marca la versión | Llovió |', '|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (_, _, c) in vs.items():
            o.append(f'| {n} | {v} | {c["horas"]} | {c["antes"]:.0f} % | {c["ahora"]:.0f} % | {c["llovio"]:.0f} % |')
    o += ['', '## En las horas secas con rayos a menos de 60 km', '',
          'Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: '
          'predicciones de 30 % o más en que no llovió.', '',
          '| Pronóstico | Versión | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |',
          '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (_, s, _) in vs.items():
            o.append(f'| {n} | {v} | {s["filas"]:,} | {s["dias"]} | {s["lluvia"]:.1f} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det_antes"]:.0f} % → {s["det_ahora"]:.0f} % | {s["falsas_antes"]:,} → {s["falsas_ahora"]:,} |')
    (AQUI / 'rayos_suaves.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/rayos_suaves.md')


if __name__ == '__main__':
    main()
