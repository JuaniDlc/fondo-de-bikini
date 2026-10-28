"""Nubes de tormenta cerca de Guayaquil en la imagen infrarroja de GOES-Este (ABI, canal 13).

La imagen es la temperatura del tope de las nubes: cuanto más fría, más alta la nube. Bajo 235 K
(−38 °C) suele ser una nube de tormenta; bajo 210 K, una muy fuerte. Cada imagen (una cada
10 minutos) pesa 25 MB, pero solo se bajan las filas alrededor de Guayaquil (~1,6 MB) pidiendo
partes del archivo por HTTP.

Lo usa analisis/infrarrojo_historial.py para armar el historial.
"""

import io
import math

import h5py
import numpy as np
import requests

LAT, LON = -2.19, -79.89
RADIOS_KM = (15, 30, 60, 100)
FILAS = 60  # filas de 2 km a cada lado de Guayaquil (~120 km)
FRIO_K, MUY_FRIO_K = 235, 210

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
    """Fila y columna de Guayaquil y la distancia (km) de cada píxel del recuadro. Se calcula una
    vez por satélite (fórmulas de la grilla fija de la guía del usuario de GOES-R)."""
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

    # Píxeles del recuadro → latitud y longitud → distancia a Guayaquil
    xs, ys = np.meshgrid(x[columna - FILAS: columna + FILAS + 1], y[fila - FILAS: fila + FILAS + 1])
    a = np.sin(xs) ** 2 + np.cos(xs) ** 2 * (np.cos(ys) ** 2 + (req ** 2 / rpol ** 2) * np.sin(ys) ** 2)
    b = -2 * H * np.cos(xs) * np.cos(ys)
    c = H ** 2 - req ** 2
    rs = (-b - np.sqrt(b ** 2 - 4 * a * c)) / (2 * a)
    px, py, pz = rs * np.cos(xs) * np.cos(ys), -rs * np.sin(xs), rs * np.cos(xs) * np.sin(ys)
    plat = np.arctan((req ** 2 / rpol ** 2) * pz / np.sqrt((H - px) ** 2 + py ** 2))
    plon = lon0 - np.arctan(py / (H - px))
    h = np.sin((plat - lat) / 2) ** 2 + math.cos(lat) * np.cos(plat) * np.sin((plon - lon) / 2) ** 2
    distancia = 2 * 6371 * np.arcsin(np.sqrt(h))
    _geometria[clave] = (fila, columna, distancia)
    return _geometria[clave]


def leer(url, pedir):
    """Resumen de una imagen: temperatura del tope de nubes cerca de Guayaquil."""
    with h5py.File(ArchivoRemoto(url, pedir), 'r') as f:
        fila, columna, distancia = geometria(f)
        cmi = f['CMI']
        crudo = cmi[fila - FILAS: fila + FILAS + 1, columna - FILAS: columna + FILAS + 1]
        tb = _escalar(cmi, crudo.astype(float))
        tb[crudo == cmi.attrs['_FillValue'][0]] = np.nan
    return resumen(tb, distancia)


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
