# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-24.

## ¿Llueve en esta hora?

Horas de prueba: 15,663. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.161 | -189 % | 0.81 |
| Climatología (mes y hora) | 0.056 | +0 % | 0.78 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.143 | -157 % | 0.87 |
| MOS: regresión logística | 0.048 | +13 % | 0.89 |
| MOS: gradient boosting | 0.052 | +7 % | 0.87 |

**Calibración de «MOS: regresión logística»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 12,397 | 2 % | 2 % |
| 10–20 % | 1,367 | 14 % | 12 % |
| 20–30 % | 594 | 24 % | 18 % |
| 30–40 % | 361 | 35 % | 30 % |
| 40–50 % | 291 | 45 % | 40 % |
| 50–60 % | 253 | 55 % | 43 % |
| 60–70 % | 181 | 65 % | 50 % |
| 70–80 % | 121 | 75 % | 53 % |
| 80–90 % | 79 | 84 % | 67 % |
| 90–100 % | 19 | 92 % | 84 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 6 | 51 % | 32 % |
| 60 % | 4 | 56 % | 21 % |
| 70 % | 2 | 61 % | 13 % |
| 80 % | 1 | 70 % | 7 % |
| 90 % | 1 | 84 % | 2 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | MOS logística |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,619 | 15 % | -131 %; 0.77 | +11 %; 0.82 |
| Temporada seca (may–dic) | 10,044 | 2 % | -241 %; 0.87 | +19 %; 0.87 |
| Último mes (2026-10) | 573 | 10 % | -133 %; 0.84 | +33 %; 0.89 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,861. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.110 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.211 | -93 % | 0.85 |
| MOS: regresión logística | 0.085 | +22 % | 0.90 |
| MOS: gradient boosting | 0.094 | +14 % | 0.86 |
| MOS logística + lluvia actual (METAR) | 0.077 | +30 % | 0.91 |

**Calibración de «MOS: regresión logística»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 8,421 | 4 % | 2 % |
| 10–20 % | 1,894 | 15 % | 11 % |
| 20–30 % | 1,030 | 25 % | 18 % |
| 30–40 % | 838 | 35 % | 27 % |
| 40–50 % | 606 | 45 % | 34 % |
| 50–60 % | 564 | 55 % | 51 % |
| 60–70 % | 485 | 65 % | 50 % |
| 70–80 % | 507 | 75 % | 65 % |
| 80–90 % | 469 | 85 % | 79 % |
| 90–100 % | 47 | 91 % | 100 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 8 | 62 % | 57 % |
| 60 % | 7 | 66 % | 44 % |
| 70 % | 5 | 73 % | 33 % |
| 80 % | 3 | 81 % | 19 % |
| 90 % | 1 | 100 % | 2 % |

**Si se usara como alerta** («MOS logística + lluvia actual (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 13 | 68 % | 58 % |
| 60 % | 12 | 74 % | 49 % |
| 70 % | 11 | 79 % | 39 % |
| 80 % | 9 | 87 % | 29 % |
| 90 % | 6 | 91 % | 19 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | MOS logística |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,331 | 32 % | -65 %; 0.74 | +18 %; 0.81 |
| Temporada seca (may–dic) | 9,530 | 6 % | -145 %; 0.85 | +30 %; 0.89 |
| Último mes (2026-10) | 552 | 25 % | -56 %; 0.76 | +42 %; 0.83 |
