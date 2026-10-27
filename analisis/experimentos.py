"""Prueba mejoras del modelo corregido con los mismos datos de prueba (2025 en adelante).

Cada variante se entrena con 2023-2024 y se evalúa sobre las mismas horas de prueba,
así las diferencias se deben a las variables y no a horas distintas.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from entrenar import CORTE, PERSISTENCIA, VARIABLES, cargar, climatologia

EXTRA_HORA = ['spread', 'nubes_bajas', 'li', 'cin', 'viento_u', 'viento_v', 'chubascos', 'cape_icon']
EXTRA_6H = ['spread', 'nubes_bajas_6h', 'li_min_6h', 'cin', 'viento_u', 'viento_v', 'chubascos_6h', 'cape_icon_max_6h']
PREVIA = ['lluvia_previa', 'lluvia_previa_3h']

VARIANTES = {
    'hora': {
        'Actual': VARIABLES['hora'],
        '+ variables nuevas': VARIABLES['hora'] + EXTRA_HORA,
        '+ lluvia de la hora anterior': VARIABLES['hora'] + PREVIA,
        '+ ambas': VARIABLES['hora'] + EXTRA_HORA + PREVIA,
    },
    '6h': {
        'Actual (sin aeropuerto)': VARIABLES['6h'],
        'Actual (con aeropuerto)': VARIABLES['6h'] + PERSISTENCIA,
        '+ variables nuevas (con aeropuerto)': VARIABLES['6h'] + PERSISTENCIA + EXTRA_6H,
    },
}


def tabla_calibracion(y, p):
    out = []
    for lo in (0.5, 0.6, 0.7, 0.8, 0.9):
        sel = (p >= lo) & (p < lo + 0.1)
        if sel.sum() >= 20:
            out.append(f'{int(lo * 100)}–{int(lo * 100) + 10} %: llovió {y[sel].mean() * 100:.0f} % ({sel.sum()})')
    return '; '.join(out)


def main():
    df, _ = cargar()
    for objetivo, variantes in VARIANTES.items():
        y = f'y_{objetivo}'
        todas = sorted({c for cols in variantes.values() for c in cols})
        datos = df.dropna(subset=todas + [y])
        tr, te = datos[datos.index < CORTE], datos[datos.index >= CORTE]
        yt = te[y].to_numpy()
        bc = brier_score_loss(yt, climatologia(tr, te, y))
        oct26 = np.asarray(te.index >= '2026-10-01')
        print(f'\n=== {objetivo}: {len(tr):,} horas de entrenamiento, {len(te):,} de prueba; '
              f'llovió {yt.mean() * 100:.0f} % (octubre 2026: {yt[oct26].mean() * 100:.0f} %)')
        print(f'{"Variante":42s} {"Brier":>6} {"Mejora":>7} {"AUC":>5}   {"Oct-26 Brier":>12}')
        for nombre, cols in variantes.items():
            m = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)).fit(tr[cols], tr[y])
            p = m.predict_proba(te[cols])[:, 1]
            bs = brier_score_loss(yt, p)
            print(f'{nombre:42s} {bs:6.3f} {(1 - bs / bc) * 100:+6.0f}% {roc_auc_score(yt, p):5.2f}   '
                  f'{brier_score_loss(yt[oct26], p[oct26]):12.3f}')
            print(f'    calibración: {tabla_calibracion(yt, p)}')


if __name__ == '__main__':
    main()
