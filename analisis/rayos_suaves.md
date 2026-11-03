# Que los rayos no bajen de más la probabilidad

Lo escribe `analisis/rayos_suaves.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero, mejora en al menos 6 de 8 trimestres y mejora en las horas secas con rayos a menos de 60 km.

| Pronóstico | Versión | Brier antes | Brier con la versión | Mejora (%) | Intervalo de 99 % | Trimestres | Mejora en secas con rayos (%) | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Hora en curso | Rayos solo suman | 0.0279 | 0.0279 | -0,13 | [-0,57; +0,26] | 2/8 | -0,57 | no |
| Hora en curso | Rayos de 20 minutos suavizados | 0.0279 | 0.0279 | +0,00 | [-0,14; +0,14] | 2/8 | +0,06 | no |
| Hora en curso | No baja tanto | 0.0279 | 0.0278 | +0,09 | [-0,24; +0,45] | 5/8 | +0,47 | no |
| Hora con 2 h | Rayos solo suman | 0.0342 | 0.0342 | -0,04 | [-0,40; +0,32] | 4/8 | -0,16 | no |
| Hora con 2 h | Rayos de 20 minutos suavizados | 0.0342 | 0.0342 | +0,05 | [-0,08; +0,16] | 7/8 | +0,13 | no |
| Hora con 2 h | No baja tanto | 0.0342 | 0.0343 | -0,13 | [-0,49; +0,21] | 2/8 | -0,57 | no |
| Hora con 3 h | Rayos solo suman | 0.0381 | 0.0381 | -0,08 | [-0,54; +0,34] | 4/8 | -0,73 | no |
| Hora con 3 h | Rayos de 20 minutos suavizados | 0.0381 | 0.0381 | -0,01 | [-0,15; +0,14] | 5/8 | +0,12 | no |
| Hora con 3 h | No baja tanto | 0.0381 | 0.0382 | -0,23 | [-0,54; +0,07] | 1/8 | -0,99 | no |
| Hora con 4 h | Rayos solo suman | 0.0415 | 0.0415 | +0,19 | [-0,17; +0,55] | 5/8 | +0,15 | no |
| Hora con 4 h | Rayos de 20 minutos suavizados | 0.0415 | 0.0415 | +0,00 | [-0,13; +0,14] | 3/8 | +0,16 | no |
| Hora con 4 h | No baja tanto | 0.0415 | 0.0416 | -0,16 | [-0,41; +0,08] | 1/8 | -0,73 | no |
| Hora con 5 h | Rayos solo suman | 0.0437 | 0.0437 | -0,03 | [-0,28; +0,20] | 4/8 | +0,12 | no |
| Hora con 5 h | Rayos de 20 minutos suavizados | 0.0437 | 0.0437 | -0,02 | [-0,15; +0,09] | 5/8 | -0,00 | no |
| Hora con 5 h | No baja tanto | 0.0437 | 0.0437 | -0,07 | [-0,19; +0,05] | 1/8 | -0,31 | no |

## Horas que caen

Horas secas que marcaban 40 % o más al minuto 0 y bajaron 10 puntos o más al minuto 50 en el modelo de la página. Valores al minuto 50. Son pocas horas: es una pista, no una prueba.

| Pronóstico | Versión | Horas | Marcaba la página | Marca la versión | Llovió |
|---|---|---|---|---|---|
| Hora en curso | Rayos solo suman | 20 | 33 % | 34 % | 45 % |
| Hora en curso | Rayos de 20 minutos suavizados | 20 | 33 % | 32 % | 45 % |
| Hora en curso | No baja tanto | 20 | 33 % | 45 % | 45 % |
| Hora con 2 h | Rayos solo suman | 61 | 33 % | 34 % | 34 % |
| Hora con 2 h | Rayos de 20 minutos suavizados | 61 | 33 % | 33 % | 34 % |
| Hora con 2 h | No baja tanto | 61 | 33 % | 42 % | 34 % |
| Hora con 3 h | Rayos solo suman | 78 | 38 % | 40 % | 29 % |
| Hora con 3 h | Rayos de 20 minutos suavizados | 78 | 38 % | 39 % | 29 % |
| Hora con 3 h | No baja tanto | 78 | 38 % | 46 % | 29 % |
| Hora con 4 h | Rayos solo suman | 75 | 43 % | 44 % | 36 % |
| Hora con 4 h | Rayos de 20 minutos suavizados | 75 | 43 % | 43 % | 36 % |
| Hora con 4 h | No baja tanto | 75 | 43 % | 49 % | 36 % |
| Hora con 5 h | Rayos solo suman | 11 | 46 % | 46 % | 55 % |
| Hora con 5 h | Rayos de 20 minutos suavizados | 11 | 46 % | 47 % | 55 % |
| Hora con 5 h | No baja tanto | 11 | 46 % | 52 % | 55 % |

## En las horas secas con rayos a menos de 60 km

Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Falsas: predicciones de 30 % o más en que no llovió.

| Pronóstico | Versión | Predicciones | Días | Llovió (%) | Probabilidad antes → ahora | Detecta antes → ahora | Falsas antes → ahora |
|---|---|---|---|---|---|---|---|
| Hora en curso | Rayos solo suman | 6,594 | 280 | 11.0 | 23 % → 23 % | 40 % → 41 % | 310 → 303 |
| Hora en curso | Rayos de 20 minutos suavizados | 6,594 | 280 | 11.0 | 23 % → 23 % | 40 % → 41 % | 310 → 315 |
| Hora en curso | No baja tanto | 6,594 | 280 | 11.0 | 23 % → 26 % | 40 % → 45 % | 310 → 365 |
| Hora con 2 h | Rayos solo suman | 6,597 | 280 | 18.2 | 37 % → 37 % | 60 % → 59 % | 683 → 686 |
| Hora con 2 h | Rayos de 20 minutos suavizados | 6,597 | 280 | 18.2 | 37 % → 37 % | 60 % → 60 % | 683 → 680 |
| Hora con 2 h | No baja tanto | 6,597 | 280 | 18.2 | 37 % → 40 % | 60 % → 61 % | 683 → 813 |
| Hora con 3 h | Rayos solo suman | 6,586 | 281 | 20.9 | 45 % → 45 % | 71 % → 71 % | 1,035 → 1,056 |
| Hora con 3 h | Rayos de 20 minutos suavizados | 6,586 | 281 | 20.9 | 45 % → 45 % | 71 % → 70 % | 1,035 → 1,039 |
| Hora con 3 h | No baja tanto | 6,586 | 281 | 20.9 | 45 % → 47 % | 71 % → 73 % | 1,035 → 1,151 |
| Hora con 4 h | Rayos solo suman | 6,590 | 283 | 22.0 | 50 % → 50 % | 76 % → 77 % | 1,213 → 1,224 |
| Hora con 4 h | Rayos de 20 minutos suavizados | 6,590 | 283 | 22.0 | 50 % → 50 % | 76 % → 76 % | 1,213 → 1,215 |
| Hora con 4 h | No baja tanto | 6,590 | 283 | 22.0 | 50 % → 52 % | 76 % → 78 % | 1,213 → 1,304 |
| Hora con 5 h | Rayos solo suman | 6,588 | 291 | 22.8 | 51 % → 51 % | 78 % → 77 % | 1,185 → 1,174 |
| Hora con 5 h | Rayos de 20 minutos suavizados | 6,588 | 291 | 22.8 | 51 % → 51 % | 78 % → 77 % | 1,185 → 1,200 |
| Hora con 5 h | No baja tanto | 6,588 | 291 | 22.8 | 51 % → 53 % | 78 % → 78 % | 1,185 → 1,216 |
