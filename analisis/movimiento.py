"""Prueba cómo viene evolucionando la tormenta: el avance de los rayos y la llegada de la nube fría.

La idea salió de la madrugada del 2026-11-03: los rayos estuvieron horas a unos 45 km y el modelo subió
tarde. El modelo ve la última hora; aquí se le agrega lo ocurrido en las últimas 1, 2 y 3 horas.

- Rayos: cómo cambió la cercanía del rayo más cercano, la cercanía máxima en 3 horas y cómo cambió la
  cantidad de rayos a menos de 60 km. No se prueba la dirección: el historial no la guarda.
- Nube fría: cómo cambió la temperatura sobre el centro y cuánto creció el área fría a 30, 60 y 100 km.

Se compara con el modelo de la página de cada anticipación, de 1 a 5 horas. Reentrenado cada trimestre
desde 2025 con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, para adoptarlo en un pronóstico: mejora el Brier en al menos
0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero, mejora en al menos 6 de los 8
trimestres y además mejora en las horas secas con el rayo más cercano a 30-60 km, que es el caso que se
quiere arreglar. Es más estricta que otras porque la idea salió de un solo caso.

Escribe analisis/movimiento.md.
"""

import time

import numpy as np
import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, CADA_10MIN, COMPLETO, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS, PREVIA,
                      RAYOS, VAPOR, VARIABLES, cargar, previas)
from viento_mar import adoptar, comparar, por_trimestres

HORAS = (1, 2, 3)
RAYOS_MOV = ([f'cercania_cambio_{h}h' for h in HORAS] + ['cercania_max_3h']
             + [f'rayos60_cambio_{h}h' for h in HORAS])
AREAS = ('ir_frio_30_area', 'ir_frio_60_area', 'ir_frio_100_area')
NUBE_MOV = [f'tb_cambio_{h}h' for h in HORAS] + [f'{a}_cambio_{h}h' for a in AREAS for h in HORAS]


def movimiento_cada_10min():
    """Cambios hasta el minuto t. Una hora son 6 pasos de 10 minutos."""
    rayos, ir, tb = CADA_10MIN['rayos'], CADA_10MIN['ir'], CADA_10MIN['tibias']
    indice = pd.date_range(min(rayos.index.min(), ir.index.min()), max(rayos.index.max(), ir.index.max()), freq='10min')
    rayos, ir, tb = rayos.reindex(indice), ir.reindex(indice), tb.reindex(indice)
    r60 = np.log1p(np.expm1(rayos[['rayos_15_1h', 'rayos_30_1h', 'rayos_60_1h']]).sum(axis=1, min_count=3))
    v = pd.DataFrame(index=indice)
    for h in HORAS:
        v[f'cercania_cambio_{h}h'] = rayos['cercania_1h'] - rayos['cercania_1h'].shift(6 * h)
        v[f'rayos60_cambio_{h}h'] = r60 - r60.shift(6 * h)
        v[f'tb_cambio_{h}h'] = tb['tb_centro'] - tb['tb_centro'].shift(6 * h)
        for a in AREAS:
            v[f'{a}_cambio_{h}h'] = ir[a] - ir[a].shift(6 * h)
    v['cercania_max_3h'] = rayos['cercania_1h'].rolling(13, min_periods=13).max()
    return v


def en_franja(d):
    """Sin lluvia en las 3 horas anteriores y el rayo más cercano a 30-60 km."""
    c = d['cercania_1h'].to_numpy()
    return (d['lluvia_previa_3h'].to_numpy() == 0) & (c >= np.exp(-2)) & (c < np.exp(-1)) & (d['rayos_60_1h'].to_numpy() > 0)


def resumen_franja(te, sel, pb, pv):
    y = te['y'].to_numpy()
    eb, ev = ((pb[sel] - y[sel]) ** 2).sum(), ((pv[sel] - y[sel]) ** 2).sum()
    llovio = sel & (y == 1)
    return {'filas': int(sel.sum()), 'dias': te.index[sel].normalize().nunique(), 'lluvia': float(y[sel].mean()) * 100,
            'mejora': (1 - ev / eb) * 100, 'p_antes': float(np.median(pb[llovio])) * 100,
            'p_ahora': float(np.median(pv[llovio])) * 100, 'det_antes': float((pb[llovio] >= 0.3).mean()) * 100,
            'det_ahora': float((pv[llovio] >= 0.3).mean()) * 100,
            'falsas_antes': int(((pb >= 0.3) & sel & (y == 0)).sum()), 'falsas_ahora': int(((pv >= 0.3) & sel & (y == 0)).sum())}


def main():
    t0 = time.time()
    df, _ = cargar()
    mov = movimiento_cada_10min()
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
            t = d.index - pd.Timedelta(hours=k) + pd.Timedelta(minutes=m)
            d[RAYOS_MOV + NUBE_MOV] = mov.reindex(t)[RAYOS_MOV + NUBE_MOV].to_numpy()
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        sel = en_franja(d[d.index >= DESDE])
        pb = por_trimestres(d, base, 'y_hora')
        assert comparar(te, pb, pb)['auc_base'] > 0.85, k
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        salida[nombre] = {}
        for v, nuevas in (('Rayos', RAYOS_MOV), ('Nube fría', NUBE_MOV), ('Ambas', RAYOS_MOV + NUBE_MOV)):
            pv = por_trimestres(d, base + nuevas, 'y_hora')
            salida[nombre][v] = (comparar(te, pb, pv), resumen_franja(te, sel, pb, pv))
        print(f'{nombre}: {time.time() - t0:.0f} s; filas {len(d):,}; base Brier {salida[nombre]["Rayos"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{v} {r[0]["mejora"]:+.2f} % (franja {r[1]["mejora"]:+.2f} %)' for v, r in salida[nombre].items()), flush=True)
    escribir(salida)


def cumple(r, s):
    return adoptar(r) and s['mejora'] > 0


def escribir(salida):
    o = ['# Avance de los rayos y llegada de la nube fría', '',
         'Lo escribe `analisis/movimiento.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
         'mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye '
         'el cero, mejora en al menos 6 de 8 trimestres y mejora también en la franja de rayos a 30-60 km.', '',
         '| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en la franja (%) | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (r, s) in vs.items():
            o.append(f'| {n} | {v} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] | '
                     f'{r["ganados"]}/{r["trimestres"]} | {num(s["mejora"])} | {"sí" if cumple(r, s) else "no"} |')
    o += ['', '## En la franja: horas secas con el rayo más cercano a 30-60 km', '',
          'Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: '
          'predicciones de 30 % o más en que no llovió.', '',
          '| Pronóstico | Variante | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |',
          '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, (_, s) in vs.items():
            o.append(f'| {n} | {v} | {s["filas"]:,} | {s["dias"]} | {s["lluvia"]:.1f} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det_antes"]:.0f} % → {s["det_ahora"]:.0f} % | {s["falsas_antes"]:,} → {s["falsas_ahora"]:,} |')
    (AQUI / 'movimiento.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/movimiento.md')


if __name__ == '__main__':
    main()
