"""Lluvia estimada por satélite (GOES, producto RRQPE, cuadritos de 2 km) en el aeropuerto,
una fila por imagen (cada 10 minutos), para ver si coincide con lo que reportó el aeropuerto.

Uso: python analisis/satelite_lluvia_historial.py 2025-03 [carpeta]
Escribe <carpeta>/satelite-lluvia-2025-03.csv (por defecto analisis/datos/satelite-lluvia/).
Lo corre el workflow «Historial de lluvia por satélite», uno por mes.
"""

import datetime as dt
import io
import math
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from infrarrojo_historial import BUCKETS, GOES19_DESDE, inicio, pedir  # noqa: E402

AEROPUERTO = (-2.1572, -79.8836)
RADIO_PX = 5  # ±10 km
KM_PIXEL = 2.0
CAMPOS = ['aero', 'aero_2km', 'aero_5km', 'aero_10km', 'media_10km']
_indice = {}


def indice(f, lat, lon):
    """Fila y columna del píxel (grilla fija de GOES-R) más cercano al punto."""
    proj = f['goes_imager_projection'].attrs
    clave = (float(proj['longitude_of_projection_origin'][0]), lat, lon)
    if clave not in _indice:
        req, rpol = float(proj['semi_major_axis'][0]), float(proj['semi_minor_axis'][0])
        H = float(proj['perspective_point_height'][0]) + req
        lon0 = math.radians(clave[0])
        esc = lambda v: v[:] * float(v.attrs['scale_factor'][0]) + float(v.attrs['add_offset'][0])  # noqa: E731
        x, y = esc(f['x']), esc(f['y'])
        la, lo = math.radians(lat), math.radians(lon)
        latc = math.atan((rpol ** 2 / req ** 2) * math.tan(la))
        rc = rpol / math.sqrt(1 - (req ** 2 - rpol ** 2) / req ** 2 * math.cos(latc) ** 2)
        sx = H - rc * math.cos(latc) * math.cos(lo - lon0)
        sy, sz = -rc * math.cos(latc) * math.sin(lo - lon0), rc * math.sin(latc)
        _indice[clave] = (int(np.argmin(abs(y - math.atan(sz / sx)))),
                          int(np.argmin(abs(x - math.asin(-sy / math.sqrt(sx ** 2 + sy ** 2 + sz ** 2))))))
    return _indice[clave]


def resumir(sat_clave):
    sat, clave = sat_clave
    try:
        with h5py.File(io.BytesIO(pedir(BUCKETS[sat] + clave).content), 'r') as f:
            fila, col = indice(f, *AEROPUERTO)
            v = f['RRQPE']
            crudo = v[fila - RADIO_PX: fila + RADIO_PX + 1, col - RADIO_PX: col + RADIO_PX + 1]
            mm = crudo * float(v.attrs['scale_factor'][0])
            mm = np.where(crudo == v.attrs['_FillValue'][0], np.nan, mm)
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return clave, None
    if np.isnan(mm).mean() > 0.2:
        return clave, None
    di, dj = np.meshgrid(np.arange(-RADIO_PX, RADIO_PX + 1), np.arange(-RADIO_PX, RADIO_PX + 1), indexing='ij')
    d = KM_PIXEL * np.sqrt(di ** 2 + dj ** 2)
    r = {'aero': mm[RADIO_PX, RADIO_PX], 'aero_2km': np.nanmax(mm[d <= 3]), 'aero_5km': np.nanmax(mm[d <= 5]),
         'aero_10km': np.nanmax(mm[d <= 10]), 'media_10km': np.nanmean(mm[d <= 10])}
    return clave, {k: round(float(x), 3) for k, x in r.items()}


def claves_hora(hora):
    orden = ['goes19', 'goes16'] if hora >= GOES19_DESDE else ['goes16', 'goes19']
    for sat in orden:
        r = pedir(BUCKETS[sat], params={'list-type': '2', 'prefix': f'ABI-L2-RRQPEF/{hora:%Y/%j/%H}/'})
        claves = re.findall(r'<Key>([^<]+)</Key>', r.text)
        if claves:
            return [(sat, c) for c in claves]
    return []


def main():
    mes = dt.datetime.strptime(sys.argv[1], '%Y-%m').replace(tzinfo=dt.timezone.utc)
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'satelite-lluvia'
    carpeta.mkdir(parents=True, exist_ok=True)
    fin = (mes + dt.timedelta(days=32)).replace(day=1)
    horas = [mes + dt.timedelta(hours=i) for i in range(int((fin - mes).total_seconds() // 3600))]
    with ThreadPoolExecutor(4) as ex:
        trabajos = [t for lista in ex.map(claves_hora, horas) for t in lista]
    print(f'{sys.argv[1]}: {len(trabajos)} imágenes', flush=True)
    filas = []
    with ThreadPoolExecutor(24) as ex:
        for clave, r in ex.map(resumir, trabajos):
            if r is not None:
                filas.append((inicio(clave), r))
    lineas = [','.join(['inicio'] + CAMPOS)]
    for t, r in sorted(filas, key=lambda x: x[0]):
        lineas.append(','.join([t.strftime('%Y-%m-%dT%H:%MZ')] + [str(r[c]) for c in CAMPOS]))
    salida = carpeta / f'satelite-lluvia-{sys.argv[1]}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(filas)} imágenes', flush=True)


if __name__ == '__main__':
    main()
