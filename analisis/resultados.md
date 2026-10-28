# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-25.

## ¿Llueve en esta hora?

Horas de prueba: 15,380. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.159 | -185 % | 0.81 |
| Climatología (mes y hora) | 0.056 | +0 % | 0.78 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.143 | -156 % | 0.87 |
| MOS: regresión logística | 0.048 | +14 % | 0.89 |
| MOS: gradient boosting | 0.052 | +7 % | 0.87 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.032 | +43 % | 0.94 |

**Calibración de «MOS logística + lluvia en el aeropuerto (METAR)»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,587 | 2 % | 2 % |
| 10–20 % | 545 | 14 % | 11 % |
| 20–30 % | 188 | 24 % | 23 % |
| 30–40 % | 88 | 35 % | 43 % |
| 40–50 % | 96 | 45 % | 41 % |
| 50–60 % | 96 | 55 % | 50 % |
| 60–70 % | 157 | 65 % | 62 % |
| 70–80 % | 165 | 75 % | 70 % |
| 80–90 % | 279 | 86 % | 82 % |
| 90–100 % | 179 | 93 % | 85 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 6 | 51 % | 32 % |
| 60 % | 4 | 57 % | 22 % |
| 70 % | 2 | 62 % | 12 % |
| 80 % | 1 | 72 % | 6 % |
| 90 % | 0 | 88 % | 1 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 73 % | 63 % |
| 60 % | 10 | 76 % | 58 % |
| 70 % | 8 | 80 % | 48 % |
| 80 % | 5 | 83 % | 37 % |
| 90 % | 3 | 85 % | 15 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | MOS con METAR |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,511 | 15 % | -129 %; 0.78 | +43 %; 0.91 |
| Temporada seca (may–dic) | 9,869 | 2 % | -235 %; 0.88 | +42 %; 0.92 |
| Último mes (2026-10) | 591 | 11 % | -119 %; 0.84 | +54 %; 0.93 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,885. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.110 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.211 | -92 % | 0.85 |
| MOS: regresión logística | 0.086 | +22 % | 0.90 |
| MOS: gradient boosting | 0.094 | +15 % | 0.86 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.077 | +30 % | 0.91 |

**Calibración de «MOS logística + lluvia en el aeropuerto (METAR)»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 8,949 | 3 % | 2 % |
| 10–20 % | 1,872 | 14 % | 12 % |
| 20–30 % | 968 | 25 % | 19 % |
| 30–40 % | 668 | 35 % | 27 % |
| 40–50 % | 506 | 45 % | 39 % |
| 50–60 % | 427 | 55 % | 46 % |
| 60–70 % | 373 | 65 % | 57 % |
| 70–80 % | 360 | 75 % | 64 % |
| 80–90 % | 293 | 85 % | 80 % |
| 90–100 % | 469 | 95 % | 91 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 8 | 62 % | 57 % |
| 60 % | 7 | 66 % | 44 % |
| 70 % | 5 | 73 % | 33 % |
| 80 % | 3 | 81 % | 19 % |
| 90 % | 1 | 100 % | 2 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 13 | 68 % | 58 % |
| 60 % | 12 | 74 % | 49 % |
| 70 % | 11 | 80 % | 40 % |
| 80 % | 9 | 87 % | 29 % |
| 90 % | 6 | 91 % | 19 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | MOS con METAR |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,331 | 32 % | -65 %; 0.74 | +27 %; 0.85 |
| Temporada seca (may–dic) | 9,554 | 6 % | -142 %; 0.86 | +37 %; 0.90 |
| Último mes (2026-10) | 576 | 26 % | -50 %; 0.76 | +49 %; 0.85 |

## ¿Llueve antes de cierta hora? (acumulada)

Probabilidad de que llueva al menos una vez desde ahora hasta k horas después. Es la que muestra la página en la tabla hora por hora.

| Hasta | Llovió | Climatología (Brier) | MOS (Brier; mejora; AUC) | MOS + aeropuerto (Brier; mejora; AUC) |
|---|---|---|---|---|
| 1 h | 7 % | 0.056 | 0.049; +13 %; 0.90 | 0.032; +43 %; 0.94 |
| 2 h | 9 % | 0.071 | 0.059; +16 %; 0.90 | 0.045; +36 %; 0.93 |
| 3 h | 11 % | 0.082 | 0.067; +18 %; 0.90 | 0.055; +33 %; 0.92 |
| 4 h | 12 % | 0.093 | 0.074; +20 %; 0.90 | 0.063; +32 %; 0.92 |
| 5 h | 14 % | 0.102 | 0.080; +22 %; 0.90 | 0.070; +31 %; 0.91 |
| 6 h | 15 % | 0.110 | 0.086; +22 %; 0.90 | 0.077; +30 %; 0.91 |
