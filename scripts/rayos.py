"""Rayos cerca de Guayaquil en los últimos minutos, según el satélite GOES-19 (sensor GLM).

Baja los archivos de rayos (uno cada 20 s, ~0.3 MB) de los últimos MINUTOS minutos desde el
archivo público de NOAA en AWS, se queda con los rayos a menos de RADIO_KM de Guayaquil y
escribe data/rayos.json con cuántos hay, el más cercano y hacia dónde están.

Lo corre el workflow «Rayos» cada 10 minutos.
"""

import datetime as dt
import io
import json
import math
import re
from pathlib import Path

import h5py
import numpy as np
import requests

LAT, LON = -2.19, -79.89
MINUTOS = 10
RADIO_KM = 60
CERCA_KM = 25
BUCKET = 'https://noaa-goes19.s3.amazonaws.com/'
SALIDA = Path(__file__).resolve().parent.parent / 'data' / 'rayos.json'
RUMBOS = ['norte', 'noreste', 'este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste']


def archivos(desde: dt.datetime, hasta: dt.datetime) -> list[str]:
    """Claves de los archivos GLM que empiezan entre desde y hasta (UTC)."""
    claves = []
    horas = {desde.replace(minute=0, second=0, microsecond=0), hasta.replace(minute=0, second=0, microsecond=0)}
    for h in sorted(horas):
        r = requests.get(BUCKET, params={'list-type': '2', 'prefix': f'GLM-L2-LCFA/{h:%Y/%j/%H}/'}, timeout=60)
        r.raise_for_status()
        for clave in re.findall(r'<Key>([^<]+)</Key>', r.text):
            m = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', clave)
            inicio = dt.datetime.strptime(''.join(m.groups()), '%Y%j%H%M%S').replace(tzinfo=dt.timezone.utc)
            if desde <= inicio < hasta:
                claves.append(clave)
    return claves


def distancia_y_rumbo(lat, lon):
    """Distancia (km) y rumbo (grados desde el norte) desde Guayaquil."""
    f1, f2 = math.radians(LAT), np.radians(lat)
    dl = np.radians(lon - LON)
    a = np.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * np.cos(f2) * np.sin(dl / 2) ** 2
    d = 2 * 6371 * np.arcsin(np.sqrt(a))
    rumbo = np.degrees(np.arctan2(np.sin(dl) * np.cos(f2),
                                  math.cos(f1) * np.sin(f2) - math.sin(f1) * np.cos(f2) * np.cos(dl))) % 360
    return d, rumbo


# Para el modelo corregido: rayos por anillos de distancia (hasta 15 km, de 15 a 30, …) con una
# muestra fija de archivos, la misma que usa analisis/rayos_historial.py para entrenar.
ANILLOS_KM = (15, 30, 60, 100, 150)


def en_muestra(clave: str) -> bool:
    """El primer archivo (20 s) de cada minuto par."""
    m = re.search(r'_s\d{7}\d{2}(\d{2})(\d{2})', clave)
    return int(m[1]) % 2 == 0 and int(m[2]) < 20


def resumen_anillos(lat, lon):
    """Cuántos rayos hay en cada anillo y la distancia del más cercano (inf si no hay)."""
    d, _ = distancia_y_rumbo(np.asarray(lat, dtype=float), np.asarray(lon, dtype=float))
    cuentas, desde = {}, 0
    for hasta in ANILLOS_KM:
        cuentas[hasta] = int(((d > desde) & (d <= hasta)).sum()) if desde else int((d <= hasta).sum())
        desde = hasta
    cerca = d[d <= ANILLOS_KM[-1]]
    return cuentas, float(cerca.min()) if cerca.size else math.inf


def main():
    ahora = dt.datetime.now(dt.timezone.utc)
    desde = ahora - dt.timedelta(minutes=MINUTOS)
    claves = archivos(desde, ahora)
    distancias, rumbos = [], []
    for clave in claves:
        datos = requests.get(BUCKET + clave, timeout=60).content
        with h5py.File(io.BytesIO(datos), 'r') as f:
            lat, lon = f['flash_lat'][:], f['flash_lon'][:]
            calidad = f['flash_quality_flag'][:]
        ok = calidad == 0
        d, r = distancia_y_rumbo(lat[ok], lon[ok])
        dentro = d <= RADIO_KM
        distancias.extend(d[dentro].tolist())
        rumbos.extend(r[dentro].tolist())

    resultado = {
        'generado': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'minutos': MINUTOS,
        'archivos': len(claves),
        'radio_km': RADIO_KM,
        'rayos': len(distancias),
        'rayos_cerca': sum(d <= CERCA_KM for d in distancias),
        'mas_cercano_km': round(min(distancias), 1) if distancias else None,
        'rumbo': None,
    }
    if rumbos:
        # Rumbo promedio (circular) de los rayos, en palabras
        ang = math.degrees(math.atan2(sum(math.sin(math.radians(x)) for x in rumbos),
                                      sum(math.cos(math.radians(x)) for x in rumbos))) % 360
        resultado['rumbo'] = RUMBOS[round(ang / 45) % 8]
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(resultado, ensure_ascii=False))
    if not claves:
        raise SystemExit('No se encontraron archivos del satélite en los últimos minutos')


if __name__ == '__main__':
    main()
