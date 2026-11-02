"""Prueba separar el modelo: uno para cuando hay tormenta eléctrica y otro para cuando no.

Hay tormenta si hubo rayos a menos de 60 km en la hora antes de pronosticar, la misma definición de
analisis/senales_aeropuerto.py. «Todo» son las variables de la página, las señales del aeropuerto,
las nubes tibias y las nubes bajas (analisis/nubes_bajas.py). Variantes:

- Un modelo con todo: la referencia, para saber si lo que ayuda es separar o solo tener más variables.
- Dos por regla, variables de la página: usa uno u otro según haya tormenta.
- Dos por regla, con todo: igual, con todas las variables.
- Dos por regla, sin tormenta con variables elegidas: el de tormenta usa las de la página; el otro,
  hasta 40 de todas, de mayor a menor correlación con la lluvia, sin las que tengan correlación
  mayor que 0,9 con una ya elegida. Se eligen cada trimestre solo con lo anterior.
- Tercer modelo que pesa: un modelo da la probabilidad de que haya rayos en la hora pronosticada y con
  ella se ponderan dos modelos, entrenados con las horas que tuvieron y que no tuvieron rayos.
- El porcentaje mayor: de los dos por regla con todo, siempre el más alto.

Regla fijada antes de ver los resultados, para adoptar la separación en un pronóstico: mejora el Brier
en al menos 0,5 %, el intervalo de 99 % (remuestreando días) no incluye el cero y mejora en al menos
6 de los 8 trimestres. Cada variante se compara con un solo modelo de las mismas variables: las de la
página con la página, y las demás con el modelo con todo.

Reentrenado cada trimestre desde 2025 con lo anterior, los seis minutos de la hora y las mismas horas;
las próximas 6 h llevan Platt, como la página. Escribe analisis/dos_modelos.md.
"""

import os
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from combinado import AQUI, DESDE, num
from entrenar import (ADELANTOS, ADELANTOS_IR, BAJAS, CADA_10MIN, CALIBRA_DESDE, FRACCION_IR, FRACCION_RAYOS, IR, MINUTOS,
                      PERSISTENCIA, PREVIA, RAYOS, VAPOR, VARIABLES, bajas_cada_10min, cargar, logistica, platt, previas,
                      senales_por_hora, tibias_cada_10min)
from nubes_bajas import OTRAS
from senales_aeropuerto import agregar, inicios_sin_rayos
from viento_mar import adoptar, comparar

CERCA = ['rayos_15_1h', 'rayos_30_1h', 'rayos_60_1h']
MAXIMO_ELEGIDAS = 40
PARECIDAS = 0.9


def elegir(candidatas):
    """Las de mayor correlación con la lluvia, sin las que dicen casi lo mismo que una ya elegida."""
    def cols(tr, y):
        orden = tr[candidatas].corrwith(tr[y]).abs().fillna(0).sort_values(ascending=False)
        r = tr[orden.index].corr().abs().to_numpy()
        elegidas = []
        for i in range(len(orden)):
            if all(r[i, j] <= PARECIDAS for j in elegidas):
                elegidas.append(i)
            if len(elegidas) == MAXIMO_ELEGIDAS:
                break
        return [orden.index[i] for i in elegidas]
    return cols


def ajustar(d, cols, y, filas, desde):
    """z (logit) de todas las horas desde «desde»; cada trimestre se entrena con las filas marcadas anteriores."""
    inicios = pd.date_range(desde, d.index.max(), freq='QS')
    fines = [*inicios[1:], d.index.max() + pd.Timedelta(hours=1)]

    def uno(a, b):
        tr = d[(d.index < a) & filas]
        c = cols(tr, y) if callable(cols) else cols
        return logistica(tr, c, y, a).decision_function(d.loc[(d.index >= a) & (d.index < b), c])

    return np.concatenate(Parallel(n_jobs=os.cpu_count(), backend='threading')(
        delayed(uno)(a, b) for a, b in zip(inicios, fines)))


def recalibrar(z, d, y, filas):
    """Platt ajustado con predicciones fuera de muestra de las filas marcadas, solo de antes de cada trimestre."""
    desde = d.index >= CALIBRA_DESDE
    indice, ys, sel = d.index[desde], d[y].to_numpy()[desde], filas[desde]
    salida = []
    for inicio in pd.date_range(DESDE, d.index.max(), freq='QS'):
        fin = inicio + pd.offsets.QuarterBegin(startingMonth=1)
        antes, ahora = (indice < inicio) & sel, (indice >= inicio) & (indice < fin)
        a, b = platt(z[antes], ys[antes])
        salida.append(1 / (1 + np.exp(-(a * z[ahora] + b))))
    return np.concatenate(salida)


def evaluar(d, base, y, previa, seis):
    todo = list(dict.fromkeys(base + OTRAS + BAJAS))
    todas = np.ones(len(d), dtype=bool)
    tormenta = d[CERCA].sum(axis=1).to_numpy() > 0
    futura = d['rayos_despues'].to_numpy() > 0
    d = d.assign(tormenta_despues=futura.astype(int))

    def prob(cols, objetivo, filas):
        if seis:
            return recalibrar(ajustar(d, cols, objetivo, filas, CALIBRA_DESDE), d, objetivo, filas)
        return 1 / (1 + np.exp(-ajustar(d, cols, objetivo, filas, DESDE)))

    te = d.loc[d.index >= DESDE, [y]].rename(columns={y: 'y'})
    hay = tormenta[d.index >= DESDE]
    pagina, uno = prob(base, y, todas), prob(todo, y, todas)
    base_con, base_sin = prob(base, y, tormenta), prob(base, y, ~tormenta)
    todo_con, todo_sin = prob(todo, y, tormenta), prob(todo, y, ~tormenta)
    elegido_sin = prob(elegir(todo), y, ~tormenta)
    llovio_con, llovio_sin = prob(todo, y, futura), prob(todo, y, ~futura)
    peso = prob(todo, 'tormenta_despues', todas)
    variantes = {
        'Un modelo con todo': (pagina, uno),
        'Dos por regla, variables de la página': (pagina, np.where(hay, base_con, base_sin)),
        'Dos por regla, con todo': (uno, np.where(hay, todo_con, todo_sin)),
        'Dos por regla, sin tormenta con variables elegidas': (uno, np.where(hay, base_con, elegido_sin)),
        'Tercer modelo que pesa': (uno, peso * llovio_con + (1 - peso) * llovio_sin),
        'El porcentaje mayor': (uno, np.maximum(todo_con, todo_sin)),
    }
    salida = {}
    for nombre, (ref, p) in variantes.items():
        salida[nombre] = {'total': comparar(te, ref, p), 'sin': comparar(te[~hay], ref[~hay], p[~hay]),
                          'con': comparar(te[hay], ref[hay], p[hay]),
                          'inicios': inicios_sin_rayos(d, te, previa, y, pagina, p)}
    assert salida['Un modelo con todo']['total']['auc_base'] > 0.85, y
    return salida, float(hay.mean()) * 100


def main():
    t0 = time.time()
    df, p = cargar()
    senales, tibias, bajas = senales_por_hora(), tibias_cada_10min(), bajas_cada_10min()
    temperatura = p['temperature_2m_gfs_seamless']
    rayos = CADA_10MIN['rayos']
    salida, parte, elegidas = {}, {}, None
    for k in ADELANTOS:
        base = VARIABLES['hora'] + PREVIA + RAYOS + (IR + VAPOR + FRACCION_IR if k in ADELANTOS_IR else FRACCION_RAYOS)
        cols = list(dict.fromkeys(base + ['y_hora']))
        partes = []
        for m in MINUTOS:
            d = agregar(previas(df, k, m)[cols], senales, tibias, temperatura, k, m)
            d[BAJAS] = bajas.reindex(d.index - pd.Timedelta(hours=k) + pd.Timedelta(minutes=m))[BAJAS].to_numpy()
            # Lo que pasó en la hora pronosticada: solo para entrenar el tercer modelo.
            d['rayos_despues'] = rayos.reindex(d.index)[CERCA].sum(axis=1, min_count=3).to_numpy()
            partes.append(d)
        d = pd.concat(partes).dropna().sort_index(kind='stable')
        nombre = 'Hora en curso' if k == 1 else f'Hora con {k} h'
        salida[nombre], parte[nombre] = evaluar(d, base, 'y_hora', 'lluvia_previa_3h', False)
        if k == 1:
            todo = list(dict.fromkeys(base + OTRAS + BAJAS))
            sin = d[(d[CERCA].sum(axis=1) == 0) & (d.index < DESDE)]
            elegidas = sin[elegir(todo)(sin, 'y_hora')].corrwith(sin['y_hora'])
        print(f'{nombre}: {time.time() - t0:.0f} s; ' + '; '.join(
            f'{v} {r["total"]["mejora"]:+.2f} %' for v, r in salida[nombre].items()), flush=True)
    base = VARIABLES['6h'] + PERSISTENCIA + RAYOS + VAPOR
    d = agregar(df, senales, tibias, temperatura, 0)
    d[BAJAS] = bajas.reindex(d.index)[BAJAS].to_numpy()
    siguientes = [rayos.reindex(d.index + pd.Timedelta(hours=h))[CERCA].sum(axis=1, min_count=3).to_numpy() for h in range(1, 7)]
    d['rayos_despues'] = np.sum(siguientes, axis=0)
    d = d.dropna(subset=base + OTRAS + BAJAS + ['y_6h', 'rayos_despues']).sort_index(kind='stable')
    salida['Próximas 6 h'], parte['Próximas 6 h'] = evaluar(d, base, 'y_6h', 'lluvia_3h', True)
    print(f'Próximas 6 h: {time.time() - t0:.0f} s; ' + '; '.join(
        f'{v} {r["total"]["mejora"]:+.2f} %' for v, r in salida['Próximas 6 h'].items()), flush=True)
    escribir(salida, parte, elegidas)


def escribir(salida, parte, elegidas):
    o = ['# Dos modelos: con y sin tormenta eléctrica', '',
         'Lo escribe `analisis/dos_modelos.py`. Mejora: cuánto baja el Brier (positivo es mejor). «Un modelo con todo» y '
         '«Dos por regla, variables de la página» se comparan con la página; las demás, con el modelo con todo. Para '
         'adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y '
         'mejora en al menos 6 de 8 trimestres. Las columnas con y sin tormenta son la misma mejora en esas horas.', '',
         '| Pronóstico | Variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? | Sin tormenta (%) | Con tormenta (%) |',
         '|---|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, r in vs.items():
            t = r['total']
            o.append(f'| {n} | {v} | {num(t["mejora"])} | [{num(t["bajo"])}; {num(t["alto"])}] | {t["ganados"]}/{t["trimestres"]} | '
                     f'{"sí" if adoptar(t) else "no"} | {num(r["sin"]["mejora"])} | {num(r["con"]["mejora"])} |')
    o += ['', '## Horas con tormenta', '', '| Pronóstico | Predicciones con rayos a menos de 60 km en la hora anterior |', '|---|---|']
    o += [f'| {n} | {v:.0f} % |' for n, v in parte.items()]
    o += ['', '## En los inicios de lluvia sin rayos, frente a la página', '',
          'Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que '
          'sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o '
          'más llovió.', '',
          '| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |',
          '|---|---|---|---|---|---|---|']
    for n, vs in salida.items():
        for v, r in vs.items():
            s = r['inicios']
            o.append(f'| {n} | {v} | {s["lluvia"]:,} | {num(s["mejora"])} | {s["p_antes"]:.0f} % → {s["p_ahora"]:.0f} % | '
                     f'{s["det30_antes"]:.0f} % → {s["det30_ahora"]:.0f} % | {s["acierto30"]:.0f} % ({s["alertas30"]:,}) |')
    o += ['', '## Variables elegidas sin tormenta, hora en curso', '',
          'Con los datos de antes de 2025, de mayor a menor correlación con la lluvia. Solo las 15 primeras.', '',
          '| Variable | Correlación |', '|---|---|']
    o += [f'| `{c}` | {v:+.3f} |' for c, v in list(elegidas.items())[:15]]
    (AQUI / 'dos_modelos.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/dos_modelos.md')


if __name__ == '__main__':
    main()
