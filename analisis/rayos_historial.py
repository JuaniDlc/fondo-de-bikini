"""Historial de rayos cerca de Guayaquil, cada 10 minutos, para entrenar el modelo corregido.

Lee los archivos del sensor GLM de GOES-Este (GOES-16 hasta el 7 de abril de 2025, GOES-19
después) desde el archivo público de NOAA en AWS. Para no bajar todo, usa la misma muestra que
scripts/rayos.py en vivo: el primer archivo (20 s) de cada minuto par. Cuenta los rayos por
anillos de distancia y guarda el más cercano.

Uso: python analisis/rayos_historial.py 2025-03 [carpeta]
Escribe <carpeta>/rayos-2025-03.csv (por defecto analisis/datos/rayos/). Lo corre el workflow
«Historial de rayos», uno por mes, porque son varios GB por mes.
"""

import datetime as dt
import io
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h5py
import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from rayos import ANILLOS_KM, en_muestra, resumen_anillos  # noqa: E402

GOES19_DESDE = dt.datetime(2025, 4, 7, tzinfo=dt.timezone.utc)
BUCKETS = {'goes16': 'https://noaa-goes16.s3.amazonaws.com/', 'goes19': 'https://noaa-goes19.s3.amazonaws.com/'}

sesion = requests.Session()
sesion.mount('https://', requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=64, max_retries=3))


def claves_hora(hora: dt.datetime) -> tuple[str, list[str]]:
    """Archivos de la muestra para una hora UTC; prueba el otro satélite si no hay."""
    orden = ['goes19', 'goes16'] if hora >= GOES19_DESDE else ['goes16', 'goes19']
    for sat in orden:
        r = sesion.get(BUCKETS[sat], params={'list-type': '2', 'prefix': f'GLM-L2-LCFA/{hora:%Y/%j/%H}/'}, timeout=60)
        r.raise_for_status()
        claves = [c for c in re.findall(r'<Key>([^<]+)</Key>', r.text) if en_muestra(c)]
        if claves:
            return sat, claves
    return '', []


def leer(sat_clave):
    sat, clave = sat_clave
    for intento in range(3):
        try:
            datos = sesion.get(BUCKETS[sat] + clave, timeout=60).content
            with h5py.File(io.BytesIO(datos), 'r') as f:
                lat, lon = f['flash_lat'][:], f['flash_lon'][:]
                calidad = f['flash_quality_flag'][:]
            return clave, lat[calidad == 0], lon[calidad == 0]
        except Exception as e:  # noqa: BLE001
            error = e
    print(f'  no se pudo leer {clave}: {error}', flush=True)
    return clave, None, None


def inicio(clave: str) -> dt.datetime:
    m = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', clave)
    return dt.datetime.strptime(''.join(m.groups()), '%Y%j%H%M%S').replace(tzinfo=dt.timezone.utc)


def main():
    mes = dt.datetime.strptime(sys.argv[1], '%Y-%m').replace(tzinfo=dt.timezone.utc)
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'rayos'
    carpeta.mkdir(parents=True, exist_ok=True)
    fin = (mes + dt.timedelta(days=32)).replace(day=1)
    horas = []
    h = mes
    while h < fin:
        horas.append(h)
        h += dt.timedelta(hours=1)

    with ThreadPoolExecutor(16) as ex:
        listas = list(ex.map(claves_hora, horas))
    trabajos = [(sat, c) for sat, claves in listas for c in claves]
    print(f'{sys.argv[1]}: {len(trabajos)} archivos', flush=True)

    bloques = {}
    with ThreadPoolExecutor(48) as ex:
        for n, (clave, lat, lon) in enumerate(ex.map(leer, trabajos), 1):
            if lat is None:
                continue
            t = inicio(clave)
            b = t.replace(minute=t.minute // 10 * 10, second=0)
            fila = bloques.setdefault(b, {'archivos': 0, **{f'r{k}': 0 for k in ANILLOS_KM}, 'dmin': np.inf})
            fila['archivos'] += 1
            cuentas, dmin = resumen_anillos(lat, lon)
            for k, v in cuentas.items():
                fila[f'r{k}'] += v
            fila['dmin'] = min(fila['dmin'], dmin)
            if n % 2000 == 0:
                print(f'  {n}/{len(trabajos)}', flush=True)

    columnas = ['bloque', 'archivos', *[f'r{k}' for k in ANILLOS_KM], 'dmin']
    lineas = [','.join(columnas)]
    for b in sorted(bloques):
        f = bloques[b]
        dmin = '' if np.isinf(f['dmin']) else f"{f['dmin']:.1f}"
        lineas.append(','.join([b.strftime('%Y-%m-%dT%H:%MZ'), str(f['archivos']),
                                *[str(f[f'r{k}']) for k in ANILLOS_KM], dmin]))
    salida = carpeta / f'rayos-{sys.argv[1]}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(bloques)} bloques de 10 minutos', flush=True)


if __name__ == '__main__':
    main()
