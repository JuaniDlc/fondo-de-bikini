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
import os
import re
from concurrent.futures import ThreadPoolExecutor
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


# Para el modelo corregido: rayos por anillos de distancia (hasta 15 km, de 15 a 30, …) con todos
# los archivos, igual que analisis/rayos_historial.py para entrenar.
ANILLOS_KM = (15, 30, 60, 100, 150)


def resumen_anillos(lat, lon):
    """Cuántos rayos hay en cada anillo y la distancia del más cercano (inf si no hay)."""
    d, _ = distancia_y_rumbo(np.asarray(lat, dtype=float), np.asarray(lon, dtype=float))
    cuentas, desde = {}, 0
    for hasta in ANILLOS_KM:
        cuentas[hasta] = int(((d > desde) & (d <= hasta)).sum()) if desde else int((d <= hasta).sum())
        desde = hasta
    cerca = d[d <= ANILLOS_KM[-1]]
    return cuentas, float(cerca.min()) if cerca.size else math.inf


ARCHIVOS_HORA = 180  # uno cada 20 segundos


def variables_modelo(bloques):
    """Variables de rayos para el modelo corregido, igual que variables_rayos de analisis/entrenar.py.
    bloques: los 6 bloques de 10 minutos de la última hora, del más viejo al más nuevo, cada uno
    {'archivos': n, 'r15': …, 'r150': …, 'dmin': km o inf}. None si faltan archivos."""
    if len(bloques) != 6 or sum(b['archivos'] for b in bloques) < 0.8 * ARCHIVOS_HORA:
        return None
    cerca = lambda d: math.exp(-d / 30)  # noqa: E731
    dmin = lambda bs: min(b['dmin'] for b in bs)  # noqa: E731
    v = {f'rayos_{k}_1h': math.log1p(sum(b[f'r{k}'] for b in bloques)) for k in ANILLOS_KM}
    v['rayos_60_20m'] = math.log1p(sum(b[f'r{k}'] for b in bloques[-2:] for k in ANILLOS_KM if k <= 60))
    v['cercania_20m'] = cerca(dmin(bloques[-2:]))
    v['cercania_1h'] = cerca(dmin(bloques))
    v['acercamiento'] = cerca(dmin(bloques[-2:])) - cerca(dmin(bloques[:4]))
    return {k: round(x, 6) for k, x in v.items()}


def bloques_ultima_hora(hasta: dt.datetime, leer_archivo):
    """Bloques de 10 minutos de [hasta − 60 min, hasta) con todos los archivos."""
    claves = archivos(hasta - dt.timedelta(minutes=60), hasta)
    bloques = [{'archivos': 0, **{f'r{k}': 0 for k in ANILLOS_KM}, 'dmin': math.inf} for _ in range(6)]
    with ThreadPoolExecutor(16) as ex:
        leidos = list(ex.map(leer_archivo, claves))
    for clave, (lat, lon) in zip(claves, leidos):
        m = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', clave)
        inicio = dt.datetime.strptime(''.join(m.groups()), '%Y%j%H%M%S').replace(tzinfo=dt.timezone.utc)
        b = bloques[int((inicio - (hasta - dt.timedelta(minutes=60))).total_seconds() // 600)]
        cuentas, d = resumen_anillos(lat, lon)
        b['archivos'] += 1
        for k, x in cuentas.items():
            b[f'r{k}'] += x
        b['dmin'] = min(b['dmin'], d)
    return bloques


def leer(clave):
    """Rayos de buena calidad de un archivo: (lat, lon)."""
    datos = requests.get(BUCKET + clave, timeout=60).content
    with h5py.File(io.BytesIO(datos), 'r') as f:
        lat, lon = f['flash_lat'][:], f['flash_lon'][:]
        calidad = f['flash_quality_flag'][:]
    ok = calidad == 0
    return lat[ok], lon[ok]


def avisar_si_hay_que_guardar(modelo):
    """Le dice al workflow (salida «guardar») si conviene hacer commit de rayos.json: cuando
    cambian las variables del modelo o empieza otra hora, para que la página siempre tenga rayos
    de la hora en curso sin un commit cada 10 minutos."""
    try:
        anterior = json.loads(SALIDA.read_text(encoding='utf-8')).get('modelo')
    except (OSError, ValueError):
        anterior = None
    sin_hora = lambda m: {k: v for k, v in (m or {}).items() if k != 'hasta'}  # noqa: E731
    hora = lambda m: (m or {}).get('hasta', '')[:13]  # noqa: E731
    guardar = anterior is None or sin_hora(anterior) != sin_hora(modelo) or hora(anterior) != hora(modelo)
    salida = os.environ.get('GITHUB_OUTPUT')
    if salida:
        with open(salida, 'a', encoding='utf-8') as f:
            f.write(f'guardar={"si" if guardar else "no"}\n')


def main():
    ahora = dt.datetime.now(dt.timezone.utc)
    leidos = {}
    leer_una_vez = lambda c: leidos[c] if c in leidos else leidos.setdefault(c, leer(c))  # noqa: E731
    # Para el modelo corregido: la última hora completa en bloques de 10 minutos, con todos los
    # archivos. «hasta» es hora local de Guayaquil, como las horas de Open-Meteo.
    hasta = ahora.replace(minute=ahora.minute // 10 * 10, second=0, microsecond=0)
    variables = variables_modelo(bloques_ultima_hora(hasta, leer_una_vez))

    desde = ahora - dt.timedelta(minutes=MINUTOS)
    claves = archivos(desde, ahora)
    distancias, rumbos = [], []
    for clave in claves:
        lat, lon = leer_una_vez(clave)
        d, r = distancia_y_rumbo(lat, lon)
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
    resultado['modelo'] = None if variables is None else {
        'hasta': (hasta - dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M'), **variables}
    avisar_si_hay_que_guardar(resultado['modelo'])
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(resultado, ensure_ascii=False))
    if not claves:
        raise SystemExit('No se encontraron archivos del satélite en los últimos minutos')


if __name__ == '__main__':
    main()
