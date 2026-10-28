"""Historial de nubes de tormenta cerca de Guayaquil, una fila por imagen infrarroja (cada 10 min).

Lee el canal 13 de ABI de GOES-Este (GOES-16 hasta el 7 de abril de 2025, GOES-19 después)
desde el archivo público de NOAA en AWS, pero solo el recuadro alrededor de Guayaquil
(scripts/infrarrojo.py).

Uso: python analisis/infrarrojo_historial.py 2025-03 [carpeta]
Escribe <carpeta>/infrarrojo-2025-03.csv (por defecto analisis/datos/infrarrojo/). Lo corre el
workflow «Historial infrarrojo», uno por mes.
"""

import datetime as dt
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from infrarrojo import leer, sesion  # noqa: E402

GOES19_DESDE = dt.datetime(2025, 4, 7, tzinfo=dt.timezone.utc)
BUCKETS = {'goes16': 'https://noaa-goes16.s3.amazonaws.com/', 'goes19': 'https://noaa-goes19.s3.amazonaws.com/'}
CAMPOS = ['tb_centro', 'tbmin_15', 'tbmin_30', 'tbmin_60', 'tbmin_100', 'frio_30', 'frio_60', 'frio_100', 'muy_frio_60']


def pedir(url, metodo='get', **kwargs):
    """GET o HEAD con reintentos: S3 responde 503 «Slow Down» si se le pide demasiado rápido."""
    for intento in range(8):
        try:
            r = getattr(sesion, metodo)(url, timeout=60, **kwargs)
            if r.status_code not in (500, 503):
                r.raise_for_status()
                return r
        except requests.RequestException:
            if intento == 7:
                raise
        time.sleep(min(60, 2 ** intento) * (0.5 + random.random()))
    r.raise_for_status()


def claves_hora(hora):
    """Imágenes del canal 13 de una hora UTC; prueba el otro satélite si no hay."""
    orden = ['goes19', 'goes16'] if hora >= GOES19_DESDE else ['goes16', 'goes19']
    for sat in orden:
        r = pedir(BUCKETS[sat], params={'list-type': '2', 'prefix': f'ABI-L2-CMIPF/{hora:%Y/%j/%H}/'})
        claves = [c for c in re.findall(r'<Key>([^<]+)</Key>', r.text) if 'C13_' in c]
        if claves:
            return [(sat, c) for c in claves]
    return []


def resumir(sat_clave):
    sat, clave = sat_clave
    try:
        return clave, leer(BUCKETS[sat] + clave, pedir)
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return clave, None


def inicio(clave):
    m = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', clave)
    return dt.datetime.strptime(''.join(m.groups()), '%Y%j%H%M%S').replace(tzinfo=dt.timezone.utc)


def main():
    mes = dt.datetime.strptime(sys.argv[1], '%Y-%m').replace(tzinfo=dt.timezone.utc)
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'infrarrojo'
    carpeta.mkdir(parents=True, exist_ok=True)
    fin = (mes + dt.timedelta(days=32)).replace(day=1)
    horas = [mes + dt.timedelta(hours=i) for i in range(int((fin - mes).total_seconds() // 3600))]
    with ThreadPoolExecutor(4) as ex:
        trabajos = [t for lista in ex.map(claves_hora, horas) for t in lista]
    print(f'{sys.argv[1]}: {len(trabajos)} imágenes', flush=True)

    filas = []
    with ThreadPoolExecutor(16) as ex:
        for n, (clave, r) in enumerate(ex.map(resumir, trabajos), 1):
            if r is not None:
                filas.append((inicio(clave), r))
            if n % 1000 == 0:
                print(f'  {n}/{len(trabajos)}', flush=True)
    lineas = [','.join(['inicio'] + CAMPOS)]
    for t, r in sorted(filas, key=lambda x: x[0]):
        lineas.append(','.join([t.strftime('%Y-%m-%dT%H:%MZ')] + [str(r[c]) for c in CAMPOS]))
    salida = carpeta / f'infrarrojo-{sys.argv[1]}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(filas)} imágenes', flush=True)


if __name__ == '__main__':
    main()
