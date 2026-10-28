# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-26.

## ¿Llueve en esta hora?

Horas de prueba: 15,342. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.78 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.144 | -152 % | 0.87 |
| MOS: regresión logística | 0.048 | +16 % | 0.92 |
| MOS: gradient boosting | 0.051 | +11 % | 0.89 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.032 | +44 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.031 | +46 % | 0.95 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,274 | 2 % | 1 % |
| 10–20 % | 734 | 14 % | 11 % |
| 20–30 % | 217 | 24 % | 22 % |
| 30–40 % | 91 | 35 % | 34 % |
| 40–50 % | 98 | 45 % | 42 % |
| 50–60 % | 86 | 56 % | 52 % |
| 60–70 % | 121 | 65 % | 52 % |
| 70–80 % | 193 | 76 % | 64 % |
| 80–90 % | 263 | 85 % | 81 % |
| 90–100 % | 265 | 95 % | 91 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 52 % | 43 % |
| 60 % | 5 | 57 % | 27 % |
| 70 % | 3 | 70 % | 15 % |
| 80 % | 1 | 81 % | 3 % |
| 90 % | 0 | nan % | 0 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 66 % |
| 60 % | 11 | 75 % | 62 % |
| 70 % | 9 | 77 % | 56 % |
| 80 % | 7 | 82 % | 43 % |
| 90 % | 3 | 86 % | 13 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 66 % |
| 60 % | 11 | 76 % | 62 % |
| 70 % | 9 | 80 % | 55 % |
| 80 % | 7 | 86 % | 44 % |
| 90 % | 5 | 91 % | 23 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,506 | 15 % | -129 %; 0.78 | +46 %; 0.92 |
| Temporada seca (may–dic) | 9,836 | 2 % | -217 %; 0.88 | +48 %; 0.95 |
| Último mes (2026-10) | 613 | 13 % | -84 %; 0.85 | +61 %; 0.94 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,850. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.211 | -89 % | 0.85 |
| MOS: regresión logística | 0.086 | +23 % | 0.90 |
| MOS: gradient boosting | 0.095 | +15 % | 0.86 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.077 | +31 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.076 | +32 % | 0.91 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 8,968 | 4 % | 2 % |
| 10–20 % | 1,865 | 14 % | 13 % |
| 20–30 % | 966 | 25 % | 20 % |
| 30–40 % | 648 | 35 % | 27 % |
| 40–50 % | 492 | 45 % | 42 % |
| 50–60 % | 402 | 55 % | 48 % |
| 60–70 % | 326 | 65 % | 49 % |
| 70–80 % | 290 | 75 % | 66 % |
| 80–90 % | 345 | 85 % | 80 % |
| 90–100 % | 548 | 96 % | 91 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 8 | 62 % | 57 % |
| 60 % | 7 | 66 % | 44 % |
| 70 % | 5 | 74 % | 34 % |
| 80 % | 4 | 82 % | 19 % |
| 90 % | 1 | 100 % | 2 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 13 | 68 % | 58 % |
| 60 % | 12 | 74 % | 49 % |
| 70 % | 11 | 80 % | 40 % |
| 80 % | 10 | 87 % | 29 % |
| 90 % | 6 | 92 % | 19 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 15 | 69 % | 58 % |
| 60 % | 14 | 75 % | 49 % |
| 70 % | 13 | 82 % | 42 % |
| 80 % | 10 | 87 % | 34 % |
| 90 % | 7 | 91 % | 22 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,326 | 32 % | -65 %; 0.74 | +28 %; 0.85 |
| Temporada seca (may–dic) | 9,524 | 6 % | -134 %; 0.86 | +39 %; 0.91 |
| Último mes (2026-10) | 600 | 29 % | -31 %; 0.77 | +53 %; 0.87 |
