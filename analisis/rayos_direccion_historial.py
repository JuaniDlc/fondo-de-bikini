"""Historial de dónde están los rayos alrededor de Guayaquil, cada 10 minutos, para probar la dirección.

rayos_historial.py guarda cuántos rayos hay y a qué distancia, no hacia dónde. Este lee los mismos
archivos y guarda, para los rayos a menos de 150 km: cuántos hay, la suma de sus posiciones en km al
este (x) y al norte (y) del centro, con lo que se saca dónde está el centro de la actividad y cómo se
mueve, y cuántos hay en cada uno de los 8 sectores a menos de 60 km.

Uso: python analisis/rayos_direccion_historial.py 2025-03 [carpeta]   (o un día: 2025-03-14)
Escribe <carpeta>/direccion-2025-03.csv (por defecto analisis/datos/rayos-direccion/). Lo corre el
workflow «Historial de dirección de rayos», uno por mes, porque son unos 45 GB por mes.
"""

import datetime as dt
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rayos import distancia_y_rumbo  # noqa: E402
from rayos_historial import claves_hora, inicio, leer  # noqa: E402

RADIO_KM = 150
SECTORES_KM = 60
SECTORES = [f's{i}' for i in range(8)]  # s0 es el norte, s1 el noreste, y así en sentido horario
COLUMNAS = ['bloque', 'archivos', 'n', 'suma_x', 'suma_y', *SECTORES]


def resumir(lat, lon):
    """Lo que aporta un archivo: cuántos rayos, la suma de sus posiciones y los sectores."""
    d, r = distancia_y_rumbo(np.asarray(lat, dtype=float), np.asarray(lon, dtype=float))
    dentro = d <= RADIO_KM
    d, rad = d[dentro], np.radians(r[dentro])
    cerca = d <= SECTORES_KM
    sector = np.round((np.degrees(rad[cerca]) % 360) / 45).astype(int) % 8
    return {'n': int(dentro.sum()), 'suma_x': float((d * np.sin(rad)).sum()), 'suma_y': float((d * np.cos(rad)).sum()),
            **{f's{i}': int((sector == i).sum()) for i in range(8)}}


def main():
    texto = sys.argv[1]
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'rayos-direccion'
    carpeta.mkdir(parents=True, exist_ok=True)
    if len(texto) == 7:
        desde = dt.datetime.strptime(texto, '%Y-%m').replace(tzinfo=dt.timezone.utc)
        fin = (desde + dt.timedelta(days=32)).replace(day=1)
    else:
        desde = dt.datetime.strptime(texto, '%Y-%m-%d').replace(tzinfo=dt.timezone.utc)
        fin = desde + dt.timedelta(days=1)
    horas = [desde + dt.timedelta(hours=i) for i in range(int((fin - desde).total_seconds() // 3600))]
    with ThreadPoolExecutor(4) as ex:
        listas = list(ex.map(claves_hora, horas))
    trabajos = [(sat, c) for sat, claves in listas for c in claves]
    print(f'{texto}: {len(trabajos)} archivos', flush=True)

    bloques = {}
    with ThreadPoolExecutor(32) as ex:
        for n, (clave, lat, lon) in enumerate(ex.map(leer, trabajos), 1):
            if lat is None:
                continue
            t = inicio(clave)
            b = t.replace(minute=t.minute // 10 * 10, second=0)
            fila = bloques.setdefault(b, dict.fromkeys(COLUMNAS[1:], 0))
            fila['archivos'] += 1
            for c, v in resumir(lat, lon).items():
                fila[c] += v
            if n % 10000 == 0:
                print(f'  {n}/{len(trabajos)}', flush=True)

    lineas = [','.join(COLUMNAS)]
    for b in sorted(bloques):
        f = bloques[b]
        lineas.append(','.join([b.strftime('%Y-%m-%dT%H:%MZ'), str(f['archivos']), str(f['n']),
                                f"{f['suma_x']:.1f}", f"{f['suma_y']:.1f}", *[str(f[s]) for s in SECTORES]]))
    salida = carpeta / f'direccion-{texto}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(bloques)} bloques de 10 minutos', flush=True)


if __name__ == '__main__':
    main()
