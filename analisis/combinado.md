# Modelo combinado: presión de vapor, viento y temperatura del mar

Lo escribe `analisis/combinado.py`. Reentrenado cada trimestre desde 2025 solo con lo anterior, sobre las mismas horas. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor); entre corchetes, el intervalo de 95 % remuestreando días; después, trimestres en que mejora.

Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo no incluye el cero y mejora en al menos 6 de 8 trimestres.

## Hora en curso

29,707 predicciones; llovió en el 6 %. Modelo de la página: Brier 0.0270, AUC 0.960.

| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |
|---|---|---|---|---|---|
| Solo presión de vapor | -0,30 | [-0,66; +0,05] | 2/8 | 0.960 | no |
| Solo viento | +0,35 | [-0,31; +0,98] | 4/8 | 0.960 | no |
| Solo temperatura del mar | +0,45 | [-0,11; +1,02] | 5/8 | 0.961 | no |
| Combinado | +0,56 | [-0,37; +1,46] | 4/8 | 0.960 | no |
| Combinado con interacciones | +0,49 | [-0,49; +1,39] | 4/8 | 0.960 | no |
| GB combinado | +1,02 | [-0,86; +2,79] | 6/8 | 0.960 | no |
| GB combinado frente a la página | -0,43 | [-3,20; +2,02] | 3/8 | 0.960 | no |

## Hora con 2 h

29,689 predicciones; llovió en el 6 %. Modelo de la página: Brier 0.0336, AUC 0.943.

| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |
|---|---|---|---|---|---|
| Solo presión de vapor | -0,27 | [-0,63; +0,10] | 2/8 | 0.942 | no |
| Solo viento | +0,62 | [-0,31; +1,52] | 4/8 | 0.942 | no |
| Solo temperatura del mar | +0,74 | [-0,09; +1,62] | 5/8 | 0.943 | no |
| Combinado | +1,08 | [-0,22; +2,34] | 5/8 | 0.943 | no |
| Combinado con interacciones | +0,96 | [-0,43; +2,30] | 5/8 | 0.942 | no |
| GB combinado | +0,19 | [-2,32; +2,61] | 4/8 | 0.941 | no |
| GB combinado frente a la página | -0,78 | [-4,00; +2,44] | 5/8 | 0.941 | no |

## Hora con 3 h

29,681 predicciones; llovió en el 6 %. Modelo de la página: Brier 0.0369, AUC 0.935.

| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |
|---|---|---|---|---|---|
| Solo presión de vapor | -0,24 | [-0,54; +0,07] | 2/8 | 0.935 | no |
| Solo viento | +0,94 | [-0,20; +2,06] | 4/8 | 0.935 | no |
| Solo temperatura del mar | +0,77 | [-0,11; +1,70] | 5/8 | 0.935 | no |
| Combinado | +1,33 | [-0,20; +2,78] | 5/8 | 0.935 | no |
| Combinado con interacciones | +1,12 | [-0,41; +2,64] | 5/8 | 0.934 | no |
| GB combinado | -0,43 | [-3,13; +2,35] | 4/8 | 0.930 | no |
| GB combinado frente a la página | -0,91 | [-3,97; +2,11] | 4/8 | 0.930 | no |

## Hora con 4 h

29,675 predicciones; llovió en el 6 %. Modelo de la página: Brier 0.0390, AUC 0.931.

| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |
|---|---|---|---|---|---|
| Solo presión de vapor | -0,15 | [-0,42; +0,12] | 3/8 | 0.931 | no |
| Solo viento | +1,29 | [+0,02; +2,53] | 5/8 | 0.931 | no |
| Solo temperatura del mar | +0,76 | [-0,14; +1,66] | 5/8 | 0.931 | no |
| Combinado | +1,73 | [+0,16; +3,24] | 5/8 | 0.931 | no |
| Combinado con interacciones | +1,38 | [-0,24; +3,01] | 4/8 | 0.930 | no |
| GB combinado | +0,43 | [-2,63; +3,38] | 6/8 | 0.924 | no |
| GB combinado frente a la página | -0,47 | [-3,85; +3,00] | 5/8 | 0.924 | no |

## Próximas 6 h

14,387 predicciones; llovió en el 14 %. Modelo de la página: Brier 0.0689, AUC 0.921.

| Variante | Mejora (%) | Intervalo | Trimestres | AUC | ¿Cumple? |
|---|---|---|---|---|---|
| Solo presión de vapor | +0,10 | [-0,58; +0,73] | 3/8 | 0.922 | no |
| Solo viento | +0,63 | [-0,75; +2,07] | 5/8 | 0.921 | no |
| Solo temperatura del mar | -0,23 | [-1,57; +1,05] | 5/8 | 0.921 | no |
| Combinado | +0,42 | [-1,58; +2,45] | 4/8 | 0.923 | no |
| Combinado con interacciones | -0,19 | [-2,54; +2,11] | 4/8 | 0.922 | no |
| GB combinado | +2,05 | [-0,74; +4,85] | 4/8 | 0.908 | no |
| GB combinado frente a la página | -1,47 | [-5,35; +2,19] | 2/8 | 0.908 | no |

«GB combinado» se compara con gradient boosting de las variables de la página, para ver si esas variables ayudan de forma no lineal; «frente a la página» lo compara con el modelo que de verdad se usa.

## Dónde cambia el combinado

| Pronóstico | Subgrupo | Predicciones | Mejora (%) | Intervalo |
|---|---|---|---|---|
| Hora en curso | Temporada lluviosa | 10,033 | +0,98 | [-0,05; +1,96] |
| Hora en curso | Temporada seca | 19,674 | -0,45 | [-2,31; +1,21] |
| Hora en curso | Con rayos a menos de 60 km | 3,153 | +0,15 | [-1,36; +1,59] |
| Hora con 2 h | Temporada lluviosa | 10,027 | +1,30 | [-0,14; +2,67] |
| Hora con 2 h | Temporada seca | 19,662 | +0,50 | [-2,07; +2,92] |
| Hora con 2 h | Con rayos a menos de 60 km | 3,150 | +0,71 | [-1,23; +2,66] |
| Hora con 3 h | Temporada lluviosa | 10,025 | +1,60 | [-0,04; +3,19] |
| Hora con 3 h | Temporada seca | 19,656 | +0,62 | [-2,59; +3,82] |
| Hora con 3 h | Con rayos a menos de 60 km | 3,151 | +1,69 | [-0,62; +4,20] |
| Hora con 4 h | Temporada lluviosa | 10,023 | +2,06 | [+0,29; +3,77] |
| Hora con 4 h | Temporada seca | 19,652 | +0,87 | [-2,48; +4,19] |
| Hora con 4 h | Con rayos a menos de 60 km | 3,145 | +2,02 | [-0,59; +4,63] |
| Próximas 6 h | Temporada lluviosa | 4,851 | +0,79 | [-1,52; +3,31] |
| Próximas 6 h | Temporada seca | 9,536 | -0,24 | [-4,21; +3,33] |
| Próximas 6 h | Con rayos a menos de 60 km | 1,490 | +1,38 | [-3,92; +6,57] |
