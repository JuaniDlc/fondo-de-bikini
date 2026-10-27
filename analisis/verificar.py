"""Compara lo que dijo la página (data/historial.json) con la lluvia que reportó el aeropuerto.

Uso: python analisis/verificar.py
"""

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from entrenar import hubo_lluvia

RAIZ = Path(__file__).resolve().parent.parent
VENTANA = 6


def metar(desde: pd.Timestamp, hasta: pd.Timestamp) -> pd.Series:
    params = {
        'station': 'SEGU', 'data': 'metar', 'tz': 'America/Guayaquil', 'format': 'onlycomma',
        'report_type': ['3', '4'],
        'year1': desde.year, 'month1': desde.month, 'day1': desde.day,
        'year2': hasta.year, 'month2': hasta.month, 'day2': hasta.day,
    }
    r = requests.get('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py', params=params, timeout=120)
    r.raise_for_status()
    m = pd.read_csv(io.StringIO(r.text))
    m['valid'] = pd.to_datetime(m['valid'])
    m['lluvia'] = m['metar'].map(hubo_lluvia)
    m['hora'] = m['valid'].dt.ceil('h')
    y = m.groupby('hora')['lluvia'].max().astype(float)
    return y.reindex(pd.date_range(y.index.min(), y.index.max(), freq='h'))


def main():
    h = pd.DataFrame(json.loads((RAIZ / 'data' / 'historial.json').read_text(encoding='utf-8')))
    h['hora'] = pd.to_datetime(h['hora'])
    h = h.set_index('hora').sort_index()
    y = metar(h.index.min() - pd.Timedelta(days=1), h.index.max() + pd.Timedelta(days=2))
    h['llovio'] = y.reindex(h.index)
    h['llovio_6h'] = y.rolling(VENTANA, min_periods=VENTANA).max().shift(-VENTANA).reindex(h.index)

    print(f'Horas con predicción: {len(h)} ({h.index.min():%d %b %H:%M} a {h.index.max():%d %b %H:%M})')
    print(f'Horas con lluvia en el aeropuerto: {int(h["llovio"].sum())} de {int(h["llovio"].notna().sum())}\n')

    print('Hora               Esta hora  Llovió   Próx. 6 h  Llovió en 6 h')
    for t, f in h.iterrows():
        p6 = f.get('proximas6h')
        print(f'{t:%d %b %H:%M}       {f["probabilidad"]:5.0f} %   {"sí" if f["llovio"] == 1 else "no" if f["llovio"] == 0 else "?":>4}'
              f'   {"" if pd.isna(p6) else f"{p6:5.0f} %":>9}  {"" if pd.isna(p6) else ("sí" if f["llovio_6h"] == 1 else "no" if f["llovio_6h"] == 0 else "?"):>6}')

    v = h.dropna(subset=['llovio'])
    print('\nBrier por hora (menor es mejor):')
    for col, nombre in (('corregido', 'Modelo corregido'), ('ensamble', 'Ensambles sin corregir'),
                        ('heuristica', 'Heurística')):
        d = v.dropna(subset=[col])
        print(f'  {nombre:24s} {np.mean((d[col] / 100 - d["llovio"]) ** 2):.3f}  ({len(d)} horas)')
    clim = v['llovio'].mean()
    print(f'  {"Siempre " + f"{clim * 100:.0f} %":24s} {np.mean((clim - v["llovio"]) ** 2):.3f}')


if __name__ == '__main__':
    main()
