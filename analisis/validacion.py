"""Validación mes a mes de cómo se entrena el modelo de la página; escribe analisis/validacion.md.

Cada mes desde 2025 se predice con un modelo entrenado solo con lo anterior a ese mes, como pasaría
en la página si se reentrenara cada mes. Compara:
- entrenar una sola vez con 2023-2024 contra reentrenar cada mes con todo lo anterior,
- dar más peso a lo reciente (media vida de 1 o 2 años), interacciones con la época del año,
- gradient boosting con restricciones monótonas (más lluvia pronosticada o más rayos nunca baja
  la probabilidad) contra la regresión logística,
- la recalibración (Platt e isotónica), ajustada con las predicciones de los meses anteriores,
- según el minuto de la hora: el modelo de los rayos de T − 1 con datos más nuevos contra el
  entrenado con los datos de cada minuto (apilar en entrenar.py).

Uso: python analisis/validacion.py  (unos 20 minutos)
"""

import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

import entrenar as E

warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)
DESDE = pd.Timestamp('2025-01-01')
HORA = E.VARIABLES['hora'] + E.PREVIA + E.RAYOS + E.IR + E.FRACCION_IR
SEIS = E.VARIABLES['6h'] + E.PERSISTENCIA + E.RAYOS


def estacion(d, cols):
    """Interacciones con la época del año (seno y coseno del día)."""
    for c in cols:
        d[f'{c}_xs'], d[f'{c}_xc'] = d[c] * d['dia_sin'], d[c] * d['dia_cos']
    return [f'{c}_x{s}' for c in cols for s in 'sc']


def monotono(c):
    """+1 si más de esto nunca debería bajar la probabilidad de lluvia."""
    claves = ('_mm', '_suma', 'llueve', 'rayos_', 'cercania', 'ir_frio', 'ir_muy', 'ir_centro', 'lluvia_')
    return int(any(s in c for s in claves) and not c.endswith('_x_fr'))


def boosting(tr, cols, y):
    return HistGradientBoostingClassifier(
        max_iter=500, learning_rate=0.03, max_leaf_nodes=15, min_samples_leaf=50, l2_regularization=1.0,
        monotonic_cst=[monotono(c) for c in cols], early_stopping=False, random_state=0).fit(tr[cols], tr[y])


def mes_a_mes(d, cols, est, y):
    """Predicción de cada mes desde DESDE con cada variante, entrenada con lo anterior."""
    sin_peso = lambda tr, inicio: E.logistica(tr, cols, y, inicio)  # noqa: E731
    variantes = {
        'Una vez, con 2023-2024 (antes)': lambda tr, inicio: (E.make_pipeline(
            E.StandardScaler(), E.LogisticRegression(C=0.5, max_iter=2000)).fit(tr.loc[tr.index < DESDE, cols],
                                                                              tr.loc[tr.index < DESDE, y]), cols),
        'Cada mes, con todo lo anterior': lambda tr, inicio: (E.make_pipeline(
            E.StandardScaler(), E.LogisticRegression(C=0.5, max_iter=2000)).fit(tr[cols], tr[y]), cols),
        'Cada mes, más peso a lo reciente (media vida 1 año)': lambda tr, inicio: (_media_vida(365, tr, cols, y, inicio), cols),
        'Ídem, media vida 2 años (la página)': lambda tr, inicio: (sin_peso(tr, inicio), cols),
        'Ídem 2 años + interacciones con la época': lambda tr, inicio: (E.logistica(tr, cols + est, y, inicio), cols + est),
        'Gradient boosting monótono': lambda tr, inicio: (boosting(tr, cols, y), cols),
    }
    pred = {n: [] for n in variantes}
    ys, indice = [], []
    for inicio in pd.date_range(DESDE, d.index.max(), freq='MS'):
        tr = d[d.index < inicio]
        te = d[(d.index >= inicio) & (d.index < inicio + pd.offsets.MonthBegin())]
        if not len(te):
            continue
        ys.append(te[y].to_numpy())
        indice.append(te.index)
        for n, f in variantes.items():
            modelo, c = f(tr, inicio)
            pred[n].append(modelo.predict_proba(te[c])[:, 1])
        print(f'  {inicio:%Y-%m}', flush=True)
    return np.concatenate(ys), pd.DatetimeIndex(np.concatenate(indice)), {n: np.concatenate(p) for n, p in pred.items()}


def _media_vida(dias, tr, cols, y, inicio):
    anterior, E.MEDIA_VIDA_DIAS = E.MEDIA_VIDA_DIAS, dias
    try:
        return E.logistica(tr, cols, y, inicio)
    finally:
        E.MEDIA_VIDA_DIAS = anterior


def recalibrar(y, p, indice, meses_minimos=6):
    """Cada mes, la recalibración ajustada con las predicciones de los meses anteriores."""
    z = np.log(np.clip(p, 1e-5, 1 - 1e-5) / (1 - np.clip(p, 1e-5, 1 - 1e-5)))
    mes = indice.to_period('M')
    meses = mes.unique()
    salida = {'Sin recalibrar': p.copy(), 'Platt': p.copy(), 'Isotónica': p.copy()}
    for m in meses[meses_minimos:]:
        antes, ahora = mes < m, mes == m
        a, b = E.platt(z[antes], y[antes])
        salida['Platt'][ahora] = 1 / (1 + np.exp(-(a * z[ahora] + b)))
        salida['Isotónica'][ahora] = IsotonicRegression(out_of_bounds='clip').fit(p[antes], y[antes]).predict(p[ahora])
    sel = mes >= meses[meses_minimos]
    return {n: v[sel] for n, v in salida.items()}, y[sel], meses[meses_minimos]


def tabla(y, preds):
    filas = ['| Variante | Brier (menor es mejor) | AUC |', '|---|---|---|']
    filas += [f'| {n} | {brier_score_loss(y, p):.4f} | {roc_auc_score(y, p):.3f} |' for n, p in preds.items()]
    return filas


def calibracion(y, preds):
    filas = ['| Pronóstico | ' + ' | '.join(preds) + ' |', '|---' * (len(preds) + 1) + '|']
    cortes = np.linspace(0, 1, 11)
    for i in range(10):
        celdas = []
        for p in preds.values():
            sel = (p >= cortes[i]) & (p < cortes[i + 1] if i < 9 else p <= 1)
            celdas.append(f'dice {p[sel].mean() * 100:.0f} %, llovió {y[sel].mean() * 100:.0f} %' if sel.sum() >= 20 else '—')
        filas.append(f'| {int(cortes[i] * 100)}–{int(cortes[i + 1] * 100)} % | ' + ' | '.join(celdas) + ' |')
    return filas


def por_minuto(df):
    """La hora en curso (k = 1) según el minuto en que se miden los rayos y el infrarrojo."""
    filas = ['| Minuto | Horas de tormenta | Antes: modelo de T − 1 con datos nuevos | Modelo por minuto |',
             '|---|---|---|---|']
    pila = E.apilar(df, 1).dropna(subset=HORA + ['y_hora'])
    tr = pila[pila.index < DESDE]
    sin = E.VARIABLES['hora'] + E.PREVIA + E.RAYOS + E.IR
    antes = E.logistica(tr[tr['fraccion'] == 0], sin, 'y_hora', DESDE)
    ahora = E.logistica(tr, HORA, 'y_hora', DESDE)
    for m in E.MINUTOS:
        te = pila[(pila.index >= DESDE) & (pila['fraccion'] == m / 60)]
        tormenta = (te['cercania_1h'] > np.exp(-2)).to_numpy()  # rayos a menos de 60 km
        b = [brier_score_loss(te['y_hora'], x.predict_proba(te[c])[:, 1]) for x, c in ((antes, sin), (ahora, HORA))]
        bt = [brier_score_loss(te['y_hora'][tormenta], x.predict_proba(te[c])[:, 1][tormenta])
              for x, c in ((antes, sin), (ahora, HORA))]
        filas.append(f'| {m} | {tormenta.sum():,} | {b[0]:.4f} (tormenta {bt[0]:.4f}) | {b[1]:.4f} (tormenta {bt[1]:.4f}) |')
    return filas


def main():
    df, _ = E.cargar()
    informe = ['# Validación mes a mes', '',
               f'Cada mes desde {DESDE:%Y-%m} se predice con un modelo entrenado solo con los datos anteriores a ese '
               'mes. Verdad: lluvia reportada en el aeropuerto. Brier: error cuadrático de la probabilidad (menor es '
               'mejor). Lo escribe `analisis/validacion.py`.', '']
    for titulo, d, cols, est, y in (
        ('¿Llueve en las próximas 6 horas? (avisos)', df.copy(), SEIS,
         ['cape_max_6h', 'humedad', 'nubes_6h', 'rayos_30_1h', 'lluvia_ahora'], 'y_6h'),
        ('¿Llueve en la hora en curso? (con rayos e infrarrojo, todos los minutos)', E.apilar(df, 1), HORA,
         ['cape_2h', 'humedad', 'nubes', 'modelos_llueve_2h', 'rayos_30_1h', 'ir_frio_30', 'lluvia_previa'], 'y_hora'),
    ):
        print(titulo, flush=True)
        est = estacion(d, est)
        d = d.dropna(subset=cols + est + [y])
        yy, indice, preds = mes_a_mes(d, cols, est, y)
        cal, ycal, desde = recalibrar(yy, preds['Ídem, media vida 2 años (la página)'], indice)
        informe += [f'## {titulo}', '', f'{len(yy):,} predicciones.', ''] + tabla(yy, preds) + [
            '', f'**Recalibración** del modelo con más peso a lo reciente, ajustada cada mes con las predicciones de '
            f'los meses anteriores (evaluada desde {desde}):', ''] + tabla(ycal, cal) + [''] + calibracion(ycal, cal) + ['']
    informe += ['## Según el minuto de la hora', '',
                'La hora en curso con los rayos y el infrarrojo medidos m minutos después del último reporte horario del '
                'aeropuerto (el workflow los mide cada 10 minutos). Entrenado con 2023-2024, evaluado desde 2025. '
                '«Tormenta»: con rayos a menos de 60 km en la última hora.', ''] + por_minuto(df) + ['']
    (E.AQUI / 'validacion.md').write_text('\n'.join(informe), encoding='utf-8')
    print('\n'.join(informe))


if __name__ == '__main__':
    main()
