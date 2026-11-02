"""Descarga lo que hace falta para probar el modelo combinado (analisis/combinado.py).

- Viento en altura y humedad a 850 hPa (GFS), de los pronósticos históricos de Open-Meteo.
- Temperatura del mar en tres puntos frente a la costa de Guayaquil, de la API marina de Open-Meteo.

Guarda CSV en analisis/datos/combinado/. Si un archivo ya existe no lo vuelve a bajar; usa --forzar.
La presión de vapor en superficie y el viento a 10 m salen de analisis/datos/pronosticos.csv.
"""

import argparse
import datetime as dt
import time
from pathlib import Path

import pandas as pd
import requests

DATOS = Path(__file__).parent / 'datos' / 'combinado'
INICIO = dt.date(2023, 1, 1)
FIN = dt.date(2026, 10, 27)  # hasta donde llega analisis/datos/pronosticos.csv
LAT, LON = -2.19, -79.89
ZONA = 'America/Guayaquil'
ALTURA = [f'{v}_{nivel}hPa' for nivel in (850, 500, 200) for v in ('wind_speed', 'wind_direction')]
ALTURA += ['temperature_850hPa', 'relative_humidity_850hPa']
# Puntos en el mar: frente a la entrada del golfo, mar afuera y frente a la península.
MAR = {'golfo': (-3.0, -80.5), 'costa': (-2.6, -80.6), 'afuera': (-2.3, -81.2)}


def pedir(url, params):
    for espera in (5, 30, 90, None):
        r = requests.get(url, params=params, timeout=600)
        if r.ok or espera is None:
            r.raise_for_status()
            return r.json()
        print(f'  respondió {r.status_code}; se reintenta en {espera} s', flush=True)
        time.sleep(espera)


def por_anios(url, params):
    partes = []
    for anio in range(INICIO.year, FIN.year + 1):
        desde, hasta = max(INICIO, dt.date(anio, 1, 1)), min(FIN, dt.date(anio, 12, 31))
        d = pedir(url, {**params, 'timezone': ZONA, 'start_date': desde.isoformat(), 'end_date': hasta.isoformat()})
        partes.append(pd.DataFrame(d['hourly']))
        print(f'  {desde} → {hasta}', flush=True)
    return pd.concat(partes, ignore_index=True)


def altura():
    return por_anios('https://historical-forecast-api.open-meteo.com/v1/forecast',
                     {'latitude': LAT, 'longitude': LON, 'hourly': ','.join(ALTURA), 'models': 'gfs_seamless'})


def mar():
    tabla = None
    for nombre, (lat, lon) in MAR.items():
        d = por_anios('https://marine-api.open-meteo.com/v1/marine',
                      {'latitude': lat, 'longitude': lon, 'hourly': 'sea_surface_temperature', 'cell_selection': 'sea'})
        d = d.rename(columns={'sea_surface_temperature': f'sst_{nombre}'})
        tabla = d if tabla is None else tabla.merge(d, on='time', how='outer')
    return tabla


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--forzar', action='store_true', help='vuelve a descargar aunque existan los archivos')
    args = ap.parse_args()
    DATOS.mkdir(parents=True, exist_ok=True)
    for nombre, bajar in (('altura.csv', altura), ('mar.csv', mar)):
        ruta = DATOS / nombre
        if ruta.exists() and not args.forzar:
            print(f'{nombre}: ya existe')
            continue
        print(f'{nombre}: descargando…', flush=True)
        d = bajar()
        d.to_csv(ruta, index=False)
        print(f'{nombre}: {len(d)} filas; datos por columna:\n{d.notna().mean().round(3).to_string()}', flush=True)


if __name__ == '__main__':
    main()
