# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-27.

## ¿Llueve en esta hora?

Horas de prueba: 15,346. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.77 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.145 | -154 % | 0.90 |
| MOS: regresión logística | 0.045 | +21 % | 0.92 |
| MOS: gradient boosting | 0.049 | +14 % | 0.90 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.031 | +45 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.030 | +48 % | 0.96 |
| MOS logística + aeropuerto + rayos + infrarrojo | 0.030 | +48 % | 0.96 |

**Calibración de «MOS logística + aeropuerto + rayos + infrarrojo»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,366 | 2 % | 1 % |
| 10–20 % | 646 | 14 % | 13 % |
| 20–30 % | 225 | 24 % | 20 % |
| 30–40 % | 110 | 34 % | 33 % |
| 40–50 % | 89 | 45 % | 43 % |
| 50–60 % | 97 | 55 % | 48 % |
| 60–70 % | 118 | 65 % | 58 % |
| 70–80 % | 161 | 75 % | 69 % |
| 80–90 % | 221 | 85 % | 81 % |
| 90–100 % | 313 | 95 % | 90 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 55 % | 43 % |
| 60 % | 5 | 64 % | 30 % |
| 70 % | 3 | 71 % | 19 % |
| 80 % | 2 | 83 % | 10 % |
| 90 % | 0 | 100 % | 1 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 65 % |
| 60 % | 11 | 76 % | 62 % |
| 70 % | 9 | 80 % | 55 % |
| 80 % | 7 | 84 % | 43 % |
| 90 % | 3 | 89 % | 16 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 66 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 83 % | 55 % |
| 80 % | 7 | 86 % | 43 % |
| 90 % | 5 | 90 % | 24 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos + infrarrojo»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 66 % |
| 60 % | 10 | 79 % | 61 % |
| 70 % | 9 | 82 % | 55 % |
| 80 % | 7 | 86 % | 44 % |
| 90 % | 5 | 90 % | 27 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,499 | 15 % | -129 %; 0.81 | +48 %; 0.93 |
| Temporada seca (may–dic) | 9,847 | 2 % | -226 %; 0.91 | +49 %; 0.96 |
| Último mes (2026-10) | 636 | 13 % | -94 %; 0.87 | +62 %; 0.92 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,874. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.226 | -102 % | 0.87 |
| MOS: regresión logística | 0.084 | +25 % | 0.90 |
| MOS: gradient boosting | 0.089 | +20 % | 0.88 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.076 | +32 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.074 | +33 % | 0.92 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 9,086 | 3 % | 2 % |
| 10–20 % | 1,624 | 14 % | 11 % |
| 20–30 % | 1,058 | 25 % | 20 % |
| 30–40 % | 713 | 35 % | 27 % |
| 40–50 % | 496 | 45 % | 40 % |
| 50–60 % | 404 | 55 % | 46 % |
| 60–70 % | 316 | 65 % | 51 % |
| 70–80 % | 291 | 75 % | 67 % |
| 80–90 % | 319 | 85 % | 79 % |
| 90–100 % | 567 | 96 % | 94 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 62 % | 57 % |
| 60 % | 9 | 70 % | 46 % |
| 70 % | 7 | 77 % | 34 % |
| 80 % | 4 | 85 % | 21 % |
| 90 % | 2 | 98 % | 7 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 14 | 70 % | 58 % |
| 60 % | 13 | 76 % | 49 % |
| 70 % | 12 | 82 % | 40 % |
| 80 % | 10 | 89 % | 31 % |
| 90 % | 6 | 94 % | 20 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 15 | 70 % | 58 % |
| 60 % | 14 | 77 % | 50 % |
| 70 % | 13 | 83 % | 43 % |
| 80 % | 10 | 89 % | 34 % |
| 90 % | 7 | 94 % | 23 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,326 | 32 % | -74 %; 0.77 | +32 %; 0.86 |
| Temporada seca (may–dic) | 9,548 | 6 % | -153 %; 0.88 | +37 %; 0.91 |
| Último mes (2026-10) | 624 | 28 % | -50 %; 0.76 | +47 %; 0.85 |
