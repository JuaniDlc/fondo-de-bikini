"""Prueba la dirección de la tormenta: de qué lado están los rayos y hacia dónde se mueven.

Sigue a analisis/movimiento.py, que no cumplió la regla pero no podía probar la dirección. Con los datos
de analisis/rayos_direccion_historial.py, en cada momento:

- Posición y sectores: dónde está el centro de los rayos de la última hora, en km al este y al norte del
  centro de Guayaquil, y cuántos rayos hubo en cada uno de los 8 sectores a menos de 60 km.
- Movimiento: cuánto se movió ese centro al este y al norte frente a 1 y 2 horas antes, cuánto de ese
  movimiento apunta hacia Guayaquil y en qué fracción de la distancia que falta se avanzó.

Se compara con el modelo de la página de cada anticipación, de 1 a 5 horas. Reentrenado cada trimestre
desde 2025 con lo anterior, los seis minutos de la hora y las mismas horas.

Regla fijada antes de ver los resultados, la misma de analisis/movimiento.py, para adoptarlo en un
pronóstico: mejora el Brier en al menos 0,5 %, el intervalo de 99 % (remuestreando días) no incluye el
cero, mejora en al menos 6 de los 8 trimestres y además mejora en las horas secas con el rayo más cercano
a 30-60 km.

Escribe analisis/direccion.md.
"""

import time

import numpy as np
import pandas as pd

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, ARCHIVOS_HORA, CADA_10MIN, COMPLETO, DATOS, FRACCION_IR, FRACCION_RAYOS,
                      IR, MINUTOS, PREVIA, RAYOS, VAPOR, VARIABLES, cargar, previas)
from movimiento import cumple, en_franja, resumen_franja
from viento_mar import comparar, por_trimestres

SECTORES = [f's{i}' for i in range(8)]
POSICION = ['centro_x', 'centro_y'] + [f'sector_{i}' for i in range(8)]
HORAS = (1, 2)
MOVIMIENTO = [f'{c}_{h}h' for h in HORAS for c in ('mueve_x', 'mueve_y', 'avance', 'avance_relativo')]
ESCALA_KM = 100


def direccion_cada_10min():
    """Como los rayos del modelo: en el minuto T, los bloques de T − 60 a T − 10 (en hora local)."""
    b = pd.concat([pd.read_csv(a) for a in sorted((DATOS / 'rayos-direccion').glob('direccion-*.csv'))])
    b['bloque'] = (pd.to_datetime(b['bloque'], utc=True).dt.tz_convert('America/Guayaquil').dt.tz_localize(None))
    b = b.drop_duplicates('bloque').set_index('bloque').sort_index()
    b = b.reindex(pd.date_range(b.index.min(), b.index.max(), freq='10min'))
    hora = b.rolling(6).sum()
    n = hora['n']
    x, y = (hora['suma_x'] / n.where(n > 0)), (hora['suma_y'] / n.where(n > 0))  # sin rayos, no hay centro
    v = pd.DataFrame(index=b.index)
    v['n_1h'] = n
    v['centro_x'], v['centro_y'] = (x / ESCALA_KM).fillna(0), (y / ESCALA_KM).fillna(0)
    for i, s in enumerate(SECTORES):
        v[f'sector_{i}'] = np.log1p(hora[s])
    distancia = np.hypot(x, y)
    for h in HORAS:
        dx, dy = x - x.shift(6 * h), y - y.shift(6 * h)  # km que se movió el centro
        # Hacia Guayaquil es positivo: lo que se movió en la dirección que va del centro de rayos a la ciudad.
        avance = -(dx * x + dy * y) / distancia.where(distancia > 0)
        v[f'mueve_x_{h}h'] = (dx / ESCALA_KM).fillna(0)
        v[f'mueve_y_{h}h'] = (dy / ESCALA_KM).fillna(0)
        v[f'avance_{h}h'] = (avance / ESCALA_KM).fillna(0)
        v[f'avance_relativo_{h}h'] = (avance / distancia.where(distancia > 0)).clip(-2, 2).fillna(0)
    v[hora['archivos'] < 0.8 * ARCHIVOS_HORA] = np.nan  # faltan archivos: no se sabe
    v.index = v.index + pd.Timedelta(minutes=10)
    return v


def comprobar_alineacion(v):
    """Debe contar los mismos rayos que el modelo en el mismo minuto, o las horas están corridas."""
    r = CADA_10MIN['rayos']
    total = np.expm1(r[[f'rayos_{k}_1h' for k in (15, 30, 60, 100, 150)]]).sum(axis=1, min_count=5)
    comunes = pd.concat([total, v['n_1h']], axis=1, keys=['a', 'b']).dropna()
    assert len(comunes) > 100000, len(comunes)
    diferencia = (comunes['a'] - comunes['b']).abs()
    assert comunes['b'].sum() > 0 and diferencia.sum() / comunes['b'].sum() < 0.001, diferencia.sum() / comunes['b'].sum()


def main():
    t0 = time.time()
    df, _ = cargar()
    v = direccion_cada_10min()
    comprobar_alineacion(v)
    nuevas = POSICION + MOVIMIENTO
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
            d[nuevas] = v.reindex(d.index - pd.Timedelta(hours=k) + pd.Timedelta(minutes=m))[nuevas].to_numpy()
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        te = d.loc[d.index >= DESDE, ['y_hora']].rename(columns={'y_hora': 'y'})
        sel = en_franja(d[d.index >= DESDE])
        pb = por_trimestres(d, base, 'y_hora')
        assert comparar(te, pb, pb)['auc_base'] > 0.85, k
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        salida[nombre] = {}
        for variante, extra in (('Posición y sectores', POSICION), ('Movimiento', MOVIMIENTO), ('Todo', nuevas)):
            pv = por_trimestres(d, base + extra, 'y_hora')
            salida[nombre][variante] = (comparar(te, pb, pv), resumen_franja(te, sel, pb, pv))
        print(f'{nombre}: {time.time() - t0:.0f} s; filas {len(d):,}; base Brier {salida[nombre]["Todo"][0]["brier_base"]:.4f}; ' + '; '.join(
            f'{a} {r[0]["mejora"]:+.2f} % (franja {r[1]["mejora"]:+.2f} %)' for a, r in salida[nombre].items()), flush=True)
    escribir(salida)


def escribir(salida):
    o = ['# Dirección de la tormenta', '',
         'Lo escribe `analisis/direccion.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es '
         'mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye '
         'el cero, mejora en al menos 6 de 8 trimestres y mejora también en la franja de rayos a 30-60 km.', '',
         '| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en la franja (%) | ¿Cumple? |',
         '|---|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for a, (r, s) in vs.items():
            o.append(f'| {n} | {a} | {r["brier_base"]:.4f} | {r["brier"]:.4f} | {num(r["mejora"])} | [{num(r["bajo"])}; {num(r["alto"])}] | '
                     f'{r["ganados"]}/{r["trimestres"]} | {num(s["mejora"])} | {"sí" if cumple(r, s) else "no"} |')
    o += ['', '## En la franja: horas secas con el rayo más cercano a 30-60 km', '',
          'Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: '
          'predicciones de 30 % o más en que no llovió.', '',
          '| Pronóstico | Variante | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |',
          '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for a, (_, s) in vs.items():
            o.append(f'| {n} | {a} | {s["filas"]:,} | {s["dias"]} | {s["lluvia"]:.1f} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det_antes"]:.0f} % → {s["det_ahora"]:.0f} % | {s["falsas_antes"]:,} → {s["falsas_ahora"]:,} |')
    (AQUI / 'direccion.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/direccion.md')


if __name__ == '__main__':
    main()
