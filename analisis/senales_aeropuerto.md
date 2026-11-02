# Señales del aeropuerto y nubes tibias, para la lluvia sin rayos

Lo escribe `analisis/senales_aeropuerto.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres.

| Pronóstico | Variante | Brier página | Brier nuevo | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|---|
| Hora en curso | Señales del aeropuerto | 0.0287 | 0.0281 | +1,88 | [-0,45; +4,21] | 6/8 | no |
| Hora en curso | Nubes tibias | 0.0287 | 0.0284 | +1,04 | [-0,05; +2,10] | 6/8 | no |
| Hora en curso | Ambas | 0.0287 | 0.0279 | +2,79 | [+0,32; +5,26] | 6/8 | sí |
| Hora con 2 h | Señales del aeropuerto | 0.0356 | 0.0349 | +1,84 | [-0,54; +4,11] | 5/8 | no |
| Hora con 2 h | Nubes tibias | 0.0356 | 0.0354 | +0,49 | [-0,46; +1,42] | 5/8 | no |
| Hora con 2 h | Ambas | 0.0356 | 0.0348 | +2,18 | [-0,26; +4,62] | 4/8 | no |
| Hora con 3 h | Señales del aeropuerto | 0.0392 | 0.0387 | +1,42 | [-0,79; +3,78] | 5/8 | no |
| Hora con 3 h | Nubes tibias | 0.0392 | 0.0391 | +0,21 | [-0,56; +1,00] | 7/8 | no |
| Hora con 3 h | Ambas | 0.0392 | 0.0387 | +1,42 | [-0,82; +3,68] | 5/8 | no |
| Hora con 4 h | Señales del aeropuerto | 0.0415 | 0.0411 | +0,97 | [-1,14; +2,96] | 5/8 | no |
| Hora con 4 h | Nubes tibias | 0.0415 | 0.0415 | +0,13 | [-0,50; +0,78] | 6/8 | no |
| Hora con 4 h | Ambas | 0.0415 | 0.0411 | +0,95 | [-1,24; +3,09] | 5/8 | no |
| Hora con 5 h | Señales del aeropuerto | 0.0437 | 0.0435 | +0,48 | [-1,33; +2,26] | 4/8 | no |
| Hora con 5 h | Nubes tibias | 0.0437 | 0.0435 | +0,32 | [-0,48; +1,10] | 4/8 | no |
| Hora con 5 h | Ambas | 0.0437 | 0.0434 | +0,72 | [-1,11; +2,64] | 4/8 | no |
| Hora con 6 h | Señales del aeropuerto | 0.0443 | 0.0440 | +0,72 | [-1,03; +2,40] | 4/8 | no |
| Hora con 6 h | Nubes tibias | 0.0443 | 0.0442 | +0,18 | [-0,45; +0,72] | 5/8 | no |
| Hora con 6 h | Ambas | 0.0443 | 0.0439 | +0,84 | [-0,85; +2,49] | 5/8 | no |
| Próximas 6 h | Señales del aeropuerto | 0.0739 | 0.0728 | +1,47 | [-0,19; +3,17] | 4/8 | no |
| Próximas 6 h | Nubes tibias | 0.0739 | 0.0737 | +0,38 | [-0,48; +1,20] | 5/8 | no |
| Próximas 6 h | Ambas | 0.0739 | 0.0727 | +1,73 | [-0,29; +3,70] | 5/8 | no |

## En los inicios de lluvia sin rayos

Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o más llovió.

| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |
|---|---|---|---|---|---|---|
| Hora en curso | Señales del aeropuerto | 796 | +1,80 | 4 % → 5 % | 1 % → 3 % | 22 % (97) |
| Hora en curso | Nubes tibias | 796 | +0,59 | 4 % → 5 % | 1 % → 1 % | 18 % (50) |
| Hora en curso | Ambas | 796 | +2,57 | 4 % → 7 % | 1 % → 4 % | 29 % (121) |
| Hora con 2 h | Señales del aeropuerto | 1,163 | +2,40 | 8 % → 10 % | 9 % → 12 % | 28 % (493) |
| Hora con 2 h | Nubes tibias | 1,163 | +0,00 | 8 % → 8 % | 9 % → 10 % | 29 % (412) |
| Hora con 2 h | Ambas | 1,163 | +2,06 | 8 % → 10 % | 9 % → 12 % | 28 % (506) |
| Hora con 3 h | Señales del aeropuerto | 1,479 | +1,45 | 10 % → 12 % | 15 % → 17 % | 26 % (967) |
| Hora con 3 h | Nubes tibias | 1,479 | -0,26 | 10 % → 10 % | 15 % → 15 % | 25 % (909) |
| Hora con 3 h | Ambas | 1,479 | +0,99 | 10 % → 12 % | 15 % → 19 % | 27 % (1,035) |
| Hora con 4 h | Señales del aeropuerto | 1,801 | +0,97 | 12 % → 14 % | 21 % → 24 % | 29 % (1,478) |
| Hora con 4 h | Nubes tibias | 1,801 | -0,38 | 12 % → 13 % | 21 % → 21 % | 26 % (1,456) |
| Hora con 4 h | Ambas | 1,801 | +0,41 | 12 % → 14 % | 21 % → 23 % | 27 % (1,549) |
| Hora con 5 h | Señales del aeropuerto | 2,097 | +0,50 | 15 % → 17 % | 26 % → 29 % | 30 % (1,970) |
| Hora con 5 h | Nubes tibias | 2,097 | -0,54 | 15 % → 16 % | 26 % → 26 % | 28 % (1,948) |
| Hora con 5 h | Ambas | 2,097 | -0,13 | 15 % → 17 % | 26 % → 29 % | 30 % (2,048) |
| Hora con 6 h | Señales del aeropuerto | 2,291 | +0,53 | 19 % → 20 % | 34 % → 34 % | 32 % (2,423) |
| Hora con 6 h | Nubes tibias | 2,291 | -0,41 | 19 % → 19 % | 34 % → 33 % | 30 % (2,485) |
| Hora con 6 h | Ambas | 2,291 | +0,17 | 19 % → 20 % | 34 % → 34 % | 32 % (2,445) |
| Próximas 6 h | Señales del aeropuerto | 869 | +1,55 | 19 % → 20 % | 25 % → 31 % | 48 % (570) |
| Próximas 6 h | Nubes tibias | 869 | +0,01 | 19 % → 19 % | 25 % → 26 % | 44 % (512) |
| Próximas 6 h | Ambas | 869 | +1,48 | 19 % → 20 % | 25 % → 32 % | 46 % (599) |
