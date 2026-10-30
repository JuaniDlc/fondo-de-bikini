# Validación mes a mes

Cada mes desde 2025-01 se predice con un modelo entrenado solo con los datos anteriores a ese mes. Verdad: lluvia reportada en el aeropuerto. Brier: error cuadrático de la probabilidad (menor es mejor). Lo escribe `analisis/validacion.py`.

## ¿Llueve en las próximas 6 horas? (avisos)

14,874 predicciones.

| Variante | Brier (menor es mejor) | AUC |
|---|---|---|
| Una vez, con 2023-2024 (antes) | 0.0744 | 0.917 |
| Cada mes, con todo lo anterior | 0.0730 | 0.919 |
| Cada mes, más peso a lo reciente (media vida 1 año) | 0.0725 | 0.920 |
| Ídem, media vida 2 años (la página) | 0.0727 | 0.920 |
| Ídem 2 años + interacciones con la época | 0.0732 | 0.918 |
| Gradient boosting monótono | 0.0759 | 0.908 |

**Recalibración** del modelo con más peso a lo reciente, ajustada cada mes con las predicciones de los meses anteriores (evaluada desde 2025-07):

| Variante | Brier (menor es mejor) | AUC |
|---|---|---|
| Sin recalibrar | 0.0548 | 0.922 |
| Platt | 0.0540 | 0.921 |
| Isotónica | 0.0548 | 0.919 |

| Pronóstico | Sin recalibrar | Platt | Isotónica |
|---|---|---|---|
| 0–10 % | dice 3 %, llovió 2 % | dice 3 %, llovió 2 % | dice 2 %, llovió 2 % |
| 10–20 % | dice 14 %, llovió 11 % | dice 14 %, llovió 11 % | dice 14 %, llovió 11 % |
| 20–30 % | dice 25 %, llovió 16 % | dice 25 %, llovió 19 % | dice 26 %, llovió 17 % |
| 30–40 % | dice 34 %, llovió 25 % | dice 35 %, llovió 29 % | dice 33 %, llovió 25 % |
| 40–50 % | dice 45 %, llovió 34 % | dice 45 %, llovió 40 % | dice 44 %, llovió 34 % |
| 50–60 % | dice 55 %, llovió 48 % | dice 55 %, llovió 47 % | dice 54 %, llovió 51 % |
| 60–70 % | dice 65 %, llovió 52 % | dice 65 %, llovió 61 % | dice 67 %, llovió 76 % |
| 70–80 % | dice 75 %, llovió 72 % | dice 75 %, llovió 80 % | dice 74 %, llovió 81 % |
| 80–90 % | dice 85 %, llovió 82 % | dice 85 %, llovió 85 % | dice 84 %, llovió 85 % |
| 90–100 % | dice 96 %, llovió 96 % | dice 95 %, llovió 96 % | dice 97 %, llovió 98 % |

## ¿Llueve en la hora en curso? (con rayos e infrarrojo, todos los minutos)

92,067 predicciones.

| Variante | Brier (menor es mejor) | AUC |
|---|---|---|
| Una vez, con 2023-2024 (antes) | 0.0292 | 0.958 |
| Cada mes, con todo lo anterior | 0.0288 | 0.959 |
| Cada mes, más peso a lo reciente (media vida 1 año) | 0.0290 | 0.959 |
| Ídem, media vida 2 años (la página) | 0.0289 | 0.959 |
| Ídem 2 años + interacciones con la época | 0.0290 | 0.958 |
| Gradient boosting monótono | 0.0294 | 0.959 |

**Recalibración** del modelo con más peso a lo reciente, ajustada cada mes con las predicciones de los meses anteriores (evaluada desde 2025-07):

| Variante | Brier (menor es mejor) | AUC |
|---|---|---|
| Sin recalibrar | 0.0196 | 0.962 |
| Platt | 0.0197 | 0.961 |
| Isotónica | 0.0197 | 0.960 |

| Pronóstico | Sin recalibrar | Platt | Isotónica |
|---|---|---|---|
| 0–10 % | dice 1 %, llovió 1 % | dice 1 %, llovió 1 % | dice 1 %, llovió 1 % |
| 10–20 % | dice 14 %, llovió 12 % | dice 14 %, llovió 13 % | dice 13 %, llovió 12 % |
| 20–30 % | dice 24 %, llovió 22 % | dice 25 %, llovió 28 % | dice 29 %, llovió 30 % |
| 30–40 % | dice 34 %, llovió 32 % | dice 35 %, llovió 44 % | dice 37 %, llovió 35 % |
| 40–50 % | dice 45 %, llovió 55 % | dice 45 %, llovió 57 % | dice 45 %, llovió 62 % |
| 50–60 % | dice 55 %, llovió 62 % | dice 55 %, llovió 69 % | dice 55 %, llovió 68 % |
| 60–70 % | dice 65 %, llovió 69 % | dice 65 %, llovió 67 % | dice 66 %, llovió 73 % |
| 70–80 % | dice 75 %, llovió 70 % | dice 75 %, llovió 70 % | dice 76 %, llovió 68 % |
| 80–90 % | dice 85 %, llovió 69 % | dice 86 %, llovió 70 % | dice 85 %, llovió 76 % |
| 90–100 % | dice 96 %, llovió 91 % | dice 95 %, llovió 94 % | dice 96 %, llovió 96 % |

## Según el minuto de la hora

La hora en curso con los rayos y el infrarrojo medidos m minutos después del último reporte horario del aeropuerto (el workflow los mide cada 10 minutos). Entrenado con 2023-2024, evaluado desde 2025. «Tormenta»: con rayos a menos de 60 km en la última hora.

| Minuto | Horas de tormenta | Antes: modelo de T − 1 con datos nuevos | Modelo por minuto |
|---|---|---|---|
| 0 | 1,765 | 0.0296 (tormenta 0.1079) | 0.0298 (tormenta 0.1085) |
| 10 | 1,783 | 0.0297 (tormenta 0.1090) | 0.0297 (tormenta 0.1088) |
| 20 | 1,795 | 0.0297 (tormenta 0.1081) | 0.0296 (tormenta 0.1073) |
| 30 | 1,805 | 0.0295 (tormenta 0.1027) | 0.0292 (tormenta 0.0998) |
| 40 | 1,793 | 0.0294 (tormenta 0.1011) | 0.0287 (tormenta 0.0956) |
| 50 | 1,781 | 0.0294 (tormenta 0.1002) | 0.0287 (tormenta 0.0946) |
