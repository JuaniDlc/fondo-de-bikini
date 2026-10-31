# Más datos de satélite: qué se probó

Prueba con el modelo de la página (hora en curso con rayos e infrarrojo, todos los minutos de la hora, y el de 6 horas). Brier: error de la probabilidad (menor es mejor). Verdad: lluvia en el aeropuerto.

## Lluvia estimada por GOES (RRQPE), 2023-2026

`analisis/datos/satelite-lluvia/` (de `satelite_lluvia_historial.py`).

- Comparada con el aeropuerto por hora: cuando el satélite dice que llueve justo encima, llovió el 59 % de las veces, y solo ve el 30 % de las horas con lluvia (el 51 % si se mira a menos de 10 km). Se pierde casi toda la llovizna.
- Como variable del modelo (lluvia en el punto y a 5 y 10 km, últimos 20 y 60 minutos): no mejora nada, con o sin el reporte del aeropuerto (hora en curso: 0,0294 → 0,0295). Se calcula con el mismo infrarrojo que el modelo ya usa.

**No se usa.**

## Movimiento de las nubes, vapor de agua e inestabilidad (GOES), 2023-2026

`analisis/datos/nubes/` (de `nubes_historial.py`, workflow «Historial de nubes»).

Entrenado con 2023-2024, evaluado desde 2025 (entre paréntesis, horas con rayos a menos de 60 km):

| Anticipación | Actual | + vapor de agua | + movimiento | + inestabilidad |
|---|---|---|---|---|
| Hora en curso | 0,0294 (0,103) | 0,0290 (0,102) | 0,0297 (0,104) | 0,0293 (0,102) |
| 2 h | 0,0369 (0,142) | 0,0362 (0,138) | 0,0374 (0,143) | 0,0369 (0,141) |
| 3 h | 0,0408 (0,156) | 0,0401 (0,151) | 0,0413 (0,157) | 0,0407 (0,155) |
| 4 h | 0,0431 (0,157) | 0,0424 (0,153) | 0,0434 (0,158) | 0,0431 (0,158) |
| 6 h | 0,0459 (0,155) | 0,0456 (0,154) | 0,0459 (0,155) | 0,0460 (0,155) |
| Próximas 6 h (avisos) | 0,0749 | 0,0740 | 0,0743 | 0,0743 |

Reentrenando cada trimestre con todo lo anterior (2025-2026), el vapor de agua mejora entre 0,6 y 1,3 %: hora en curso +1,0 % (mejora en 4 de 8 trimestres), 2 h +1,3 % (5 de 8), 4 h +0,6 % (6 de 8), próximas 6 h +1,3 % (7 de 8). Sumarle el movimiento y la inestabilidad lo empeora (+0,5 %).

- **Vapor de agua** (canales 8 y 10, temperatura media a menos de 60 km): mejora poco pero de forma constante, más a 2-4 horas. Es lo único que vale la pena agregar, y **se usa**: `scripts/infrarrojo.py` lo lee con el infrarrojo y entra en los modelos `hora_con_vapor_1` … `_4` y `6h_con_vapor` (si falta, la página usa los modelos sin vapor).
- **Movimiento** (correlación de todo el recuadro de 240 km entre imágenes separadas 30 min): empeora. Mide hacia dónde se mueve la masa de nubes grande, no cada tormenta. Para seguir cada celda habría que identificarlas y rastrearlas una por una.
- **Inestabilidad** (CAPE, LI, índice K y agua precipitable de GOES): casi no cambia nada. Solo existe con cielo despejado (14 % de las imágenes) y los modelos del clima ya traen la energía para tormentas.

## IMERG (NASA)

`analisis/datos/imerg/` (de `imerg_historial.py`, versión final, enero a abril de 2025). Desde GitHub Actions casi nunca se pudo conectar al servidor de la NASA («Network is unreachable»), así que se bajó desde una computadora con OPeNDAP (con 8 descargas a la vez, entre 5 minutos y una hora por mes, según lo cargado que esté el servidor).

Comparada con el aeropuerto por hora (2854 horas, 534 con lluvia; entre paréntesis, contando como acierto si el aeropuerto reporta lluvia una hora antes o después):

| IMERG en el cuadro del aeropuerto | Cuando dice que llueve, llovió | Ve las horas con lluvia | Falsas alarmas en horas secas |
|---|---|---|---|
| ≥ 0,2 mm/h | 45 % (59 %) | 73 % (81 %) | 21 % |
| ≥ 0,5 mm/h | 58 % (72 %) | 65 % (73 %) | 11 % |
| ≥ 1 mm/h | 67 % (81 %) | 55 % (65 %) | 6 % |

Mirando los 3 × 3 cuadros alrededor (unos 33 km) ve más lluvia (82 % con 0,5 mm/h) pero acierta menos (43 %). AUC 0,82 en el cuadro y 0,85 en los 3 × 3. Por día, ve el 89 % de los días con lluvia, pero marca lluvia en el 57 % de los días secos.

Ve la lluvia bastante mejor que la de GOES (RRQPE ve el 30 %), pero hora por hora no coincide con el aeropuerto ni en dos de cada tres casos: es el promedio de un cuadro de 11 km, estimado sobre todo con infrarrojo entre pasadas de los satélites de microondas. Como verdad por lugar metería tanto ruido como el que se quiere corregir, y como variable en vivo no sirve porque la versión más rápida sale unas 4 horas después.

**No se usa como verdad por hora.** Podría servir para comparar cuánto llueve en cada lugar frente al aeropuerto a lo largo de meses (bajándolo con `LUGARES`).
