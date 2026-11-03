# Avance de los rayos y llegada de la nube fría

Lo escribe `analisis/movimiento.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero, mejora en al menos 6 de 8 trimestres y mejora también en la franja de rayos a 30-60 km.

| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en la franja (%) | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Hora en curso | Rayos | 0.0278 | 0.0279 | -0,20 | [-0,89; +0,48] | 3/8 | -0,34 | no |
| Hora en curso | Nube fría | 0.0278 | 0.0278 | +0,03 | [-0,62; +0,70] | 4/8 | -0,78 | no |
| Hora en curso | Ambas | 0.0278 | 0.0279 | -0,18 | [-1,07; +0,70] | 2/8 | -1,42 | no |
| Hora con 2 h | Rayos | 0.0343 | 0.0341 | +0,35 | [-0,40; +1,17] | 4/8 | -0,81 | no |
| Hora con 2 h | Nube fría | 0.0343 | 0.0343 | -0,03 | [-1,16; +1,10] | 5/8 | +0,40 | no |
| Hora con 2 h | Ambas | 0.0343 | 0.0342 | +0,04 | [-1,16; +1,25] | 4/8 | -0,35 | no |
| Hora con 3 h | Rayos | 0.0380 | 0.0380 | +0,13 | [-0,78; +1,16] | 5/8 | -1,19 | no |
| Hora con 3 h | Nube fría | 0.0380 | 0.0380 | +0,09 | [-1,12; +1,26] | 5/8 | +0,58 | no |
| Hora con 3 h | Ambas | 0.0380 | 0.0380 | -0,03 | [-1,54; +1,35] | 4/8 | -0,50 | no |
| Hora con 4 h | Rayos | 0.0414 | 0.0413 | +0,21 | [-0,64; +1,09] | 5/8 | -0,56 | no |
| Hora con 4 h | Nube fría | 0.0414 | 0.0415 | -0,33 | [-1,25; +0,62] | 5/8 | +0,38 | no |
| Hora con 4 h | Ambas | 0.0414 | 0.0415 | -0,10 | [-1,31; +1,03] | 5/8 | -0,04 | no |
| Hora con 5 h | Rayos | 0.0435 | 0.0435 | +0,06 | [-0,62; +0,72] | 4/8 | -0,59 | no |
| Hora con 5 h | Nube fría | 0.0435 | 0.0432 | +0,59 | [-0,80; +2,04] | 7/8 | +3,07 | no |
| Hora con 5 h | Ambas | 0.0435 | 0.0432 | +0,61 | [-0,93; +2,20] | 7/8 | +2,43 | no |

## En la franja: horas secas con el rayo más cercano a 30-60 km

Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: predicciones de 30 % o más en que no llovió.

| Pronóstico | Variante | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |
|---|---|---|---|---|---|---|---|
| Hora en curso | Rayos | 4,629 | 260 | 5.6 | 16 % → 16 % | 19 % → 19 % | 83 → 93 |
| Hora en curso | Nube fría | 4,629 | 260 | 5.6 | 16 % → 15 % | 19 % → 20 % | 83 → 89 |
| Hora en curso | Ambas | 4,629 | 260 | 5.6 | 16 % → 15 % | 19 % → 18 % | 83 → 95 |
| Hora con 2 h | Rayos | 4,638 | 261 | 11.5 | 27 % → 27 % | 44 % → 45 % | 363 → 364 |
| Hora con 2 h | Nube fría | 4,638 | 261 | 11.5 | 27 % → 27 % | 44 % → 45 % | 363 → 353 |
| Hora con 2 h | Ambas | 4,638 | 261 | 11.5 | 27 % → 27 % | 44 % → 44 % | 363 → 367 |
| Hora con 3 h | Rayos | 4,624 | 261 | 15.7 | 37 % → 38 % | 61 % → 60 % | 649 → 649 |
| Hora con 3 h | Nube fría | 4,624 | 261 | 15.7 | 37 % → 38 % | 61 % → 61 % | 649 → 601 |
| Hora con 3 h | Ambas | 4,624 | 261 | 15.7 | 37 % → 38 % | 61 % → 61 % | 649 → 618 |
| Hora con 4 h | Rayos | 4,628 | 260 | 18.6 | 44 % → 45 % | 71 % → 69 % | 781 → 796 |
| Hora con 4 h | Nube fría | 4,628 | 260 | 18.6 | 44 % → 44 % | 71 % → 71 % | 781 → 780 |
| Hora con 4 h | Ambas | 4,628 | 260 | 18.6 | 44 % → 44 % | 71 % → 71 % | 781 → 795 |
| Hora con 5 h | Rayos | 4,629 | 265 | 19.7 | 47 % → 46 % | 73 % → 71 % | 764 → 791 |
| Hora con 5 h | Nube fría | 4,629 | 265 | 19.7 | 47 % → 50 % | 73 % → 73 % | 764 → 732 |
| Hora con 5 h | Ambas | 4,629 | 265 | 19.7 | 47 % → 49 % | 73 % → 71 % | 764 → 726 |
