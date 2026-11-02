# Dos modelos: con y sin tormenta eléctrica

Lo escribe `analisis/dos_modelos.py`. Mejora: cuánto baja el Brier (positivo es mejor). «Un modelo con todo» y «Dos por regla, variables de la página» se comparan con la página; las demás, con el modelo con todo. Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99 % no incluye el cero y mejora en al menos 6 de 8 trimestres. Las columnas con y sin tormenta son la misma mejora en esas horas.

| Pronóstico | Variante | Mejora (%) | Intervalo de 99 % | Trimestres | ¿Cumple? | Sin tormenta (%) | Con tormenta (%) |
|---|---|---|---|---|---|---|---|
| Hora en curso | Un modelo con todo | +3,57 | [+0,62; +6,29] | 5/8 | no | +4,34 | +2,44 |
| Hora en curso | Dos por regla, variables de la página | -0,74 | [-2,23; +0,74] | 2/8 | no | -0,30 | -1,38 |
| Hora en curso | Dos por regla, con todo | -1,09 | [-2,97; +0,74] | 2/8 | no | -1,09 | -1,09 |
| Hora en curso | Dos por regla, sin tormenta con variables elegidas | -1,93 | [-4,50; +0,50] | 2/8 | no | -0,55 | -3,92 |
| Hora en curso | Tercer modelo que pesa | -1,12 | [-2,90; +0,56] | 2/8 | no | -0,42 | -2,14 |
| Hora en curso | El porcentaje mayor | -15,62 | [-21,55; -10,73] | 0/8 | no | -13,42 | -18,79 |
| Hora con 2 h | Un modelo con todo | +3,77 | [+0,83; +6,59] | 7/8 | sí | +4,39 | +3,00 |
| Hora con 2 h | Dos por regla, variables de la página | -0,53 | [-2,57; +1,45] | 5/8 | no | +0,11 | -1,32 |
| Hora con 2 h | Dos por regla, con todo | -1,45 | [-3,55; +0,76] | 5/8 | no | -0,89 | -2,14 |
| Hora con 2 h | Dos por regla, sin tormenta con variables elegidas | -3,24 | [-6,28; -0,53] | 1/8 | no | -2,25 | -4,46 |
| Hora con 2 h | Tercer modelo que pesa | -0,61 | [-2,31; +1,05] | 1/8 | no | -0,06 | -1,29 |
| Hora con 2 h | El porcentaje mayor | -33,02 | [-42,89; -25,01] | 0/8 | no | -31,49 | -34,90 |
| Hora con 3 h | Un modelo con todo | +2,91 | [+0,30; +5,68] | 7/8 | sí | +2,49 | +3,45 |
| Hora con 3 h | Dos por regla, variables de la página | -1,00 | [-3,11; +1,07] | 2/8 | no | -0,00 | -2,27 |
| Hora con 3 h | Dos por regla, con todo | -2,92 | [-4,95; -0,81] | 1/8 | no | -1,52 | -4,73 |
| Hora con 3 h | Dos por regla, sin tormenta con variables elegidas | -2,99 | [-6,43; +0,10] | 1/8 | no | -0,72 | -5,92 |
| Hora con 3 h | Tercer modelo que pesa | -1,10 | [-2,80; +0,63] | 2/8 | no | -0,40 | -2,02 |
| Hora con 3 h | El porcentaje mayor | -45,10 | [-55,21; -36,19] | 0/8 | no | -28,72 | -66,30 |
| Hora con 4 h | Un modelo con todo | +1,76 | [-0,72; +4,24] | 6/8 | no | +1,41 | +2,24 |
| Hora con 4 h | Dos por regla, variables de la página | -1,09 | [-3,01; +0,82] | 4/8 | no | +0,27 | -2,98 |
| Hora con 4 h | Dos por regla, con todo | -2,07 | [-4,07; -0,04] | 2/8 | no | -0,82 | -3,81 |
| Hora con 4 h | Dos por regla, sin tormenta con variables elegidas | -2,16 | [-5,44; +0,86] | 4/8 | no | +0,11 | -5,34 |
| Hora con 4 h | Tercer modelo que pesa | -0,83 | [-2,59; +0,80] | 1/8 | no | -0,31 | -1,56 |
| Hora con 4 h | El porcentaje mayor | -48,08 | [-58,63; -38,64] | 0/8 | no | -24,37 | -81,26 |
| Hora con 5 h | Un modelo con todo | +1,46 | [-0,70; +3,53] | 5/8 | no | +0,71 | +2,54 |
| Hora con 5 h | Dos por regla, variables de la página | -1,08 | [-2,89; +0,65] | 3/8 | no | -0,17 | -2,42 |
| Hora con 5 h | Dos por regla, con todo | -1,79 | [-3,76; +0,12] | 1/8 | no | -0,72 | -3,38 |
| Hora con 5 h | Dos por regla, sin tormenta con variables elegidas | -2,53 | [-5,40; +0,42] | 3/8 | no | -0,82 | -5,09 |
| Hora con 5 h | Tercer modelo que pesa | -0,91 | [-2,50; +0,69] | 2/8 | no | +0,16 | -2,51 |
| Hora con 5 h | El porcentaje mayor | -47,63 | [-57,34; -38,76] | 0/8 | no | -24,69 | -81,88 |
| Hora con 6 h | Un modelo con todo | +1,10 | [-0,89; +3,05] | 6/8 | no | +1,01 | +1,25 |
| Hora con 6 h | Dos por regla, variables de la página | -1,04 | [-3,20; +1,07] | 3/8 | no | +0,05 | -2,71 |
| Hora con 6 h | Dos por regla, con todo | -1,70 | [-3,88; +0,51] | 1/8 | no | -0,58 | -3,43 |
| Hora con 6 h | Dos por regla, sin tormenta con variables elegidas | -2,43 | [-5,68; +0,74] | 3/8 | no | -1,40 | -4,01 |
| Hora con 6 h | Tercer modelo que pesa | -1,05 | [-2,52; +0,40] | 2/8 | no | -0,31 | -2,18 |
| Hora con 6 h | El porcentaje mayor | -28,93 | [-36,24; -22,18] | 0/8 | no | -17,60 | -46,48 |
| Próximas 6 h | Un modelo con todo | +2,14 | [-0,12; +4,30] | 5/8 | no | +2,25 | +1,79 |
| Próximas 6 h | Dos por regla, variables de la página | -1,39 | [-3,13; +0,21] | 2/8 | no | +0,62 | -7,80 |
| Próximas 6 h | Dos por regla, con todo | -2,23 | [-4,03; -0,49] | 0/8 | no | +0,53 | -10,97 |
| Próximas 6 h | Dos por regla, sin tormenta con variables elegidas | -1,79 | [-4,10; +0,42] | 2/8 | no | +0,73 | -9,76 |
| Próximas 6 h | Tercer modelo que pesa | -2,19 | [-3,69; -0,83] | 0/8 | no | -0,88 | -6,36 |
| Próximas 6 h | El porcentaje mayor | -65,16 | [-83,74; -49,80] | 1/8 | no | -84,64 | -3,52 |

## Horas con tormenta

| Pronóstico | Predicciones con rayos a menos de 60 km en la hora anterior |
|---|---|
| Hora en curso | 12 % |
| Hora con 2 h | 12 % |
| Hora con 3 h | 12 % |
| Hora con 4 h | 12 % |
| Hora con 5 h | 12 % |
| Hora con 6 h | 12 % |
| Próximas 6 h | 11 % |

## En los inicios de lluvia sin rayos, frente a la página

Horas sin lluvia en las 3 anteriores y sin rayos a menos de 60 km. Probabilidad: mediana en las horas en que sí llovió. Detecta: horas con lluvia en que marcó 30 % o más. Acierto: cuántas de las veces que marcó 30 % o más llovió.

| Pronóstico | Variante | Predicciones con lluvia | Mejora (%) | Probabilidad antes → ahora | Detecta antes → ahora | Acierto (veces) |
|---|---|---|---|---|---|---|
| Hora en curso | Un modelo con todo | 796 | +3,53 | 4 % → 7 % | 1 % → 5 % | 27 % (135) |
| Hora en curso | Dos por regla, variables de la página | 796 | -0,46 | 4 % → 4 % | 1 % → 0 % | 6 % (34) |
| Hora en curso | Dos por regla, con todo | 796 | +2,30 | 4 % → 6 % | 1 % → 3 % | 21 % (121) |
| Hora en curso | Dos por regla, sin tormenta con variables elegidas | 796 | +3,74 | 4 % → 5 % | 1 % → 5 % | 38 % (105) |
| Hora en curso | Tercer modelo que pesa | 796 | +2,94 | 4 % → 6 % | 1 % → 5 % | 27 % (135) |
| Hora en curso | El porcentaje mayor | 796 | -15,21 | 4 % → 11 % | 1 % → 15 % | 14 % (839) |
| Hora con 2 h | Un modelo con todo | 1,159 | +3,01 | 8 % → 9 % | 9 % → 14 % | 30 % (526) |
| Hora con 2 h | Dos por regla, variables de la página | 1,159 | +0,47 | 8 % → 7 % | 9 % → 5 % | 28 % (218) |
| Hora con 2 h | Dos por regla, con todo | 1,159 | +2,88 | 8 % → 8 % | 9 % → 10 % | 29 % (388) |
| Hora con 2 h | Dos por regla, sin tormenta con variables elegidas | 1,159 | +3,38 | 8 % → 8 % | 9 % → 7 % | 30 % (285) |
| Hora con 2 h | Tercer modelo que pesa | 1,159 | +3,01 | 8 % → 9 % | 9 % → 13 % | 31 % (501) |
| Hora con 2 h | El porcentaje mayor | 1,159 | -33,41 | 8 % → 18 % | 9 % → 31 % | 15 % (2,385) |
| Hora con 3 h | Un modelo con todo | 1,473 | +2,50 | 10 % → 12 % | 15 % → 19 % | 28 % (983) |
| Hora con 3 h | Dos por regla, variables de la página | 1,473 | -0,49 | 10 % → 9 % | 15 % → 13 % | 26 % (728) |
| Hora con 3 h | Dos por regla, con todo | 1,473 | +1,22 | 10 % → 11 % | 15 % → 18 % | 29 % (890) |
| Hora con 3 h | Dos por regla, sin tormenta con variables elegidas | 1,473 | +2,33 | 10 % → 10 % | 15 % → 15 % | 28 % (799) |
| Hora con 3 h | Tercer modelo que pesa | 1,473 | +1,72 | 10 % → 12 % | 15 % → 19 % | 26 % (1,047) |
| Hora con 3 h | El porcentaje mayor | 1,473 | -29,86 | 10 % → 20 % | 15 % → 34 % | 17 % (2,943) |
| Hora con 4 h | Un modelo con todo | 1,795 | +1,45 | 13 % → 15 % | 21 % → 23 % | 28 % (1,455) |
| Hora con 4 h | Dos por regla, variables de la página | 1,795 | -0,66 | 13 % → 11 % | 21 % → 19 % | 27 % (1,281) |
| Hora con 4 h | Dos por regla, con todo | 1,795 | -0,15 | 13 % → 14 % | 21 % → 24 % | 29 % (1,483) |
| Hora con 4 h | Dos por regla, sin tormenta con variables elegidas | 1,795 | +1,73 | 13 % → 12 % | 21 % → 20 % | 28 % (1,270) |
| Hora con 4 h | Tercer modelo que pesa | 1,795 | +0,48 | 13 % → 15 % | 21 % → 24 % | 27 % (1,584) |
| Hora con 4 h | El porcentaje mayor | 1,795 | -24,74 | 13 % → 22 % | 21 % → 38 % | 20 % (3,436) |
| Hora con 5 h | Un modelo con todo | 2,090 | +0,49 | 16 % → 17 % | 27 % → 28 % | 29 % (1,985) |
| Hora con 5 h | Dos por regla, variables de la página | 2,090 | -0,35 | 16 % → 15 % | 27 % → 26 % | 29 % (1,899) |
| Hora con 5 h | Dos por regla, con todo | 2,090 | -0,71 | 16 % → 16 % | 27 % → 31 % | 30 % (2,119) |
| Hora con 5 h | Dos por regla, sin tormenta con variables elegidas | 2,090 | +0,77 | 16 % → 17 % | 27 % → 28 % | 30 % (1,955) |
| Hora con 5 h | Tercer modelo que pesa | 2,090 | +0,49 | 16 % → 17 % | 27 % → 28 % | 29 % (2,039) |
| Hora con 5 h | El porcentaje mayor | 2,090 | -25,35 | 16 % → 26 % | 27 % → 45 % | 22 % (4,240) |
| Hora con 6 h | Un modelo con todo | 2,286 | +0,63 | 19 % → 19 % | 33 % → 35 % | 33 % (2,438) |
| Hora con 6 h | Dos por regla, variables de la página | 2,286 | +0,24 | 19 % → 19 % | 33 % → 33 % | 32 % (2,357) |
| Hora con 6 h | Dos por regla, con todo | 2,286 | -0,23 | 19 % → 20 % | 33 % → 36 % | 33 % (2,453) |
| Hora con 6 h | Dos por regla, sin tormenta con variables elegidas | 2,286 | -0,07 | 19 % → 19 % | 33 % → 33 % | 33 % (2,291) |
| Hora con 6 h | Tercer modelo que pesa | 2,286 | +0,43 | 19 % → 21 % | 33 % → 35 % | 31 % (2,573) |
| Hora con 6 h | El porcentaje mayor | 2,286 | -18,20 | 19 % → 27 % | 33 % → 45 % | 24 % (4,215) |
| Próximas 6 h | Un modelo con todo | 865 | +1,65 | 18 % → 20 % | 24 % → 32 % | 46 % (602) |
| Próximas 6 h | Dos por regla, variables de la página | 865 | +0,55 | 18 % → 19 % | 24 % → 25 % | 47 % (468) |
| Próximas 6 h | Dos por regla, con todo | 865 | +2,23 | 18 % → 20 % | 24 % → 33 % | 46 % (607) |
| Próximas 6 h | Dos por regla, sin tormenta con variables elegidas | 865 | +2,58 | 18 % → 20 % | 24 % → 31 % | 46 % (586) |
| Próximas 6 h | Tercer modelo que pesa | 865 | +1,62 | 18 % → 21 % | 24 % → 32 % | 44 % (640) |
| Próximas 6 h | El porcentaje mayor | 865 | -101,47 | 18 % → 40 % | 24 % → 74 % | 13 % (4,945) |

## Variables elegidas sin tormenta, hora en curso

Con los datos de antes de 2025, de mayor a menor correlación con la lluvia. Solo las 15 primeras.

| Variable | Correlación |
|---|---|
| `lluvia_previa` | +0.568 |
| `lluvia_previa_3h` | +0.438 |
| `vis` | -0.394 |
| `modelos_llueve_2h` | +0.263 |
| `base` | -0.257 |
| `ecmwf9_suma_2h` | +0.251 |
| `icon_suma_2h` | +0.244 |
| `ecmwf_suma_2h` | +0.234 |
| `techo` | -0.230 |
| `tb_centro` | -0.230 |
| `ecmwf_mm_3h` | +0.218 |
| `gfs_suma_2h` | +0.212 |
| `sp` | -0.208 |
| `ukmo_suma_2h` | +0.207 |
| `ir_centro` | +0.205 |
