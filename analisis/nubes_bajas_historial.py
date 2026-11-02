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

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from infrarrojo import ArchivoRemoto, FILAS, _escalar, distancias, geometria  # noqa: E402
from infrarrojo_historial import BUCKETS, inicio, pedir  # noqa: E402
from nubes_historial import claves  # noqa: E402

RADIOS = (15, 30, 60)
CAMPOS = (['c13_centro', 'c3_centro']
          + [f'{c}_{r}' for r in RADIOS for c in ('c7', 'c13', 'c15', 'tibia', 'd13_7', 'd13_15', 'c3')])


def leer_canal(sat_clave):
    """Recuadro de un canal. El de 1 km se promedia a 2 km para que coincida píxel a píxel."""
    sat, clave = sat_clave
    try:
        with h5py.File(ArchivoRemoto(BUCKETS[sat] + clave, pedir), 'r') as f:
            fila, columna, plat, plon = geometria(f)
            ancho = f['CMI'].shape[0]
            cmi = f['CMI']
            if ancho > 6000:  # 1 km: el doble de píxeles
                fi, co = fila, columna
                crudo = cmi[fi - 2 * FILAS: fi + 2 * FILAS + 2, co - 2 * FILAS: co + 2 * FILAS + 2]
                x = _escalar(cmi, crudo.astype(float))
                x[crudo == cmi.attrs['_FillValue'][0]] = np.nan
                x = x.reshape(2 * FILAS + 1, 2, 2 * FILAS + 1, 2).mean(axis=(1, 3))
            else:
                crudo = cmi[fila - FILAS: fila + FILAS + 1, columna - FILAS: columna + FILAS + 1]
                x = _escalar(cmi, crudo.astype(float))
                x[crudo == cmi.attrs['_FillValue'][0]] = np.nan
        return inicio(clave), x.astype(np.float32), plat, plon
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return inicio(clave), None, None, None


def resumir(imagenes):
    """Variables de una hora a partir de {canal: recuadro}. Tibia: entre 273 y 290 K en el canal 13."""
    v = {c: math.nan for c in CAMPOS}
    c13, c7, c15, c3 = (imagenes.get(c, (None, None, None))[0] for c in ('C13', 'C07', 'C15', 'C03'))
    if c13 is None:
        return v
    _, plat, plon = imagenes['C13']
    d = distancias(plat, plon)
    media = lambda x, s: float(np.nanmean(x[s])) if np.isfinite(x[s]).any() else math.nan  # noqa: E731
    centro = d <= 5
    v['c13_centro'] = media(c13, centro)
    if c3 is not None:
        v['c3_centro'] = media(c3, centro)
    for r in RADIOS:
        s = d <= r
        v[f'c13_{r}'] = media(c13, s)
        v[f'tibia_{r}'] = media(((c13 >= 273) & (c13 < 290)).astype(float), s)
        if c7 is not None:
            v[f'c7_{r}'], v[f'd13_7_{r}'] = media(c7, s), media(c13 - c7, s)
        if c15 is not None:
            v[f'c15_{r}'], v[f'd13_15_{r}'] = media(c15, s), media(c13 - c15, s)
        if c3 is not None:
            v[f'c3_{r}'] = media(c3, s)
    return v


def hora_completa(hora):
    canales = {}
    for canal in ('C13', 'C07', 'C15', 'C03'):
        lista = claves('ABI-L2-CMIPF', hora, f'{canal}_')
        if lista:
            t, x, plat, plon = leer_canal(lista[0])
            if x is not None:
                canales[canal] = (x, plat, plon)
    return hora, resumir(canales)


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
