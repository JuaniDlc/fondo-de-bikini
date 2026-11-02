"""Historial para probar las nubes bajas de GOES en el modelo, cerca de Guayaquil. Una imagen por hora.

Las nubes bajas son tibias: el infrarrojo del modelo, que mira las nubes frías, no las ve.
- Canales 7 (3,9 µm), 13 (10,3 µm) y 15 (12,3 µm), de 2 km: la diferencia 13 − 7 marca nubes bajas de
  noche, y 13 − 15 distingue nube gruesa de nube alta delgada.
- Canal 3 (0,86 µm), de 1 km, solo de día: cuánta luz refleja la nube; más es más gruesa.

Uso: python analisis/nubes_bajas_historial.py 2025-03 [carpeta]   (o un día: 2025-03-14)
Escribe <carpeta>/nubes-bajas-2025-03.csv (por defecto analisis/datos/nubes-bajas/).
"""

import datetime as dt
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from infrarrojo import CAMPOS_BAJAS as CAMPOS, leer_caja, resumen_bajas  # noqa: E402
from infrarrojo_historial import BUCKETS, inicio, pedir  # noqa: E402
from nubes_historial import claves  # noqa: E402


def leer_canal(sat_clave):
    sat, clave = sat_clave
    try:
        x, plat, plon = leer_caja(BUCKETS[sat] + clave, pedir)
        return inicio(clave), x.astype(np.float32), plat, plon
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return inicio(clave), None, None, None


def hora_completa(hora):
    canales = {}
    for canal in ('C13', 'C07', 'C15', 'C03'):
        lista = claves('ABI-L2-CMIPF', hora, f'{canal}_')
        if lista:
            t, x, plat, plon = leer_canal(lista[0])
            if x is not None:
                canales[canal] = (x, plat, plon)
    return hora, resumen_bajas(canales)


def main():
    texto = sys.argv[1]
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'nubes-bajas'
    carpeta.mkdir(parents=True, exist_ok=True)
    if len(texto) == 7:
        desde = dt.datetime.strptime(texto, '%Y-%m').replace(tzinfo=dt.timezone.utc)
        fin = (desde + dt.timedelta(days=32)).replace(day=1)
    else:
        desde = dt.datetime.strptime(texto, '%Y-%m-%d').replace(tzinfo=dt.timezone.utc)
        fin = desde + dt.timedelta(days=1)
    horas = [desde + dt.timedelta(hours=i) for i in range(int((fin - desde).total_seconds() // 3600))]
    with ThreadPoolExecutor(12) as ex:
        filas = list(ex.map(hora_completa, horas))
    lineas = [','.join(['inicio'] + CAMPOS)]
    for t, r in filas:
        lineas.append(','.join([t.strftime('%Y-%m-%dT%H:%MZ')] + ['' if math.isnan(r[c]) else f'{r[c]:.3f}' for c in CAMPOS]))
    salida = carpeta / f'nubes-bajas-{texto}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(filas)} filas', flush=True)


if __name__ == '__main__':
    main()
