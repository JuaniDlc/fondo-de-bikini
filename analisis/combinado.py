"""Prueba el modelo combinado: presión de vapor, viento (10 m y altura) y temperatura del mar, todos juntos.

Compara con el modelo de la página (rayos, infrarrojo, vapor de GOES y aeropuerto) reentrenando cada
trimestre desde 2025 solo con lo anterior, sobre las mismas horas. También se prueba cada grupo solo,
para saber de dónde viene una mejora, y el combinado con interacciones y con gradient boosting, por
si las variables solo ayudan actuando juntas.

Regla fijada antes de ver los resultados, para adoptarlo: mejora el Brier en al menos 0,5 %, el
intervalo de 95 % (remuestreando días) no incluye el cero y mejora en al menos 6 de los 8 trimestres.

Necesita analisis/combinado_descargar.py. Escribe analisis/combinado.md.
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from entrenar import (ADELANTOS_IR, FRACCION_IR, IR, PERSISTENCIA, PREVIA, RAYOS, VAPOR, VARIABLES, VENTANA,
                      cargar, logistica, previas)

AQUI = Path(__file__).parent
DESDE = pd.Timestamp('2025-01-01')
# La página apila los 6 minutos de la hora; con 0 y 30 alcanza para comparar y es 3 veces más rápido.
MINUTOS = (0, 30)
REMUESTREOS = 2000

PRESION_VAPOR = ['e_2m', 'e_850']
VIENTO = ['u_10', 'v_10', 'vel_10', 'u_850', 'v_850', 'vel_850', 'u_500', 'v_500', 'u_200', 'v_200', 'cizalla']
MAR = ['sst_costa', 'sst_gradiente', 'sst_cambio_7d', 'sst_menos_850']
INTERACCIONES = ['flujo_u_850', 'flujo_v_850', 'flujo_u_10', 'flujo_v_10', 'sst_x_e', 'sst_x_cape']
COMBINADO = PRESION_VAPOR + VIENTO + MAR
VARIANTES = {
    'Solo presión de vapor': PRESION_VAPOR,
    'Solo viento': VIENTO,
    'Solo temperatura del mar': MAR,
    'Combinado': COMBINADO,
    'Combinado con interacciones': COMBINADO + INTERACCIONES,
}


def presion_vapor(td):
    """Presión de vapor (hPa) a partir del punto de rocío (Bolton, 1980)."""
    return 6.112 * np.exp(17.67 * td / (td + 243.5))


def componentes(velocidad, direccion):
    rad = np.radians(direccion)
    return -velocidad * np.sin(rad), -velocidad * np.cos(rad)


def agregar_variables(df, p):
    """En cada hora T, el pronóstico para T; la temperatura del mar es de 24 a 48 horas antes de T, así
    que ya se conoce a cualquier anticipación y no adelanta información."""
    a = pd.read_csv(AQUI / 'datos' / 'combinado' / 'altura.csv', parse_dates=['time']).set_index('time').reindex(df.index)
    m = pd.read_csv(AQUI / 'datos' / 'combinado' / 'mar.csv', parse_dates=['time']).set_index('time').reindex(df.index)
    e_850 = a['relative_humidity_850hPa'] / 100 * presion_vapor(a['temperature_850hPa'])
    u_10, v_10 = componentes(p['wind_speed_10m_gfs_seamless'], p['wind_direction_10m_gfs_seamless'])
    n = {'e_2m': presion_vapor(p['dew_point_2m_gfs_seamless']), 'e_850': e_850,
         'u_10': u_10, 'v_10': v_10, 'vel_10': p['wind_speed_10m_gfs_seamless'], 'vel_850': a['wind_speed_850hPa']}
    for nivel in (850, 500, 200):
        n[f'u_{nivel}'], n[f'v_{nivel}'] = componentes(a[f'wind_speed_{nivel}hPa'], a[f'wind_direction_{nivel}hPa'])
    n['cizalla'] = np.hypot(n['u_850'] - n['u_200'], n['v_850'] - n['v_200'])
    pasado = lambda s: s.shift(24).rolling(24, min_periods=18).mean()  # noqa: E731
    costa, afuera = pasado(m['sst_costa']), pasado(m['sst_afuera'])
    n['sst_costa'] = costa
    n['sst_gradiente'] = costa - afuera
    n['sst_cambio_7d'] = costa - costa.shift(24 * 7)
    n['sst_menos_850'] = costa - a['temperature_850hPa']
    n['flujo_u_850'], n['flujo_v_850'] = e_850 * n['u_850'], e_850 * n['v_850']
    n['flujo_u_10'], n['flujo_v_10'] = n['e_2m'] * u_10, n['e_2m'] * v_10
    n['sst_x_e'], n['sst_x_cape'] = costa * n['e_2m'], costa * df['cape']
    n = pd.DataFrame(n, index=df.index)
    # Para «próximas 6 h», el promedio de T + 1 … T + 6; el mar sigue siendo el conocido en T.
    futuro = n.drop(columns=['sst_costa', 'sst_gradiente', 'sst_cambio_7d']).rolling(VENTANA).mean().shift(-VENTANA)
    futuro = futuro.join(n[['sst_costa', 'sst_gradiente', 'sst_cambio_7d']])[n.columns]
    return df.join(n), futuro


def tareas():
    """Cada pronóstico como lo calcula la página: sus datos, variables y objetivo."""
    df, p = cargar()
    df, futuro = agregar_variables(df, p)
    nuevas = list(futuro.columns)
    salida = {}
    for k in ADELANTOS_IR:
        pila = pd.concat([previas(df, k, m) for m in MINUTOS])
        salida[f'Hora con {k} h' if k > 1 else 'Hora en curso'] = (
            pila, VARIABLES['hora'] + PREVIA + RAYOS + IR + VAPOR + FRACCION_IR, 'y_hora')
    seis = df.drop(columns=nuevas).join(futuro)
    salida['Próximas 6 h'] = (seis, VARIABLES['6h'] + PERSISTENCIA + RAYOS + VAPOR, 'y_6h')
    # Ordenado por hora: las predicciones se arman por trimestre y tienen que coincidir fila por fila
    # con las observaciones (al apilar minutos, cada hora aparece varias veces).
    return {n: (d.dropna(subset=b + nuevas + [y]).sort_index(kind='stable'), b, y) for n, (d, b, y) in salida.items()}


def predecir(datos, cols, y, inicio, fin, gb=False):
    tr, te = datos[datos.index < inicio], datos[(datos.index >= inicio) & (datos.index < fin)]
    if gb:
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                           l2_regularization=1.0, random_state=0).fit(tr[cols], tr[y])
        return m.predict_proba(te[cols])[:, 1]
    return logistica(tr, cols, y, inicio).predict_proba(te[cols])[:, 1]


def comparar(te, base, variante):
    """Mejora del Brier (%) con su intervalo, remuestreando días, y trimestres en que mejora."""
    y = te['y'].to_numpy()
    eb, ev = (base - y) ** 2, (variante - y) ** 2
    dias = pd.factorize(te.index.floor('D'))[0]
    nb, nv = np.bincount(dias, eb), np.bincount(dias, ev)
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(nb), (REMUESTREOS, len(nb)))
    mejoras = (1 - nv[idx].sum(axis=1) / nb[idx].sum(axis=1)) * 100
    trimestres = te.index.to_period('Q')
    ganados = [(ev[trimestres == q].sum() < eb[trimestres == q].sum()) for q in trimestres.unique()]
    return {'mejora': (1 - ev.sum() / eb.sum()) * 100, 'bajo': float(np.percentile(mejoras, 2.5)),
            'alto': float(np.percentile(mejoras, 97.5)), 'ganados': int(sum(ganados)), 'trimestres': len(ganados),
            'brier': float(ev.mean()), 'auc': float(roc_auc_score(y, variante))}


def adoptar(r):
    return r['mejora'] >= 0.5 and r['bajo'] > 0 and r['ganados'] >= 6


def main():
    t0 = time.time()
    datos = tareas()
    print(f'Datos listos en {time.time() - t0:.0f} s', {n: len(d) for n, (d, _, _) in datos.items()}, flush=True)
    resultados, detalle = {}, []
    for objetivo, (d, base, y) in datos.items():
        inicios = pd.date_range(DESDE, d.index.max(), freq='QS')
        fines = [*inicios[1:], d.index.max() + pd.Timedelta(hours=1)]
        grupos = {'Modelo de la página': (base, False), **{n: (base + v, False) for n, v in VARIANTES.items()},
                  'GB de la página': (base, True), 'GB combinado': (base + COMBINADO, True)}
        trabajos = [(n, i) for n in grupos for i in range(len(inicios))]
        partes = Parallel(n_jobs=os.cpu_count(), backend='threading')(
            delayed(predecir)(d, grupos[n][0], y, inicios[i], fines[i], grupos[n][1]) for n, i in trabajos)
        pred = {n: np.concatenate([p for (m, _), p in zip(trabajos, partes) if m == n]) for n in grupos}
        te = pd.DataFrame({'y': d.loc[d.index >= DESDE, y]})
        resultados[objetivo] = {'filas': len(te), 'llovio': float(te['y'].mean()), 'variantes': {}}
        for n in VARIANTES:
            resultados[objetivo]['variantes'][n] = comparar(te, pred['Modelo de la página'], pred[n])
        resultados[objetivo]['variantes']['GB combinado'] = comparar(te, pred['GB de la página'], pred['GB combinado'])
        resultados[objetivo]['variantes']['GB combinado frente a la página'] = comparar(
            te, pred['Modelo de la página'], pred['GB combinado'])
        resultados[objetivo]['base'] = {'brier': float(((pred['Modelo de la página'] - te['y'].to_numpy()) ** 2).mean()),
                                        'auc': float(roc_auc_score(te['y'], pred['Modelo de la página']))}
        # El modelo de la página ya se validó (analisis/validacion.md): si aquí sale mucho peor, la prueba está mal.
        assert resultados[objetivo]['base']['auc'] > 0.85, (objetivo, resultados[objetivo]['base'])
        # Dónde cambia: temporada lluviosa y seca, y horas con rayos cerca
        lluviosa = np.isin(te.index.month, [1, 2, 3, 4])
        rayos = d.loc[d.index >= DESDE, 'rayos_60_1h'].to_numpy() > 0
        for nombre, sel in (('Temporada lluviosa', lluviosa), ('Temporada seca', ~lluviosa), ('Con rayos a menos de 60 km', rayos)):
            detalle.append({'objetivo': objetivo, 'subgrupo': nombre, 'filas': int(sel.sum()),
                            **comparar(te[sel], pred['Modelo de la página'][sel], pred['Combinado'][sel])})
        print(f'{objetivo}: {time.time() - t0:.0f} s; ' + json.dumps(
            {n: round(r['mejora'], 2) for n, r in resultados[objetivo]['variantes'].items()}, ensure_ascii=False), flush=True)
    (AQUI / 'datos' / 'combinado' / 'resultados.json').write_text(
        json.dumps({'resultados': resultados, 'detalle': detalle}, ensure_ascii=False, indent=1), encoding='utf-8')
    escribir(resultados, detalle)


def num(x, dec=2):
    return f'{x:+.{dec}f}'.replace('.', ',')


def escribir(resultados, detalle):
    o = ['# Modelo combinado: presión de vapor, viento y temperatura del mar', '',
         'Lo escribe `analisis/combinado.py`. Reentrenado cada trimestre desde 2025 solo con lo anterior, sobre las '
         'mismas horas. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor); entre '
         'corchetes, el intervalo de 95 % remuestreando días; después, trimestres en que mejora.', '',
         'Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo no incluye el cero y '
         'mejora en al menos 6 de 8 trimestres.', '']
    nombres = [*VARIANTES, 'GB combinado', 'GB combinado frente a la página']
    for objetivo, r in resultados.items():
        o += [f'## {objetivo}', '', f'{r["filas"]:,} predicciones; llovió en el {r["llovio"] * 100:.0f} %. '
              f'Modelo de la página: Brier {r["base"]["brier"]:.4f}, AUC {r["base"]["auc"]:.3f}.', '',
              '| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |', '|---|---|---|---|---|---|']
        for n in nombres:
            v = r['variantes'][n]
            o.append(f'| {n} | {num(v["mejora"])} | [{num(v["bajo"])}; {num(v["alto"])}] | '
                     f'{v["ganados"]}/{v["trimestres"]} | {v["auc"]:.3f} | {"sí" if adoptar(v) else "no"} |')
        o.append('')
    o += ['«GB combinado» se compara con gradient boosting de las variables de la página, para ver si esas variables '
          'ayudan de forma no lineal; «frente a la página» lo compara con el modelo que de verdad se usa.', '',
          '## Dónde cambia el combinado', '', '| Pronóstico | Subgrupo | Predicciones | Mejora (%) | Intervalo |',
          '|---|---|---|---|---|']
    for d in detalle:
        o.append(f'| {d["objetivo"]} | {d["subgrupo"]} | {d["filas"]:,} | {num(d["mejora"])} | '
                 f'[{num(d["bajo"])}; {num(d["alto"])}] |')
    (AQUI / 'combinado.md').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito analisis/combinado.md')


if __name__ == '__main__':
    main()
