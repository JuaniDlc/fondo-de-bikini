"""Fase B: qué tan certeros son los pronósticos para Guayaquil, y un modelo corregido (MOS).

Compara, contra la lluvia que de verdad reportó el aeropuerto (SEGU):
- climatología (frecuencia de lluvia por mes y hora),
- la heurística actual de assets/modelo.js,
- los modelos crudos (fracción de GFS, ECMWF e ICON que pronostican lluvia),
- dos modelos corregidos entrenados con los datos de Guayaquil:
  regresión logística (exportable a JavaScript) y gradient boosting.

Entrena con 2023-2024 y evalúa con 2025-2026, que el modelo no vio; escribe analisis/resultados.md.
Después reentrena con todos los datos y escribe assets/mos-coeficientes.js (lo usan la página y
el workflow) y tests/fixtures/mos-casos.json (comprueba que JavaScript calcula igual que Python).
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).parent
DATOS = AQUI / 'datos'
CORTE = pd.Timestamp('2025-01-01')  # entrena antes de esta fecha, evalúa desde ella
UMBRAL_MM = 0.1
VENTANA = 6
MODELOS = {'gfs': 'gfs_seamless', 'ecmwf': 'ecmwf', 'icon': 'icon_seamless'}
UMBRALES_ALERTA = [0.5, 0.6, 0.7, 0.8, 0.9]

# ---------- verdad: lluvia reportada en el aeropuerto ----------

# Fenómenos con precipitación: RA (lluvia), DZ (llovizna), con o sin SH (chubasco), TS (tormenta),
# intensidad (+/-) o RE (reciente: llovió desde el reporte anterior). VC (en las cercanías) no cuenta.
TOKEN_LLUVIA = re.compile(r'^[+-]?(RE)?(TS|SH)?(RA|DZ)+$')


def hubo_lluvia(metar: str) -> bool:
    # El pronóstico de tendencia (TEMPO, BECMG) y los comentarios (RMK) no son observación.
    cuerpo = re.split(r'\s(?:NOSIG|TEMPO|BECMG|RMK)\b', str(metar))[0]
    return any(TOKEN_LLUVIA.match(t) for t in cuerpo.split())


def verdad() -> pd.Series:
    m = pd.read_csv(DATOS / 'metar_segu.csv')
    m['valid'] = pd.to_datetime(m['valid'])
    m['lluvia'] = m['metar'].map(hubo_lluvia)
    # Convención de Open-Meteo: la hora T acumula la lluvia de (T − 1 h, T].
    m['hora'] = m['valid'].dt.ceil('h')
    y = m.groupby('hora')['lluvia'].max().astype(float)
    return y.reindex(pd.date_range(y.index.min(), y.index.max(), freq='h'))  # horas sin reporte: NaN


# ---------- heurística actual (misma fórmula que assets/modelo.js) ----------

BASE_MES = np.array([0.45, 0.60, 0.60, 0.45, 0.15, 0.06, 0.04, 0.03, 0.04, 0.05, 0.06, 0.18])
logit = lambda p: np.log(p / (1 - p))  # noqa: E731


def heuristica(P, P3, T, HR, mes, hora):
    P, P3, T, HR, mes, hora = (np.asarray(x, dtype=float) for x in (P, P3, T, HR, mes, hora))
    base = BASE_MES[mes.astype(int) - 1]
    a, b = 17.62, 243.12
    g = np.log(HR / 100) + a * T / (b + T)
    sp = T - b * g / (a - g)
    marea = lambda h: 1.2 * np.cos(2 * np.pi * (h - 10) / 12)  # noqa: E731
    anomalia = (P - P3) - (marea(hora) - marea(hora - 3))
    conv = np.where((base >= 0.30) & (hora >= 13) & (hora <= 20), 0.6 + np.where(T >= 31, 0.4, 0), 0)
    z = (logit(base)
         + np.clip(-0.55 * (sp - 4), -2.2, 2.0)
         + np.clip(0.06 * (HR - 80), -1.8, 1.0)
         + np.where(np.isnan(P3), 0, np.clip(-0.9 * anomalia, -1.5, 2.0))
         + np.clip(-0.25 * (P - 1011), -0.8, 1.0)
         + np.clip(conv, 0, 1.0))
    return 1 / (1 + np.exp(-z))


# Mismos casos fijos que tests/modelo.test.mjs, para asegurar que la copia es fiel.
assert abs(heuristica(1009.5, 1011.0, 32, 85, 2, 15) - 0.930351) < 1e-6
assert abs(heuristica(1013.2, 1012.8, 26, 65, 8, 10) - 0.002715) < 1e-6
assert abs(heuristica(1011.0, np.nan, 24, 92, 12, 3) - 0.655597) < 1e-6

# ---------- variables de entrada ----------


def cargar() -> pd.DataFrame:
    p = pd.read_csv(DATOS / 'pronosticos.csv', parse_dates=['time']).set_index('time')
    p['precipitation_ecmwf'] = p['precipitation_ecmwf_ifs025'].fillna(p['precipitation_ecmwf_ifs04'])

    n = pd.read_csv(DATOS / 'nino.csv', parse_dates=['semana']).sort_values('semana')
    # El índice semanal se publica unos días después: se usa el de hace al menos 7 días.
    n['disponible'] = n['semana'] + pd.Timedelta(days=7)
    p = pd.merge_asof(p.sort_index().reset_index(), n[['disponible', 'nino12', 'nino34']],
                      left_on='time', right_on='disponible').set_index('time')

    df = pd.DataFrame(index=p.index)
    df['y_hora'] = verdad().reindex(p.index)
    # Llueve en algún momento de las próximas 6 horas (T+1 … T+6); NaN si falta algún reporte.
    df['y_6h'] = df['y_hora'].rolling(VENTANA, min_periods=VENTANA).max().shift(-VENTANA)
    df['lluvia_ahora'] = df['y_hora']
    df['lluvia_3h'] = df['y_hora'].rolling(3, min_periods=3).max()

    hora = p.index.hour
    dia = p.index.day_of_year
    df['mes'] = p.index.month
    df['hora'] = hora
    df['hora_sin'], df['hora_cos'] = np.sin(2 * np.pi * hora / 24), np.cos(2 * np.pi * hora / 24)
    df['dia_sin'], df['dia_cos'] = np.sin(2 * np.pi * dia / 365.25), np.cos(2 * np.pi * dia / 365.25)
    df['nino12'], df['nino34'] = p['nino12'], p['nino34']

    llueve = {}
    for corto, col in MODELOS.items():
        pr = p[f'precipitation_{col}']
        llueve[corto] = (pr >= UMBRAL_MM).where(pr.notna())
        df[f'{corto}_mm'] = np.log1p(pr)
        df[f'{corto}_mm_vecinas'] = np.log1p(pr.rolling(3, center=True).max())  # ±1 h por errores de hora
        df[f'{corto}_mm_6h'] = np.log1p(pr.rolling(VENTANA).sum().shift(-VENTANA))
        df[f'{corto}_max_6h'] = np.log1p(pr.rolling(VENTANA).max().shift(-VENTANA))
        df[f'{corto}_llueve_6h'] = llueve[corto].rolling(VENTANA).max().shift(-VENTANA)
    df['crudo_hora'] = sum(llueve.values()) / len(llueve)
    df['crudo_6h'] = sum(df[f'{c}_llueve_6h'] for c in MODELOS) / len(MODELOS)

    df['cape'] = np.log1p(p['cape_gfs_seamless'])
    df['cape_max_6h'] = np.log1p(p['cape_gfs_seamless'].rolling(VENTANA).max().shift(-VENTANA))
    df['humedad'] = p['relative_humidity_2m_gfs_seamless']
    df['nubes'] = p['cloud_cover_gfs_seamless']
    df['nubes_6h'] = p['cloud_cover_gfs_seamless'].rolling(VENTANA).mean().shift(-VENTANA)

    pres = p['pressure_msl_gfs_seamless']
    df['heuristica'] = heuristica(pres, pres.shift(3), p['temperature_2m_gfs_seamless'],
                                  p['relative_humidity_2m_gfs_seamless'], df['mes'], hora)
    return df, p


COMUNES = ['hora_sin', 'hora_cos', 'dia_sin', 'dia_cos', 'nino12', 'nino34']
VARIABLES = {
    'hora': COMUNES + [f'{c}_{s}' for c in MODELOS for s in ('mm', 'mm_vecinas')]
    + ['cape', 'humedad', 'nubes'],
    '6h': COMUNES + [f'{c}_{s}' for c in MODELOS for s in ('mm_6h', 'max_6h', 'llueve_6h')]
    + ['cape', 'cape_max_6h', 'humedad', 'nubes_6h'],
}

# ---------- evaluación ----------


def metricas(y, p, brier_clim):
    bs = brier_score_loss(y, p)
    return {'brier': bs, 'mejora': 1 - bs / brier_clim, 'auc': roc_auc_score(y, p)}


def tabla_calibracion(y, p):
    bins = np.linspace(0, 1, 11)
    idx = np.clip(np.digitize(p, bins) - 1, 0, 9)
    filas = []
    for i in range(10):
        sel = idx == i
        if sel.sum() == 0:
            continue
        filas.append({'rango': f'{int(bins[i] * 100)}–{int(bins[i + 1] * 100)} %', 'horas': int(sel.sum()),
                      'pronostico': float(p[sel].mean()), 'llovio': float(y[sel].mean())})
    return filas


def tabla_alertas(y, p, meses, horas):
    filas = []
    # Un episodio es una racha de horas seguidas en alerta: sería un solo aviso al celular.
    seguidas = np.r_[False, np.diff(horas.to_numpy()) == np.timedelta64(1, 'h')]
    for u in UMBRALES_ALERTA:
        a = p >= u
        episodios = int((a & ~(np.r_[False, a[:-1]] & seguidas)).sum())
        filas.append({'umbral': u, 'alertas': int(a.sum()), 'por_mes': episodios / meses,
                      'acierto': float(y[a].mean()) if a.any() else float('nan'),
                      'detecta': float(a[y == 1].mean())})
    return filas


PERSISTENCIA = ['lluvia_ahora', 'lluvia_3h']


def entrenar(objetivo, df, extra=()):
    cols = VARIABLES[objetivo] + list(extra)
    y = f'y_{objetivo}'
    # En 6 h todas las variantes usan las mismas horas: las que tienen reporte del aeropuerto ahora.
    requeridas = PERSISTENCIA if objetivo == '6h' else []
    datos = df.dropna(subset=cols + requeridas + [y, f'crudo_{objetivo}'])
    tr, te = datos[datos.index < CORTE], datos[datos.index >= CORTE]
    log = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)).fit(tr[cols], tr[y])
    gb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                        l2_regularization=1.0, random_state=0).fit(tr[cols], tr[y])
    return cols, tr, te, log, gb


def climatologia(tr, te, y):
    frec = tr.groupby(['mes', 'hora'])[y].mean()
    return te.join(frec.rename('clim'), on=['mes', 'hora'])['clim'].fillna(tr[y].mean()).to_numpy()


def pct(x):
    return f'{x * 100:.0f} %'


def main():
    df, pron = cargar()
    meses_prueba = (df.index[-1] - CORTE).days / 30.44
    informe = ['# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?', '',
               f'Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: '
               f'{df.index[0]:%Y-%m-%d} a {CORTE - pd.Timedelta(days=1):%Y-%m-%d}. Prueba (datos que el '
               f'modelo no vio): {CORTE:%Y-%m-%d} a {df.index[-1]:%Y-%m-%d}.', '']

    for objetivo, titulo in (('hora', '¿Llueve en esta hora?'), ('6h', '¿Llueve en las próximas 6 horas?')):
        y = f'y_{objetivo}'
        cols, tr, te, log, gb = entrenar(objetivo, df)
        yt = te[y].to_numpy()
        clim = climatologia(tr, te, y)
        brier_clim = brier_score_loss(yt, clim)
        candidatos = {
            'Climatología (mes y hora)': clim,
            'Modelos crudos (GFS, ECMWF, ICON)': te[f'crudo_{objetivo}'].to_numpy(),
            'MOS: regresión logística': log.predict_proba(te[cols])[:, 1],
            'MOS: gradient boosting': gb.predict_proba(te[cols])[:, 1],
        }
        if objetivo == 'hora':
            candidatos = {'Heurística actual': te['heuristica'].to_numpy(), **candidatos}
        else:
            # Variante que sabe si está lloviendo ahora en el aeropuerto (requiere el METAR en vivo).
            cols_p, _, te_p, log_p, _ = entrenar(objetivo, df, extra=PERSISTENCIA)
            assert te_p.index.equals(te.index)
            candidatos['MOS logística + lluvia actual (METAR)'] = log_p.predict_proba(te_p[cols_p])[:, 1]

        informe += [f'## {titulo}', '',
                    f'Horas de prueba: {len(te):,}. Llovió en el {pct(yt.mean())} de ellas '
                    f'(en entrenamiento: {pct(tr[y].mean())}).', '',
                    '| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |',
                    '|---|---|---|---|']
        for nombre, p in candidatos.items():
            m = metricas(yt, p, brier_clim)
            informe.append(f"| {nombre} | {m['brier']:.3f} | {m['mejora'] * 100:+.0f} % | {m['auc']:.2f} |")

        mejor = 'MOS: regresión logística'
        p = candidatos[mejor]
        informe += ['', f'**Calibración de «{mejor}»** (cuando dice X %, ¿cuánto llovió?):', '',
                    '| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |', '|---|---|---|---|']
        informe += [f"| {f['rango']} | {f['horas']:,} | {pct(f['pronostico'])} | {pct(f['llovio'])} |"
                    for f in tabla_calibracion(yt, p)]
        modelos_alerta = [mejor] + (['MOS logística + lluvia actual (METAR)'] if objetivo == '6h' else [])
        for nombre in modelos_alerta:
            informe += ['', f'**Si se usara como alerta** («{nombre}»):', '',
                        '| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |',
                        '|---|---|---|---|']
            informe += [f"| {pct(f['umbral'])} | {f['por_mes']:.0f} | {pct(f['acierto'])} | {pct(f['detecta'])} |"
                        for f in tabla_alertas(yt, candidatos[nombre], meses_prueba, te.index)]

        # Por temporada y en el mes actual
        informe += ['', '**Por periodo** (mejora sobre climatología; AUC):', '',
                    '| Periodo | Horas | Llovió | Modelos crudos | MOS logística |', '|---|---|---|---|---|']
        periodos = {
            'Temporada lluviosa (ene–abr)': te['mes'].between(1, 4).to_numpy(),
            'Temporada seca (may–dic)': ~te['mes'].between(1, 4).to_numpy(),
            f'Último mes ({te.index[-1]:%Y-%m})': (te.index >= te.index[-1].to_period('M').start_time),
        }
        for nombre, sel in periodos.items():
            if sel.sum() < 50 or yt[sel].min() == yt[sel].max():
                continue
            bc = brier_score_loss(yt[sel], clim[sel])
            c = metricas(yt[sel], candidatos['Modelos crudos (GFS, ECMWF, ICON)'][sel], bc)
            m = metricas(yt[sel], p[sel], bc)
            informe.append(f"| {nombre} | {sel.sum():,} | {pct(yt[sel].mean())} | "
                           f"{c['mejora'] * 100:+.0f} %; {c['auc']:.2f} | {m['mejora'] * 100:+.0f} %; {m['auc']:.2f} |")
        informe.append('')
    (AQUI / 'resultados.md').write_text('\n'.join(informe), encoding='utf-8')
    print('\n'.join(informe))
    exportar_produccion(df, pron)


# ---------- modelo para la página ----------

COLUMNAS_FIXTURE = {
    'precipitation_gfs_seamless': 'precipitation_gfs_seamless',
    'precipitation_ecmwf_ifs025': 'precipitation_ecmwf',  # en vivo solo existe ifs025
    'precipitation_icon_seamless': 'precipitation_icon_seamless',
    'cape_gfs_seamless': 'cape_gfs_seamless',
    'relative_humidity_2m_gfs_seamless': 'relative_humidity_2m_gfs_seamless',
    'cloud_cover_gfs_seamless': 'cloud_cover_gfs_seamless',
}


def exportar_produccion(df, p):
    """Reentrena con todos los datos (2023 a hoy) y escribe:
    - assets/mos-coeficientes.js, que usan la página y el workflow;
    - tests/fixtures/mos-casos.json, casos con datos crudos y el resultado de Python,
      para comprobar que JavaScript calcula exactamente lo mismo."""
    raiz = AQUI.parent
    modelos, filas = {}, {}
    for nombre, objetivo, extra in (('hora', 'hora', ()), ('6h', '6h', ()), ('6h_con_metar', '6h', PERSISTENCIA)):
        cols = VARIABLES[objetivo] + list(extra)
        y = f'y_{objetivo}'
        requeridas = PERSISTENCIA if objetivo == '6h' else []
        datos = df.dropna(subset=cols + requeridas + [y])
        pipe = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)).fit(datos[cols], datos[y])
        modelos[nombre] = exportar(pipe, cols)
        filas[nombre] = (datos, pipe, cols)

    meta = {'entrenado': pd.Timestamp.today().strftime('%Y-%m-%d'),
            'datos': f'{df.index[0]:%Y-%m-%d} a {df.index[-1]:%Y-%m-%d}',
            'umbral_mm': UMBRAL_MM, 'ventana_h': VENTANA}
    (raiz / 'assets' / 'mos-coeficientes.js').write_text(
        '// Generado por analisis/entrenar.py. No editar a mano: vuelve a correr el script.\n'
        f'export default {json.dumps({"meta": meta, **modelos}, indent=2, ensure_ascii=False)};\n',
        encoding='utf-8')

    # Casos de prueba: horas variadas donde los tres modelos se pueden calcular.
    datos6, _, _ = filas['6h_con_metar']
    comunes = datos6.index.intersection(filas['hora'][0].index)
    elegidas = list(pd.Series(comunes).sample(5, random_state=7))
    elegidas.append(datos6.loc[comunes, 'lluvia_ahora'].idxmax())  # una con lluvia en el aeropuerto
    casos = []
    for t in elegidas:
        ventana = p.loc[t - pd.Timedelta(hours=2): t + pd.Timedelta(hours=VENTANA + 1)]
        hourly = {'time': [x.strftime('%Y-%m-%dT%H:%M') for x in ventana.index]}
        for clave, col in COLUMNAS_FIXTURE.items():
            hourly[clave] = [None if pd.isna(v) else float(v) for v in ventana[col]]
        esperado = {}
        for nombre, (datos, pipe, cols) in filas.items():
            esperado[nombre] = float(pipe.predict_proba(datos.loc[[t], cols])[:, 1][0])
        casos.append({
            'hora': t.strftime('%Y-%m-%dT%H:%M'),
            'hourly': hourly,
            'nino': [{'semana': (p.loc[t, 'disponible'] - pd.Timedelta(days=7)).strftime('%Y-%m-%d'),
                      'nino12': float(p.loc[t, 'nino12']), 'nino34': float(p.loc[t, 'nino34'])}],
            'aeropuerto': {'lluvia_ahora': float(df.loc[t, 'lluvia_ahora']),
                           'lluvia_3h': float(df.loc[t, 'lluvia_3h'])},
            'esperado': esperado,
        })
    destino = raiz / 'tests' / 'fixtures'
    destino.mkdir(exist_ok=True)
    (destino / 'mos-casos.json').write_text(json.dumps(casos, indent=1), encoding='utf-8')
    print(f'\nModelo para la página: assets/mos-coeficientes.js ({meta["datos"]}); '
          f'{len(casos)} casos de prueba en tests/fixtures/mos-casos.json')


def exportar(pipe, cols):
    esc, lr = pipe.named_steps['standardscaler'], pipe.named_steps['logisticregression']
    return {
        'variables': cols,
        'media': [round(float(x), 6) for x in esc.mean_],
        'escala': [round(float(x), 6) for x in esc.scale_],
        'coeficientes': [round(float(x), 6) for x in lr.coef_[0]],
        'intercepto': round(float(lr.intercept_[0]), 6),
    }


if __name__ == '__main__':
    main()
