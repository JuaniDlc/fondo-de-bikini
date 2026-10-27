"""Descarga los datos de la fase B (modelo corregido con datos locales).

- Lluvia reportada en el aeropuerto de Guayaquil (METAR de SEGU), de Iowa Environmental Mesonet.
- Pronósticos históricos de Open-Meteo para GFS, ECMWF e ICON, tal como se emitieron.
- Índices semanales de El Niño de NOAA CPC (Niño 1+2, 3, 3.4 y 4).

Guarda CSV en analisis/datos/. Si un archivo ya existe no lo vuelve a bajar; usa --forzar.
"""

import argparse
import datetime as dt
import io
import re
from pathlib import Path

import pandas as pd
import requests

DATOS = Path(__file__).parent / 'datos'
INICIO = dt.date(2023, 1, 1)
LAT, LON = -2.19, -79.89
ZONA = 'America/Guayaquil'
VARIABLES = ['precipitation', 'cape', 'relative_humidity_2m', 'temperature_2m', 'pressure_msl', 'cloud_cover',
             'dew_point_2m', 'cloud_cover_low', 'lifted_index', 'convective_inhibition',
             'wind_speed_10m', 'wind_direction_10m', 'showers']
# ecmwf_ifs04 cubre 2023 y se une con ecmwf_ifs025, que empieza en 2024.
MODELOS = ['gfs_seamless', 'ecmwf_ifs025', 'ecmwf_ifs04', 'icon_seamless']


def metar(fin: dt.date) -> pd.DataFrame:
    params = {
        'station': 'SEGU', 'data': 'metar', 'tz': ZONA, 'format': 'onlycomma',
        'latlon': 'no', 'missing': 'M', 'report_type': ['3', '4'],  # rutinarios y especiales
        'year1': INICIO.year, 'month1': INICIO.month, 'day1': INICIO.day,
        'year2': fin.year, 'month2': fin.month, 'day2': fin.day,
    }
    r = requests.get('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py', params=params, timeout=600)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def pronosticos(fin: dt.date) -> pd.DataFrame:
    partes = []
    desde = INICIO
    while desde <= fin:
        hasta = min(dt.date(desde.year, 12, 31), fin)
        r = requests.get(
            'https://historical-forecast-api.open-meteo.com/v1/forecast',
            params={
                'latitude': LAT, 'longitude': LON, 'timezone': ZONA,
                'start_date': desde.isoformat(), 'end_date': hasta.isoformat(),
                'hourly': ','.join(VARIABLES), 'models': ','.join(MODELOS),
            },
            timeout=600,
        )
        r.raise_for_status()
        partes.append(pd.DataFrame(r.json()['hourly']))
        print(f'  pronósticos {desde} → {hasta}')
        desde = hasta + dt.timedelta(days=1)
    return pd.concat(partes, ignore_index=True)


def nino() -> pd.DataFrame:
    texto = requests.get('https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for', timeout=120).text
    filas = []
    for linea in texto.splitlines():
        m = re.match(r'\s*(\d{2}[A-Z]{3}\d{4})\s+(.*)', linea)
        if not m:
            continue
        # Cada región trae temperatura y anomalía, a veces pegadas: "23.4-0.4"
        n = [float(x) for x in re.findall(r'-?\d+\.\d', m.group(2))]
        if len(n) != 8:
            continue
        filas.append({
            'semana': pd.to_datetime(m.group(1), format='%d%b%Y'),
            'nino12': n[1], 'nino3': n[3], 'nino34': n[5], 'nino4': n[7],
        })
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--forzar', action='store_true', help='vuelve a descargar aunque existan los archivos')
    args = ap.parse_args()
    DATOS.mkdir(exist_ok=True)
    hoy = dt.date.today()
    tareas = {
        'metar_segu.csv': lambda: metar(hoy + dt.timedelta(days=1)),
        'pronosticos.csv': lambda: pronosticos(hoy - dt.timedelta(days=1)),
        'nino.csv': nino,
    }
    for nombre, bajar in tareas.items():
        ruta = DATOS / nombre
        if ruta.exists() and not args.forzar:
            print(f'{nombre}: ya existe')
            continue
        print(f'{nombre}: descargando…')
        df = bajar()
        df.to_csv(ruta, index=False)
        print(f'{nombre}: {len(df)} filas')


if __name__ == '__main__':
    main()
