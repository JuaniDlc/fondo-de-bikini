"""Lluvia de IMERG (NASA, satélites de microondas + infrarrojo, cuadros de 0,1° ≈ 11 km, cada 30 min)
en el aeropuerto y en los lugares, para ver si sirve como verdad en lugares sin estación.

Usa la versión final de IMERG (calibrada con pluviómetros, sale unos 3 meses y medio después) y,
para los meses que aún no la tienen, la versión «Late» (unas 14 horas después).

Necesita EARTHDATA_TOKEN (un token de https://urs.earthdata.nasa.gov, «Generate Token», con la
aplicación «NASA GESDISC DATA ARCHIVE» autorizada). Si existe LUGARES («Nombre:lat,lon;…», el mismo
secreto que scripts/rayos.py), agrega una columna por lugar; nunca escribe sus coordenadas.

Uso: python analisis/imerg_historial.py 2025-03 [carpeta]
Escribe <carpeta>/imerg-2025-03.csv (por defecto analisis/datos/imerg/). Lo corre el workflow
«Historial de IMERG», uno por mes.
"""

import datetime as dt
import io
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h5py
import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from rayos import AEROPUERTO, leer_lugares  # noqa: E402

RAIZ = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/'
PRODUCTOS = ('GPM_3IMERGHH.07', 'GPM_3IMERGHHL.07')  # final; si no hay, «Late»


class SesionNASA(requests.Session):
    """Mantiene el token al pasar por la redirección de Earthdata Login (requests lo quita al
    cambiar de servidor)."""

    def rebuild_auth(self, preparada, respuesta):
        if not (preparada.url.split('/')[2].endswith('nasa.gov')):
            super().rebuild_auth(preparada, respuesta)


sesion = SesionNASA()
sesion.headers['Authorization'] = f'Bearer {os.environ.get("EARTHDATA_TOKEN", "")}'
sesion.mount('https://', requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=32, max_retries=3))


def archivos_del_dia(dia):
    """URLs de los 48 archivos de media hora de un día (el producto final si existe)."""
    for producto in PRODUCTOS:
        carpeta = f'{RAIZ}{producto}/{dia:%Y}/{dia.timetuple().tm_yday:03d}/'
        r = requests.get(carpeta, timeout=60)
        if r.ok:
            nombres = sorted(set(re.findall(r'href="(3B-HHR[^"]+\.HDF5)"', r.text)))
            if nombres:
                return [carpeta + n for n in nombres]
    return []


def indices(lat, lon):
    return int((lon + 180) / 0.1), int((lat + 90) / 0.1)


def leer(url, puntos):
    """mm/h en el cuadro de cada punto y el máximo de los 3 × 3 cuadros alrededor."""
    m = re.search(r'\.(\d{8})-S(\d{6})-', url)
    inicio = dt.datetime.strptime(''.join(m.groups()), '%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc)
    for intento in range(3):
        try:
            r = sesion.get(url, timeout=120)
            r.raise_for_status()
            if not r.content.startswith(b'\x89HDF'):
                raise RuntimeError('no es un archivo HDF5 (¿token vencido o aplicación sin autorizar?)')
            with h5py.File(io.BytesIO(r.content), 'r') as f:
                p = f['Grid/precipitation']
                fila = {}
                for nombre, (i, j) in puntos.items():
                    caja = p[0, i - 1: i + 2, j - 1: j + 2].astype(float)
                    caja[caja < 0] = np.nan
                    fila[nombre] = caja[1, 1]
                    fila[f'{nombre} 3x3'] = np.nanmax(caja) if np.isfinite(caja).any() else np.nan
                return inicio, fila
        except Exception as e:  # noqa: BLE001
            error = e
    print(f'  no se pudo leer {url.rsplit("/", 1)[-1]}: {error}', flush=True)
    return inicio, None


def main():
    if not os.environ.get('EARTHDATA_TOKEN'):
        raise SystemExit('Falta EARTHDATA_TOKEN')
    mes = dt.datetime.strptime(sys.argv[1], '%Y-%m').replace(tzinfo=dt.timezone.utc)
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'imerg'
    carpeta.mkdir(parents=True, exist_ok=True)
    fin = (mes + dt.timedelta(days=32)).replace(day=1)
    puntos = {'Aeropuerto': indices(*AEROPUERTO),
              **{n: indices(*c) for n, c in leer_lugares(os.environ.get('LUGARES')).items()}}
    dias = [mes + dt.timedelta(days=i) for i in range((fin - mes).days)]
    with ThreadPoolExecutor(4) as ex:
        urls = [u for lista in ex.map(archivos_del_dia, dias) for u in lista]
    print(f'{sys.argv[1]}: {len(urls)} archivos', flush=True)
    filas = []
    with ThreadPoolExecutor(12) as ex:
        for n, (inicio, fila) in enumerate(ex.map(lambda u: leer(u, puntos), urls), 1):
            if fila is not None:
                filas.append((inicio, fila))
            if n % 200 == 0:
                print(f'  {n}/{len(urls)}', flush=True)
    if not filas:
        raise SystemExit('No se pudo leer ningún archivo')
    columnas = list(filas[0][1])
    lineas = [','.join(['inicio'] + columnas)]
    for inicio, fila in sorted(filas, key=lambda x: x[0]):
        lineas.append(','.join([inicio.strftime('%Y-%m-%dT%H:%MZ')]
                               + ['' if np.isnan(fila[c]) else f'{fila[c]:.2f}' for c in columnas]))
    salida = carpeta / f'imerg-{sys.argv[1]}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(filas)} medias horas', flush=True)


if __name__ == '__main__':
    main()
