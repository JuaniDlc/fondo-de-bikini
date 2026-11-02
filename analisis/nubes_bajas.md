# Nubes bajas de GOES, para la lluvia sin rayos

Lo escribe `analisis/nubes_bajas.py`. Mejora: cuánto baja el Brier (positivo es mejor). «Lo que agregan las nubes bajas» compara con las señales del aeropuerto y las nubes tibias; las otras dos, con el modelo de la página. Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres.

| Pronóstico | Variante | Brier antes | Brier con la variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|---|
| Hora en curso | Nubes bajas | 0.0287 | 0.0282 | +1,76 | [-0,28; +3,69] | 7/8 | no |
| Hora en curso | Señales, tibias y nubes bajas | 0.0287 | 0.0277 | +3,53 | [+0,60; +6,26] | 5/8 | no |
| Hora en curso | Lo que agregan las nubes bajas | 0.0279 | 0.0277 | +0,68 | [-1,06; +2,26] | 7/8 | no |
| Hora con 2 h | Nubes bajas | 0.0356 | 0.0348 | +2,12 | [+0,23; +4,01] | 8/8 | sí |
| Hora con 2 h | Señales, tibias y nubes bajas | 0.0356 | 0.0342 | +3,76 | [+0,84; +6,62] | 7/8 | sí |
| Hora con 2 h | Lo que agregan las nubes bajas | 0.0348 | 0.0342 | +1,63 | [+0,06; +3,14] | 8/8 | sí |
| Hora con 3 h | Nubes bajas | 0.0392 | 0.0386 | +1,58 | [+0,03; +3,15] | 8/8 | sí |
| Hora con 3 h | Señales, tibias y nubes bajas | 0.0392 | 0.0381 | +2,82 | [+0,25; +5,54] | 7/8 | sí |
| Hora con 3 h | Lo que agregan las nubes bajas | 0.0386 | 0.0381 | +1,34 | [-0,02; +2,64] | 8/8 | no |
| Hora con 4 h | Nubes bajas | 0.0415 | 0.0411 | +1,06 | [-0,24; +2,31] | 7/8 | no |
| Hora con 4 h | Señales, tibias y nubes bajas | 0.0415 | 0.0408 | +1,78 | [-0,68; +4,22] | 6/8 | no |
| Hora con 4 h | Lo que agregan las nubes bajas | 0.0411 | 0.0408 | +0,80 | [-0,25; +1,84] | 7/8 | no |
| Hora con 5 h | Nubes bajas | 0.0437 | 0.0432 | +1,09 | [-0,06; +2,27] | 7/8 | no |
| Hora con 5 h | Señales, tibias y nubes bajas | 0.0437 | 0.0430 | +1,44 | [-0,69; +3,56] | 5/8 | no |
| Hora con 5 h | Lo que agregan las nubes bajas | 0.0433 | 0.0430 | +0,70 | [-0,38; +1,71] | 6/8 | no |
| Hora con 6 h | Nubes bajas | 0.0443 | 0.0440 | +0,65 | [-0,26; +1,62] | 7/8 | no |
| Hora con 6 h | Señales, tibias y nubes bajas | 0.0443 | 0.0438 | +1,08 | [-0,94; +3,03] | 6/8 | no |
| Hora con 6 h | Lo que agregan las nubes bajas | 0.0439 | 0.0438 | +0,21 | [-0,69; +1,06] | 6/8 | no |
| Próximas 6 h | Nubes bajas | 0.0739 | 0.0732 | +0,88 | [-0,22; +1,98] | 5/8 | no |
| Próximas 6 h | Señales, tibias y nubes bajas | 0.0739 | 0.0723 | +2,16 | [-0,12; +4,37] | 3/8 | no |
| Próximas 6 h | Lo que agregan las nubes bajas | 0.0726 | 0.0723 | +0,43 | [-0,44; +1,32] | 4/8 | no |

## En los inicios de lluvia sin rayos

Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o más llovió.

| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |
|---|---|---|---|---|---|---|
| Hora en curso | Nubes bajas | 796 | +2,43 | 4 % → 5 % | 1 % → 2 % | 19 % (73) |
| Hora en curso | Señales, tibias y nubes bajas | 796 | +3,57 | 4 % → 7 % | 1 % → 5 % | 28 % (132) |
| Hora en curso | Lo que agregan las nubes bajas | 796 | +1,04 | 7 % → 7 % | 4 % → 5 % | 28 % (132) |
| Hora con 2 h | Nubes bajas | 1,163 | +2,24 | 8 % → 7 % | 9 % → 12 % | 33 % (417) |
| Hora con 2 h | Señales, tibias y nubes bajas | 1,163 | +3,04 | 8 % → 9 % | 9 % → 13 % | 30 % (516) |
| Hora con 2 h | Lo que agregan las nubes bajas | 1,163 | +1,02 | 10 % → 9 % | 12 % → 13 % | 30 % (516) |
| Hora con 3 h | Nubes bajas | 1,479 | +1,83 | 10 % → 9 % | 15 % → 16 % | 28 % (845) |
| Hora con 3 h | Señales, tibias y nubes bajas | 1,479 | +2,38 | 10 % → 12 % | 15 % → 19 % | 28 % (984) |
| Hora con 3 h | Lo que agregan las nubes bajas | 1,479 | +1,32 | 12 % → 12 % | 19 % → 19 % | 28 % (984) |
| Hora con 4 h | Nubes bajas | 1,801 | +1,37 | 12 % → 12 % | 21 % → 21 % | 29 % (1,279) |
| Hora con 4 h | Señales, tibias y nubes bajas | 1,801 | +1,47 | 12 % → 14 % | 21 % → 23 % | 29 % (1,455) |
| Hora con 4 h | Lo que agregan las nubes bajas | 1,801 | +1,09 | 14 % → 14 % | 23 % → 23 % | 29 % (1,455) |
| Hora con 5 h | Nubes bajas | 2,095 | +0,96 | 16 % → 15 % | 27 % → 26 % | 31 % (1,814) |
| Hora con 5 h | Señales, tibias y nubes bajas | 2,095 | +0,52 | 16 % → 17 % | 27 % → 28 % | 30 % (1,966) |
| Hora con 5 h | Lo que agregan las nubes bajas | 2,095 | +0,65 | 17 % → 17 % | 29 % → 28 % | 30 % (1,966) |
| Hora con 6 h | Nubes bajas | 2,286 | +0,83 | 19 % → 19 % | 34 % → 34 % | 33 % (2,340) |
| Hora con 6 h | Señales, tibias y nubes bajas | 2,286 | +0,64 | 19 % → 19 % | 34 % → 35 % | 33 % (2,426) |
| Hora con 6 h | Lo que agregan las nubes bajas | 2,286 | +0,42 | 20 % → 19 % | 34 % → 35 % | 33 % (2,426) |
| Próximas 6 h | Nubes bajas | 868 | +0,69 | 19 % → 19 % | 25 % → 27 % | 45 % (521) |
| Próximas 6 h | Señales, tibias y nubes bajas | 868 | +1,61 | 19 % → 20 % | 25 % → 33 % | 46 % (620) |
| Próximas 6 h | Lo que agregan las nubes bajas | 868 | +0,09 | 20 % → 20 % | 32 % → 33 % | 46 % (620) |
