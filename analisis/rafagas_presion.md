# Ráfagas y cambios de presión

Lo escribe `analisis/rafagas_presion.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres.

| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|---|
| Hora en curso | Ráfagas | 0.0278 | 0.0279 | -0,08 | [-0,41; +0,19] | 4/8 | no |
| Hora en curso | Presión | 0.0278 | 0.0279 | -0,19 | [-1,87; +0,85] | 6/8 | no |
| Hora en curso | Ambas | 0.0278 | 0.0279 | -0,23 | [-1,89; +0,86] | 5/8 | no |
| Hora con 2 h | Ráfagas | 0.0343 | 0.0343 | -0,08 | [-0,28; +0,10] | 2/8 | no |
| Hora con 2 h | Presión | 0.0343 | 0.0343 | -0,09 | [-0,68; +0,50] | 5/8 | no |
| Hora con 2 h | Ambas | 0.0343 | 0.0344 | -0,25 | [-0,90; +0,34] | 4/8 | no |
| Hora con 3 h | Ráfagas | 0.0381 | 0.0381 | -0,25 | [-0,79; +0,12] | 4/8 | no |
| Hora con 3 h | Presión | 0.0381 | 0.0382 | -0,43 | [-1,13; +0,28] | 4/8 | no |
| Hora con 3 h | Ambas | 0.0381 | 0.0383 | -0,74 | [-1,60; +0,02] | 4/8 | no |
| Hora con 4 h | Ráfagas | 0.0415 | 0.0414 | +0,30 | [-0,43; +0,93] | 6/8 | no |
| Hora con 4 h | Presión | 0.0415 | 0.0417 | -0,59 | [-1,81; +0,53] | 4/8 | no |
| Hora con 4 h | Ambas | 0.0415 | 0.0416 | -0,29 | [-1,67; +1,00] | 4/8 | no |
| Hora con 5 h | Ráfagas | 0.0436 | 0.0435 | +0,23 | [-0,51; +0,94] | 6/8 | no |
| Hora con 5 h | Presión | 0.0436 | 0.0438 | -0,45 | [-1,45; +0,50] | 4/8 | no |
| Hora con 5 h | Ambas | 0.0436 | 0.0437 | -0,26 | [-1,45; +0,91] | 4/8 | no |
| Hora con 6 h | Ráfagas | 0.0443 | 0.0446 | -0,65 | [-2,11; +0,48] | 6/8 | no |
| Hora con 6 h | Presión | 0.0443 | 0.0446 | -0,51 | [-1,65; +0,51] | 4/8 | no |
| Hora con 6 h | Ambas | 0.0443 | 0.0449 | -1,32 | [-3,14; +0,21] | 4/8 | no |

## En los inicios de lluvia sin rayos

Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o más llovió.

| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |
|---|---|---|---|---|---|---|
| Hora en curso | Ráfagas | 790 | -0,16 | 7 % → 7 % | 4 % → 5 % | 29 % (124) |
| Hora en curso | Presión | 790 | -1,62 | 7 % → 7 % | 4 % → 4 % | 25 % (130) |
| Hora en curso | Ambas | 790 | -1,78 | 7 % → 6 % | 4 % → 4 % | 24 % (136) |
| Hora con 2 h | Ráfagas | 1,163 | -0,09 | 9 % → 9 % | 13 % → 13 % | 29 % (523) |
| Hora con 2 h | Presión | 1,163 | -0,05 | 9 % → 9 % | 13 % → 13 % | 30 % (508) |
| Hora con 2 h | Ambas | 1,163 | -0,30 | 9 % → 9 % | 13 % → 13 % | 30 % (524) |
| Hora con 3 h | Ráfagas | 1,467 | -0,15 | 12 % → 12 % | 19 % → 19 % | 29 % (992) |
| Hora con 3 h | Presión | 1,467 | -0,36 | 12 % → 12 % | 19 % → 20 % | 28 % (1,053) |
| Hora con 3 h | Ambas | 1,467 | -0,50 | 12 % → 12 % | 19 % → 20 % | 28 % (1,062) |
| Hora con 4 h | Ráfagas | 1,789 | +0,09 | 12 % → 12 % | 21 % → 22 % | 27 % (1,414) |
| Hora con 4 h | Presión | 1,789 | -0,39 | 12 % → 12 % | 21 % → 21 % | 26 % (1,450) |
| Hora con 4 h | Ambas | 1,789 | -0,33 | 12 % → 13 % | 21 % → 22 % | 27 % (1,434) |
| Hora con 5 h | Ráfagas | 2,080 | -0,19 | 15 % → 16 % | 27 % → 28 % | 30 % (1,884) |
| Hora con 5 h | Presión | 2,080 | -0,59 | 15 % → 15 % | 27 % → 27 % | 30 % (1,894) |
| Hora con 5 h | Ambas | 2,080 | -0,79 | 15 % → 16 % | 27 % → 28 % | 30 % (1,919) |
| Hora con 6 h | Ráfagas | 2,278 | +0,09 | 19 % → 20 % | 34 % → 35 % | 32 % (2,463) |
| Hora con 6 h | Presión | 2,278 | -0,62 | 19 % → 19 % | 34 % → 33 % | 31 % (2,481) |
| Hora con 6 h | Ambas | 2,278 | -0,60 | 19 % → 20 % | 34 % → 34 % | 32 % (2,484) |
