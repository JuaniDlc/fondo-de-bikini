# Solo viento y temperatura del mar, de 1 a 6 horas

Lo escribe `analisis/viento_mar.py`. Reentrenado cada trimestre desde 2025 solo con lo anterior, sobre las mismas horas y con todos los minutos. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor).

Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres. Es más estricta que en `combinado.py` porque la idea salió de esas mismas horas.

| Pronóstico | Brier página | Brier con viento y mar | Mejora (%) | Intervalo de 99 % | Trimestres | AUC página | AUC nuevo | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Hora en curso | 0.0268 | 0.0266 | +0,72 | [-0,56; +1,86] | 4/8 | 0.960 | 0.960 | no |
| Hora con 2 h | 0.0333 | 0.0329 | +1,18 | [-0,44; +2,73] | 5/8 | 0.944 | 0.944 | no |
| Hora con 3 h | 0.0366 | 0.0361 | +1,38 | [-0,53; +3,25] | 5/8 | 0.936 | 0.936 | no |
| Hora con 4 h | 0.0388 | 0.0381 | +1,75 | [-0,21; +3,79] | 5/8 | 0.932 | 0.932 | no |
| Hora con 5 h | 0.0408 | 0.0400 | +1,83 | [-0,27; +3,87] | 5/8 | 0.926 | 0.926 | no |
| Hora con 6 h | 0.0414 | 0.0406 | +1,98 | [-0,09; +4,03] | 4/8 | 0.925 | 0.925 | no |
| Próximas 6 h | 0.0694 | 0.0705 | -1,70 | [-3,52; +0,15] | 2/8 | 0.919 | 0.920 | no |

## Por temporada

| Pronóstico | Temporada | Predicciones | Mejora (%) | Intervalo de 99 % |
|---|---|---|---|---|
| Hora en curso | Temporada lluviosa | 30,089 | +1,14 | [-0,26; +2,41] |
| Hora en curso | Temporada seca | 59,041 | -0,30 | [-2,58; +1,74] |
| Hora con 2 h | Temporada lluviosa | 30,071 | +1,37 | [-0,43; +3,17] |
| Hora con 2 h | Temporada seca | 59,005 | +0,69 | [-2,35; +3,63] |
| Hora con 3 h | Temporada lluviosa | 30,065 | +1,56 | [-0,55; +3,62] |
| Hora con 3 h | Temporada seca | 58,987 | +0,92 | [-2,95; +4,60] |
| Hora con 4 h | Temporada lluviosa | 30,059 | +2,01 | [-0,39; +4,38] |
| Hora con 4 h | Temporada seca | 58,975 | +1,09 | [-3,28; +4,92] |
| Hora con 5 h | Temporada lluviosa | 30,147 | +2,43 | [+0,06; +5,01] |
| Hora con 5 h | Temporada seca | 59,086 | +0,23 | [-3,27; +3,64] |
| Hora con 6 h | Temporada lluviosa | 30,141 | +2,68 | [+0,29; +5,27] |
| Hora con 6 h | Temporada seca | 59,088 | +0,07 | [-3,48; +3,66] |
| Próximas 6 h | Temporada lluviosa | 4,851 | -2,87 | [-5,24; -0,60] |
| Próximas 6 h | Temporada seca | 9,536 | +0,42 | [-2,72; +2,92] |
