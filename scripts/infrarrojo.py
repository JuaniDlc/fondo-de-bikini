"""Nubes de tormenta cerca de Guayaquil en la imagen infrarroja de GOES-Este (ABI, canal 13).

La imagen es la temperatura del tope de las nubes: cuanto más fría, más alta la nube. Bajo 235 K
(−38 °C) suele ser una nube de tormenta; bajo 210 K, una muy fuerte. Cada imagen (una cada
10 minutos) pesa 25 MB, pero solo se bajan las filas alrededor de Guayaquil (~1,6 MB) pidiendo
partes del archivo por HTTP.

Lo usan analisis/infrarrojo_historial.py (historial para entrenar) y el workflow «Rayos» cada
10 minutos (python scripts/infrarrojo.py), que escribe data/infrarrojo.json con las variables del
modelo. Si existen LUGARES y LUGARES_IR (como en scripts/rayos.py), calcula además las variables
desde el aeropuerto y desde cada lugar y las escribe en LUGARES_IR, fuera del repositorio.
"""

import datetime as dt
import io
import json
import math
import os
import re
import sys
from pathlib import Path

import h5py
import numpy as np
import requests

LAT, LON = -2.19, -79.89
AEROPUERTO = (-2.1572, -79.8836)
RADIOS_KM = (15, 30, 60, 100)
FILAS = 60  # filas de 2 km a cada lado de Guayaquil (~120 km)
FRIO_K, MUY_FRIO_K = 235, 210
BUCKET = 'https://noaa-goes19.s3.amazonaws.com/'
SALIDA = Path(__file__).resolve().parent.parent / 'data' / 'infrarrojo.json'
# La página solo usa infrarrojo.json si coincide con la versión con que se entrenó su modelo
# (meta.infrarrojo en assets/mos-coeficientes.js).
VERSION_IR = 'c13-v1'

sesion = requests.Session()
sesion.mount('https://', requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=64))


class ArchivoRemoto(io.RawIOBase):
    """Archivo por HTTP que pide solo los bloques que se leen (cabecera Range), con caché."""
    BLOQUE = 256 * 1024

    def __init__(self, url, pedir):
        self.url, self.pedir, self.pos, self.cache = url, pedir, 0, {}
        self.tam = int(pedir(url, metodo='head').headers['Content-Length'])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, desplazamiento, desde=0):
        self.pos = desplazamiento if desde == 0 else self.pos + desplazamiento if desde == 1 else self.tam + desplazamiento
        return self.pos

    def _bloque(self, i):
        if i not in self.cache:
            ini = i * self.BLOQUE
            fin = min(ini + self.BLOQUE, self.tam) - 1
            self.cache[i] = self.pedir(self.url, headers={'Range': f'bytes={ini}-{fin}'}).content
        return self.cache[i]

    def readinto(self, b):
        n = min(len(b), self.tam - self.pos)
        salida, p = bytearray(), self.pos
        while len(salida) < n:
            i, desplazamiento = divmod(p, self.BLOQUE)
            trozo = self._bloque(i)[desplazamiento: desplazamiento + n - len(salida)]
            salida += trozo
            p += len(trozo)
        b[:n] = salida
        self.pos += n
        return n


def _escalar(v, datos):
    a = v.attrs
    return datos * float(a['scale_factor'][0]) + float(a['add_offset'][0])


_geometria = {}


def geometria(f):
    """Fila y columna de Guayaquil y la latitud y longitud (radianes) de cada píxel del recuadro.
    Se calcula una vez por satélite (fórmulas de la grilla fija de la guía del usuario de GOES-R)."""
    proj = f['goes_imager_projection'].attrs
    clave = (float(proj['longitude_of_projection_origin'][0]), f['CMI'].shape)
    if clave in _geometria:
        return _geometria[clave]
    req, rpol = float(proj['semi_major_axis'][0]), float(proj['semi_minor_axis'][0])
    H = float(proj['perspective_point_height'][0]) + req
    lon0 = math.radians(clave[0])
    x, y = _escalar(f['x'], f['x'][:]), _escalar(f['y'], f['y'][:])

    # Guayaquil → ángulos de escaneo
    lat, lon = math.radians(LAT), math.radians(LON)
    latc = math.atan((rpol ** 2 / req ** 2) * math.tan(lat))
    rc = rpol / math.sqrt(1 - (req ** 2 - rpol ** 2) / req ** 2 * math.cos(latc) ** 2)
    sx, sy, sz = H - rc * math.cos(latc) * math.cos(lon - lon0), -rc * math.cos(latc) * math.sin(lon - lon0), rc * math.sin(latc)
    fila = int(np.argmin(abs(y - math.atan(sz / sx))))
    columna = int(np.argmin(abs(x - math.asin(-sy / math.sqrt(sx ** 2 + sy ** 2 + sz ** 2)))))

    # Píxeles del recuadro → latitud y longitud
    xs, ys = np.meshgrid(x[columna - FILAS: columna + FILAS + 1], y[fila - FILAS: fila + FILAS + 1])
    a = np.sin(xs) ** 2 + np.cos(xs) ** 2 * (np.cos(ys) ** 2 + (req ** 2 / rpol ** 2) * np.sin(ys) ** 2)
    b = -2 * H * np.cos(xs) * np.cos(ys)
    c = H ** 2 - req ** 2
    rs = (-b - np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    px, py, pz = rs * np.cos(xs) * np.cos(ys), -rs * np.sin(xs), rs * np.cos(xs) * np.sin(ys)
    plat = np.arctan((req ** 2 / rpol ** 2) * pz / np.sqrt((H - px) ** 2 + py ** 2))
    plon = lon0 - np.arctan(py / (H - px))
    _geometria[clave] = (fila, columna, plat, plon)
    return _geometria[clave]


def distancias(plat, plon, centro=(LAT, LON)):
    """Distancia (km) de cada píxel al centro."""
    lat, lon = math.radians(centro[0]), math.radians(centro[1])
    h = np.sin((plat - lat) / 2) ** 2 + math.cos(lat) * np.cos(plat) * np.sin((plon - lon) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(h))


def leer_caja(url, pedir):
    """Temperatura (K) del recuadro alrededor de Guayaquil y la latitud y longitud de sus píxeles."""
    with h5py.File(ArchivoRemoto(url, pedir), 'r') as f:
        fila, columna, plat, plon = geometria(f)
        cmi = f['CMI']
        crudo = cmi[fila - FILAS: fila + FILAS + 1, columna - FILAS: columna + FILAS + 1]
        tb = _escalar(cmi, crudo.astype(float))
        tb[crudo == cmi.attrs['_FillValue'][0]] = np.nan
    return tb, plat, plon


def leer(url, pedir, centro=(LAT, LON)):
    """Resumen de una imagen: temperatura del tope de nubes cerca del centro."""
    tb, plat, plon = leer_caja(url, pedir)
    return resumen(tb, distancias(plat, plon, centro))


def resumen(tb, distancia):
    if np.isnan(tb[distancia <= RADIOS_KM[-1]]).mean() > 0.2:
        return None  # imagen incompleta
    r = {'tb_centro': float(np.nanmean(tb[distancia <= 5]))}
    for km in RADIOS_KM:
        dentro = tb[distancia <= km]
        r[f'tbmin_{km}'] = float(np.nanmin(dentro))
        if km >= 30:
            r[f'frio_{km}'] = float(np.nanmean(dentro < FRIO_K))
    r['muy_frio_60'] = float(np.nanmean(tb[distancia <= 60] < MUY_FRIO_K))
    return {k: round(v, 4) for k, v in r.items()}


def variables_modelo(ahora, antes):
    """Variables del modelo a partir del resumen de la última imagen y el de 30 minutos antes,
    igual que variables_infrarrojo de analisis/entrenar.py. None si falta la última imagen."""
    if ahora is None:
        return None
    frio = lambda t: max(270 - t, 0)  # noqa: E731  cuánto más fría que 270 K
    v = {f'ir_frio_{km}': frio(ahora[f'tbmin_{km}']) for km in RADIOS_KM}
    for c in ('frio_30', 'frio_60', 'frio_100', 'muy_frio_60'):
        v[f'ir_{c}_area'] = ahora[c]
    v['ir_centro'] = frio(ahora['tb_centro'])
    for km in (30, 60):
        v[f'ir_crece_{km}'] = None if antes is None else min(max(antes[f'tbmin_{km}'] - ahora[f'tbmin_{km}'], -30), 30)
    return None if None in v.values() else {k: round(x, 4) for k, x in v.items()}


# ---------- en vivo ----------

def _pedir(url, metodo='get', **kwargs):
    r = getattr(sesion, metodo)(url, timeout=60, **kwargs)
    r.raise_for_status()
    return r


def _inicio(clave):
    m = re.search(r'_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})', clave)
    return dt.datetime.strptime(''.join(m.groups()), '%Y%j%H%M%S').replace(tzinfo=dt.timezone.utc)


def imagenes_recientes(ahora):
    """Imágenes del canal 13 de las últimas dos horas: {inicio redondeado a 10 min: clave}."""
    claves = {}
    for h in (ahora - dt.timedelta(hours=1), ahora):
        r = _pedir(BUCKET, params={'list-type': '2', 'prefix': f'ABI-L2-CMIPF/{h:%Y/%j/%H}/'})
        for c in re.findall(r'<Key>([^<]+)</Key>', r.text):
            if 'C13_' in c:
                t = _inicio(c)
                claves[t.replace(minute=t.minute // 10 * 10, second=0)] = c
    return claves


def leer_lugares(texto):
    """«Nombre:latitud,longitud;Nombre:latitud,longitud» → {'Nombre': (latitud, longitud), …}."""
    lugares = {}
    for parte in filter(None, (p.strip() for p in (texto or '').split(';'))):
        nombre, coordenadas = parte.rsplit(':', 1)
        lat, lon = (float(x) for x in coordenadas.split(','))
        lugares[nombre.strip()] = (lat, lon)
    return lugares


def main():
    ahora = dt.datetime.now(dt.timezone.utc)
    claves = imagenes_recientes(ahora)
    if not claves:
        raise SystemExit('No se encontraron imágenes infrarrojas recientes')
    ultima = max(claves)
    previa = claves.get(ultima - dt.timedelta(minutes=30))
    cajas = {t: leer_caja(BUCKET + c, _pedir) for t, c in ((ultima, claves[ultima]), (ultima - dt.timedelta(minutes=30), previa)) if c}
    # Como en el entrenamiento: en la hora T se usa la imagen que empezó a las T − 10 min.
    hasta = (ultima + dt.timedelta(minutes=10) - dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M')

    def para(centro):
        res = {t: resumen(tb, distancias(plat, plon, centro)) for t, (tb, plat, plon) in cajas.items()}
        v = variables_modelo(res.get(ultima), res.get(ultima - dt.timedelta(minutes=30)))
        return None if v is None else {'hasta': hasta, 'version': VERSION_IR, **v}

    modelo = para((LAT, LON))
    resultado = {'generado': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'), 'imagen': hasta, 'modelo': modelo}
    try:
        anterior = json.loads(SALIDA.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        anterior = {}
    # Solo se reescribe con una imagen nueva, para no hacer un commit en cada revisión.
    if (anterior.get('imagen'), anterior.get('modelo')) != (hasta, modelo):
        SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(resultado, ensure_ascii=False))
    if os.environ.get('LUGARES_IR'):
        lugares = {'Aeropuerto': AEROPUERTO, **leer_lugares(os.environ.get('LUGARES'))}
        Path(os.environ['LUGARES_IR']).write_text(json.dumps({n: para(c) for n, c in lugares.items()}), encoding='utf-8')
        print(f'Infrarrojo por lugar: {", ".join(lugares)}')


if __name__ == '__main__':
    sys.exit(main())
