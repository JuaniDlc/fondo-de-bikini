# Dirección de la tormenta

Lo escribe `analisis/direccion.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero, mejora en al menos 6 de 8 trimestres y mejora también en la franja de rayos a 30-60 km.

| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en la franja (%) | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Hora en curso | Posición y sectores | 0.0279 | 0.0279 | -0,22 | [-0,86; +0,36] | 3/8 | -1,00 | no |
| Hora en curso | Movimiento | 0.0279 | 0.0280 | -0,38 | [-0,98; +0,18] | 2/8 | -1,05 | no |
| Hora en curso | Todo | 0.0279 | 0.0280 | -0,52 | [-1,44; +0,27] | 3/8 | -1,94 | no |
| Hora con 2 h | Posición y sectores | 0.0342 | 0.0343 | -0,19 | [-1,01; +0,65] | 5/8 | +0,11 | no |
| Hora con 2 h | Movimiento | 0.0342 | 0.0344 | -0,51 | [-0,99; -0,01] | 1/8 | -0,56 | no |
| Hora con 2 h | Todo | 0.0342 | 0.0345 | -0,71 | [-1,69; +0,25] | 3/8 | -0,82 | no |
| Hora con 3 h | Posición y sectores | 0.0381 | 0.0383 | -0,50 | [-1,44; +0,50] | 2/8 | -2,42 | no |
| Hora con 3 h | Movimiento | 0.0381 | 0.0383 | -0,54 | [-1,04; -0,08] | 2/8 | -0,50 | no |
| Hora con 3 h | Todo | 0.0381 | 0.0385 | -0,97 | [-2,03; +0,14] | 3/8 | -3,29 | no |
| Hora con 4 h | Posición y sectores | 0.0415 | 0.0418 | -0,54 | [-1,67; +0,61] | 2/8 | -3,18 | no |
| Hora con 4 h | Movimiento | 0.0415 | 0.0416 | -0,06 | [-0,62; +0,49] | 4/8 | +0,54 | no |
| Hora con 4 h | Todo | 0.0415 | 0.0417 | -0,49 | [-1,69; +0,74] | 3/8 | -2,89 | no |
| Hora con 5 h | Posición y sectores | 0.0436 | 0.0438 | -0,44 | [-1,68; +0,94] | 5/8 | -2,64 | no |
| Hora con 5 h | Movimiento | 0.0436 | 0.0435 | +0,20 | [-0,32; +0,73] | 7/8 | +0,25 | no |
| Hora con 5 h | Todo | 0.0436 | 0.0437 | -0,28 | [-1,70; +1,28] | 6/8 | -2,50 | no |

## En la franja: horas secas con el rayo más cercano a 30-60 km

Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: predicciones de 30 % o más en que no llovió.

| Pronóstico | Variante | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |
|---|---|---|---|---|---|---|---|
| Hora en curso | Posición y sectores | 4,636 | 260 | 5.6 | 16 % → 16 % | 19 % → 24 % | 81 → 97 |
| Hora en curso | Movimiento | 4,636 | 260 | 5.6 | 16 % → 15 % | 19 % → 20 % | 81 → 93 |
| Hora en curso | Todo | 4,636 | 260 | 5.6 | 16 % → 16 % | 19 % → 24 % | 81 → 110 |
| Hora con 2 h | Posición y sectores | 4,645 | 261 | 11.5 | 27 % → 27 % | 44 % → 46 % | 362 → 376 |
| Hora con 2 h | Movimiento | 4,645 | 261 | 11.5 | 27 % → 27 % | 44 % → 43 % | 362 → 360 |
| Hora con 2 h | Todo | 4,645 | 261 | 11.5 | 27 % → 28 % | 44 % → 46 % | 362 → 394 |
| Hora con 3 h | Posición y sectores | 4,631 | 261 | 15.7 | 38 % → 38 % | 61 % → 60 % | 650 → 662 |
| Hora con 3 h | Movimiento | 4,631 | 261 | 15.7 | 38 % → 37 % | 61 % → 60 % | 650 → 659 |
| Hora con 3 h | Todo | 4,631 | 261 | 15.7 | 38 % → 36 % | 61 % → 59 % | 650 → 667 |
| Hora con 4 h | Posición y sectores | 4,635 | 260 | 18.6 | 44 % → 42 % | 71 % → 68 % | 791 → 784 |
| Hora con 4 h | Movimiento | 4,635 | 260 | 18.6 | 44 % → 43 % | 71 % → 69 % | 791 → 776 |
| Hora con 4 h | Todo | 4,635 | 260 | 18.6 | 44 % → 42 % | 71 % → 67 % | 791 → 778 |
| Hora con 5 h | Posición y sectores | 4,637 | 265 | 19.7 | 46 % → 44 % | 73 % → 70 % | 770 → 789 |
| Hora con 5 h | Movimiento | 4,637 | 265 | 19.7 | 46 % → 47 % | 73 % → 72 % | 770 → 752 |
| Hora con 5 h | Todo | 4,637 | 265 | 19.7 | 46 % → 45 % | 73 % → 69 % | 770 → 761 |
