# Promedios móviles de humedad

Lo escribe `analisis/humedad_movil.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres.

| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|---|
| Hora en curso | GFS | 0.0279 | 0.0279 | -0,13 | [-0,58; +0,31] | 3/8 | no |
| Hora en curso | Aeropuerto | 0.0279 | 0.0279 | -0,13 | [-0,74; +0,40] | 3/8 | no |
| Hora en curso | Ambas | 0.0279 | 0.0280 | -0,25 | [-1,08; +0,49] | 2/8 | no |
| Hora con 2 h | GFS | 0.0343 | 0.0342 | +0,06 | [-0,50; +0,66] | 3/8 | no |
| Hora con 2 h | Aeropuerto | 0.0343 | 0.0344 | -0,36 | [-1,12; +0,36] | 4/8 | no |
| Hora con 2 h | Ambas | 0.0343 | 0.0344 | -0,29 | [-1,22; +0,60] | 3/8 | no |
| Hora con 3 h | GFS | 0.0382 | 0.0381 | +0,11 | [-0,56; +0,84] | 5/8 | no |
| Hora con 3 h | Aeropuerto | 0.0382 | 0.0383 | -0,39 | [-1,18; +0,41] | 1/8 | no |
| Hora con 3 h | Ambas | 0.0382 | 0.0382 | -0,21 | [-1,30; +0,87] | 3/8 | no |
| Hora con 4 h | GFS | 0.0416 | 0.0415 | +0,30 | [-0,92; +1,51] | 5/8 | no |
| Hora con 4 h | Aeropuerto | 0.0416 | 0.0417 | -0,14 | [-1,03; +0,74] | 4/8 | no |
| Hora con 4 h | Ambas | 0.0416 | 0.0416 | +0,00 | [-1,44; +1,43] | 4/8 | no |
| Hora con 5 h | GFS | 0.0437 | 0.0437 | +0,02 | [-1,30; +1,17] | 5/8 | no |
| Hora con 5 h | Aeropuerto | 0.0437 | 0.0438 | -0,12 | [-1,30; +1,03] | 3/8 | no |
| Hora con 5 h | Ambas | 0.0437 | 0.0438 | -0,10 | [-1,70; +1,40] | 4/8 | no |
| Hora con 6 h | GFS | 0.0444 | 0.0444 | +0,02 | [-1,26; +1,15] | 5/8 | no |
| Hora con 6 h | Aeropuerto | 0.0444 | 0.0445 | -0,13 | [-1,18; +0,97] | 3/8 | no |
| Hora con 6 h | Ambas | 0.0444 | 0.0444 | +0,04 | [-1,48; +1,46] | 5/8 | no |

## En los inicios de lluvia sin rayos

Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o más llovió.

| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |
|---|---|---|---|---|---|---|
| Hora en curso | GFS | 796 | -0,43 | 7 % → 7 % | 4 % → 4 % | 26 % (133) |
| Hora en curso | Aeropuerto | 796 | -0,38 | 7 % → 6 % | 4 % → 5 % | 30 % (133) |
| Hora en curso | Ambas | 796 | -0,85 | 7 % → 6 % | 4 % → 5 % | 28 % (149) |
| Hora con 2 h | GFS | 1,163 | -0,31 | 9 % → 9 % | 13 % → 14 % | 30 % (520) |
| Hora con 2 h | Aeropuerto | 1,163 | -0,07 | 9 % → 9 % | 13 % → 13 % | 28 % (532) |
| Hora con 2 h | Ambas | 1,163 | -0,47 | 9 % → 9 % | 13 % → 13 % | 28 % (541) |
| Hora con 3 h | GFS | 1,479 | -0,53 | 12 % → 13 % | 19 % → 17 % | 26 % (974) |
| Hora con 3 h | Aeropuerto | 1,479 | -0,45 | 12 % → 12 % | 19 % → 18 % | 28 % (966) |
| Hora con 3 h | Ambas | 1,479 | -0,79 | 12 % → 12 % | 19 % → 17 % | 26 % (957) |
| Hora con 4 h | GFS | 1,807 | -0,43 | 12 % → 13 % | 21 % → 21 % | 27 % (1,430) |
| Hora con 4 h | Aeropuerto | 1,807 | -0,30 | 12 % → 12 % | 21 % → 21 % | 27 % (1,406) |
| Hora con 4 h | Ambas | 1,807 | -0,83 | 12 % → 12 % | 21 % → 21 % | 26 % (1,470) |
| Hora con 5 h | GFS | 2,104 | -1,20 | 16 % → 15 % | 26 % → 26 % | 28 % (1,976) |
| Hora con 5 h | Aeropuerto | 2,104 | -0,39 | 16 % → 15 % | 26 % → 27 % | 30 % (1,892) |
| Hora con 5 h | Ambas | 2,104 | -1,51 | 16 % → 14 % | 26 % → 28 % | 29 % (2,023) |
| Hora con 6 h | GFS | 2,302 | -1,17 | 19 % → 18 % | 33 % → 33 % | 29 % (2,551) |
| Hora con 6 h | Aeropuerto | 2,302 | -0,30 | 19 % → 18 % | 33 % → 32 % | 31 % (2,377) |
| Hora con 6 h | Ambas | 2,302 | -1,28 | 19 % → 18 % | 33 % → 32 % | 30 % (2,497) |
