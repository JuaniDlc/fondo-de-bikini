"""Historial para probar más datos de GOES en el modelo: movimiento de las nubes, vapor de agua e
inestabilidad del aire, cerca de Guayaquil. Una fila por imagen infrarroja (cada 10 minutos).

- Movimiento (canal 13, cada 10 min): cuánto se movieron las nubes frías en los últimos 30 minutos
  (correlación de las dos imágenes), en km/h hacia el este (u) y hacia el norte (v), y qué tan frías
  están las nubes «aguas arriba»: las que, a esa velocidad, llegarían a Guayaquil en 20, 40 o 60 min.
- Vapor de agua (canales 8 y 10, una imagen por hora): temperatura media a menos de 60 km; más fría
  es más húmeda (canal 8: capas altas; canal 10: capas medias).
- Inestabilidad y agua precipitable (productos DSI y TPW, una imagen por hora, solo con cielo
  despejado): mediana a menos de 100 km de CAPE, LI, índice K y agua precipitable.

Uso: python analisis/nubes_historial.py 2025-03 [carpeta]   (o un día: 2025-03-14)
Escribe <carpeta>/nubes-2025-03.csv (por defecto analisis/datos/nubes/). Lo corre el workflow
«Historial de nubes», uno por mes.
"""

import datetime as dt
import math
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from infrarrojo import FILAS, FRIO_K, ArchivoRemoto, distancias, leer_caja  # noqa: E402
from infrarrojo_historial import BUCKETS, GOES19_DESDE, inicio, pedir  # noqa: E402

KM_PIXEL = 2.0
SEPARACION = 3  # imágenes entre las dos que se comparan: 30 minutos, para medir más de un píxel
MAX_PX = 18  # 18 píxeles en 30 minutos = 72 km/h; más rápido no es una nube de tormenta
ADELANTOS_MIN = (20, 40, 60)
RADIO_ARRIBA_KM = 15
CAMPOS = (['u', 'v', 'mov_frio']
          + [f'arriba_{m}_{c}' for m in ADELANTOS_MIN for c in ('frio', 'area')]
          + ['vapor8_60', 'vapor10_60', 'cape_100', 'li_100', 'ki_100', 'tpw_100', 'despejado_100'])


def claves(producto, hora, filtro=''):
    orden = ['goes19', 'goes16'] if hora >= GOES19_DESDE else ['goes16', 'goes19']
    for sat in orden:
        r = pedir(BUCKETS[sat], params={'list-type': '2', 'prefix': f'{producto}/{hora:%Y/%j/%H}/'})
        cs = [c for c in re.findall(r'<Key>([^<]+)</Key>', r.text) if filtro in c]
        if cs:
            return [(sat, c) for c in sorted(cs)]
    return []


def caja(sat_clave):
    sat, clave = sat_clave
    try:
        tb, plat, plon = leer_caja(BUCKETS[sat] + clave, pedir)
        return inicio(clave), tb.astype(np.float32), plat, plon
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return inicio(clave), None, None, None


def desplazamiento(antes, ahora):
    """(filas, columnas) que se movió el campo de nubes frías de «antes» a «ahora»; None si no hay
    nubes frías suficientes. Correlación cruzada por FFT, solo en desplazamientos de ±MAX_PX."""
    a, b = (np.nan_to_num(np.clip(FRIO_K + 25 - x, 0, None)) for x in (antes, ahora))  # nubes bajo 260 K
    if (a > 0).mean() < 0.02 or (b > 0).mean() < 0.02:
        return None
    a, b = a - a.mean(), b - b.mean()
    c = np.fft.irfft2(np.conj(np.fft.rfft2(a)) * np.fft.rfft2(b), s=a.shape)
    c = np.roll(np.roll(c, MAX_PX, 0), MAX_PX, 1)[: 2 * MAX_PX + 1, : 2 * MAX_PX + 1]
    i, j = np.unravel_index(np.argmax(c), c.shape)
    # Ajuste parabólico para fracciones de píxel
    def fino(cm, c0, cp):
        d = cm - 2 * c0 + cp
        return 0.0 if d == 0 else 0.5 * (cm - cp) / d
    di = i - MAX_PX + (fino(c[i - 1, j], c[i, j], c[i + 1, j]) if 0 < i < 2 * MAX_PX else 0)
    dj = j - MAX_PX + (fino(c[i, j - 1], c[i, j], c[i, j + 1]) if 0 < j < 2 * MAX_PX else 0)
    return di, dj


def movimiento(antes, ahora, minutos):
    """Variables de movimiento y de las nubes aguas arriba a partir de dos recuadros seguidos."""
    v = {c: math.nan for c in CAMPOS[: 3 + 2 * len(ADELANTOS_MIN)]}
    d = None if antes is None or ahora is None or not 25 <= minutos <= 35 else desplazamiento(antes, ahora)
    if d is None:
        return v
    di, dj = d
    por_hora = 60 / minutos
    v['u'] = dj * KM_PIXEL * por_hora  # columnas crecen hacia el este
    v['v'] = -di * KM_PIXEL * por_hora  # filas crecen hacia el sur
    v['mov_frio'] = float(np.nanmean(ahora < FRIO_K))
    n = ahora.shape[0]
    fi, co = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
    for m in ADELANTOS_MIN:
        # La nube que llegará al centro en m minutos está ahora en centro − velocidad · m.
        ci = FILAS - di * m / minutos
        cj = FILAS - dj * m / minutos
        cerca = (np.hypot(fi - ci, co - cj) * KM_PIXEL) <= RADIO_ARRIBA_KM
        valores = ahora[cerca]
        v[f'arriba_{m}_frio'] = float(np.clip(270 - np.nanmin(valores), 0, None)) if np.isfinite(valores).any() else math.nan
        v[f'arriba_{m}_area'] = float(np.nanmean(valores < FRIO_K))
    return v


def vapor(sat_clave):
    """Temperatura media del canal de vapor a menos de 60 km."""
    t, tb, plat, plon = caja(sat_clave)
    if tb is None:
        return t, math.nan
    return t, float(np.nanmean(tb[distancias(plat, plon) <= 60]))


_indices = {}


def recuadro_10km(f, variable, radio_px=10):
    """Valores de una variable de un producto de 10 km alrededor de Guayaquil (±radio_px píxeles)."""
    proj = f['goes_imager_projection'].attrs
    clave = float(proj['longitude_of_projection_origin'][0])
    if clave not in _indices:
        from satelite_lluvia_historial import indice
        _indices[clave] = indice(f, -2.19, -79.89)
    fila, col = _indices[clave]
    v = f[variable]
    crudo = v[fila - radio_px: fila + radio_px + 1, col - radio_px: col + radio_px + 1]
    x = crudo * float(v.attrs.get('scale_factor', [1])[0]) + float(v.attrs.get('add_offset', [0])[0])
    malo = crudo == v.attrs['_FillValue'][0]
    if 'DQF_Overall' in f:
        malo |= f['DQF_Overall'][fila - radio_px: fila + radio_px + 1, col - radio_px: col + radio_px + 1] != 0
    x = np.where(malo, np.nan, x)
    di, dj = np.meshgrid(np.arange(-radio_px, radio_px + 1), np.arange(-radio_px, radio_px + 1), indexing='ij')
    return x[np.hypot(di, dj) * 10 <= 100]


def estabilidad(sat_clave):
    """Mediana a menos de 100 km de CAPE, LI e índice K (DSI) o del agua precipitable (TPW)."""
    sat, clave = sat_clave
    try:
        with h5py.File(ArchivoRemoto(BUCKETS[sat] + clave, pedir), 'r') as f:
            if 'TPW' in f:
                x = recuadro_10km(f, 'TPW')
                return inicio(clave), {'tpw_100': float(np.nanmedian(x)) if np.isfinite(x).any() else math.nan,
                                       'despejado_100': float(np.isfinite(x).mean())}
            r = {}
            for var, campo in (('CAPE', 'cape_100'), ('LI', 'li_100'), ('KI', 'ki_100')):
                x = recuadro_10km(f, var)
                r[campo] = float(np.nanmedian(x)) if np.isfinite(x).any() else math.nan
            return inicio(clave), r
    except Exception as e:  # noqa: BLE001
        print(f'  no se pudo leer {clave}: {e}', flush=True)
        return inicio(clave), {}


def main():
    texto = sys.argv[1]
    carpeta = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'datos' / 'nubes'
    carpeta.mkdir(parents=True, exist_ok=True)
    if len(texto) == 7:
        desde = dt.datetime.strptime(texto, '%Y-%m').replace(tzinfo=dt.timezone.utc)
        fin = (desde + dt.timedelta(days=32)).replace(day=1)
    else:
        desde = dt.datetime.strptime(texto, '%Y-%m-%d').replace(tzinfo=dt.timezone.utc)
        fin = desde + dt.timedelta(days=1)
    horas = [desde + dt.timedelta(hours=i) for i in range(int((fin - desde).total_seconds() // 3600))]

    # Las imágenes de los 30 minutos antes de la primera, para el movimiento
    previa = desde - dt.timedelta(minutes=10 * SEPARACION)
    with ThreadPoolExecutor(4) as ex:
        ir = [t for lista in ex.map(lambda h: claves('ABI-L2-CMIPF', h, 'C13_'), [previa.replace(minute=0)] + horas)
              for t in lista]
    ir = [t for t in ir if previa <= inicio(t[1]) < fin]
    print(f'{texto}: {len(ir)} imágenes infrarrojas', flush=True)

    filas = {}
    with ThreadPoolExecutor(16) as ex:
        cajas = sorted(ex.map(caja, ir), key=lambda x: x[0])
    for (t0, a, *_), (t1, b, *_) in zip(cajas, cajas[SEPARACION:]):
        if t1 >= desde:
            filas[t1] = movimiento(a, b, (t1 - t0).total_seconds() / 60)
    del cajas

    # Una imagen por hora (la primera) de vapor de agua, inestabilidad y agua precipitable
    with ThreadPoolExecutor(4) as ex:
        primeras = {nombre: [lista[0] for lista in ex.map(lambda h: claves(producto, h, filtro), horas) if lista]
                    for nombre, producto, filtro in (('vapor8_60', 'ABI-L2-CMIPF', 'C08_'),
                                                     ('vapor10_60', 'ABI-L2-CMIPF', 'C10_'),
                                                     ('dsi', 'ABI-L2-DSIF', ''), ('tpw', 'ABI-L2-TPWF', ''))}
    porhora = {}
    with ThreadPoolExecutor(16) as ex:
        for nombre in ('vapor8_60', 'vapor10_60'):
            for t, x in ex.map(vapor, primeras[nombre]):
                porhora.setdefault(t.replace(minute=0, second=0), {})[nombre] = x
        for nombre in ('dsi', 'tpw'):
            for t, r in ex.map(estabilidad, primeras[nombre]):
                porhora.setdefault(t.replace(minute=0, second=0), {}).update(r)
    for t, r in porhora.items():
        destino = min((x for x in filas if x.replace(minute=0, second=0) == t), default=None)
        if destino is None:
            filas[t] = {c: math.nan for c in CAMPOS}
            destino = t
        filas[destino].update(r)

    lineas = [','.join(['inicio'] + CAMPOS)]
    for t in sorted(filas):
        r = filas[t]
        lineas.append(','.join([t.strftime('%Y-%m-%dT%H:%MZ')] + ['' if math.isnan(r.get(c, math.nan)) else f'{r[c]:.3f}'
                                                                   for c in CAMPOS]))
    salida = carpeta / f'nubes-{texto}.csv'
    salida.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print(f'{salida}: {len(filas)} filas', flush=True)


if __name__ == '__main__':
    main()
