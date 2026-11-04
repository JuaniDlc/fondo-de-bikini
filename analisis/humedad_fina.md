# Humedad, prueba fina

Lo escribe `analisis/humedad_fina.py`. Mejora: cuánto baja el Brier frente al modelo de la página (positivo es mejor). Para adoptarlo (fijado antes de ver los resultados): al menos +0,5 %, el intervalo de 99,9 % no incluye el cero y mejora en al menos 6 de 8 trimestres. Temporada lluviosa: enero a abril.

De 72 comparaciones, cumplen la regla: 0.

| Pronóstico | Fuente | Ventana | Mejora (%) | Intervalo de 99,9 % | Trimestres | Lluviosa (%) | Seca (%) | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Hora en curso | Humedad relativa de GFS | 3 h | -0,12 | [-0,40; +0,20] | 3/8 | -0,10 | -0,16 | no |
| Hora en curso | Humedad relativa de GFS | 6 h | -0,23 | [-0,48; +0,05] | 2/8 | -0,18 | -0,35 | no |
| Hora en curso | Humedad relativa de GFS | 12 h | -0,17 | [-0,52; +0,16] | 2/8 | -0,06 | -0,45 | no |
| Hora en curso | Humedad relativa de GFS | 24 h | -0,12 | [-0,39; +0,10] | 0/8 | -0,07 | -0,28 | no |
| Hora en curso | Punto de rocío de GFS | 3 h | -0,29 | [-0,87; +0,33] | 4/8 | -0,24 | -0,42 | no |
| Hora en curso | Punto de rocío de GFS | 6 h | -0,26 | [-0,80; +0,32] | 4/8 | -0,24 | -0,29 | no |
| Hora en curso | Punto de rocío de GFS | 12 h | -0,31 | [-0,85; +0,34] | 4/8 | -0,33 | -0,28 | no |
| Hora en curso | Punto de rocío de GFS | 24 h | -0,35 | [-0,88; +0,25] | 4/8 | -0,35 | -0,34 | no |
| Hora en curso | Aeropuerto (T − Td) | 3 h | +0,13 | [-0,39; +0,64] | 6/8 | +0,16 | +0,06 | no |
| Hora en curso | Aeropuerto (T − Td) | 6 h | -0,08 | [-0,54; +0,34] | 6/8 | -0,16 | +0,15 | no |
| Hora en curso | Aeropuerto (T − Td) | 12 h | -0,14 | [-0,41; +0,09] | 2/8 | -0,19 | -0,01 | no |
| Hora en curso | Aeropuerto (T − Td) | 24 h | -0,05 | [-0,30; +0,20] | 3/8 | -0,05 | -0,05 | no |
| Hora con 2 h | Humedad relativa de GFS | 3 h | -0,09 | [-0,32; +0,14] | 2/8 | -0,06 | -0,16 | no |
| Hora con 2 h | Humedad relativa de GFS | 6 h | -0,06 | [-0,45; +0,26] | 3/8 | +0,00 | -0,26 | no |
| Hora con 2 h | Humedad relativa de GFS | 12 h | +0,15 | [-0,54; +0,90] | 4/8 | +0,14 | +0,18 | no |
| Hora con 2 h | Humedad relativa de GFS | 24 h | +0,13 | [-0,41; +0,66] | 4/8 | +0,15 | +0,09 | no |
| Hora con 2 h | Punto de rocío de GFS | 3 h | -0,44 | [-1,31; +0,38] | 3/8 | -0,53 | -0,18 | no |
| Hora con 2 h | Punto de rocío de GFS | 6 h | -0,47 | [-1,28; +0,36] | 2/8 | -0,56 | -0,18 | no |
| Hora con 2 h | Punto de rocío de GFS | 12 h | -0,54 | [-1,49; +0,47] | 3/8 | -0,70 | -0,05 | no |
| Hora con 2 h | Punto de rocío de GFS | 24 h | -0,59 | [-1,57; +0,44] | 2/8 | -0,70 | -0,24 | no |
| Hora con 2 h | Aeropuerto (T − Td) | 3 h | +0,05 | [-0,32; +0,40] | 4/8 | +0,06 | +0,02 | no |
| Hora con 2 h | Aeropuerto (T − Td) | 6 h | -0,16 | [-0,49; +0,18] | 3/8 | -0,20 | -0,05 | no |
| Hora con 2 h | Aeropuerto (T − Td) | 12 h | -0,04 | [-0,39; +0,31] | 3/8 | -0,11 | +0,16 | no |
| Hora con 2 h | Aeropuerto (T − Td) | 24 h | -0,01 | [-0,65; +0,58] | 4/8 | -0,00 | -0,03 | no |
| Hora con 3 h | Humedad relativa de GFS | 3 h | +0,04 | [-0,25; +0,32] | 5/8 | +0,09 | -0,12 | no |
| Hora con 3 h | Humedad relativa de GFS | 6 h | +0,06 | [-0,56; +0,66] | 4/8 | +0,17 | -0,26 | no |
| Hora con 3 h | Humedad relativa de GFS | 12 h | +0,21 | [-0,76; +1,09] | 6/8 | +0,28 | +0,01 | no |
| Hora con 3 h | Humedad relativa de GFS | 24 h | +0,10 | [-0,61; +0,81] | 4/8 | +0,21 | -0,24 | no |
| Hora con 3 h | Punto de rocío de GFS | 3 h | -0,37 | [-0,98; +0,34] | 1/8 | -0,44 | -0,18 | no |
| Hora con 3 h | Punto de rocío de GFS | 6 h | -0,36 | [-1,12; +0,40] | 1/8 | -0,44 | -0,14 | no |
| Hora con 3 h | Punto de rocío de GFS | 12 h | -0,32 | [-1,24; +0,57] | 3/8 | -0,35 | -0,21 | no |
| Hora con 3 h | Punto de rocío de GFS | 24 h | -0,36 | [-1,31; +0,55] | 3/8 | -0,37 | -0,33 | no |
| Hora con 3 h | Aeropuerto (T − Td) | 3 h | -0,05 | [-0,26; +0,12] | 2/8 | -0,03 | -0,09 | no |
| Hora con 3 h | Aeropuerto (T − Td) | 6 h | -0,06 | [-0,29; +0,15] | 3/8 | -0,05 | -0,11 | no |
| Hora con 3 h | Aeropuerto (T − Td) | 12 h | -0,01 | [-0,57; +0,56] | 3/8 | -0,03 | +0,07 | no |
| Hora con 3 h | Aeropuerto (T − Td) | 24 h | -0,04 | [-0,98; +0,79] | 4/8 | +0,01 | -0,18 | no |
| Hora con 4 h | Humedad relativa de GFS | 3 h | -0,11 | [-0,74; +0,54] | 4/8 | +0,00 | -0,45 | no |
| Hora con 4 h | Humedad relativa de GFS | 6 h | +0,01 | [-0,86; +1,07] | 4/8 | +0,22 | -0,63 | no |
| Hora con 4 h | Humedad relativa de GFS | 12 h | +0,13 | [-1,18; +1,60] | 4/8 | +0,27 | -0,27 | no |
| Hora con 4 h | Humedad relativa de GFS | 24 h | -0,01 | [-0,99; +1,07] | 4/8 | +0,14 | -0,46 | no |
| Hora con 4 h | Punto de rocío de GFS | 3 h | -0,10 | [-0,34; +0,13] | 2/8 | -0,15 | +0,06 | no |
| Hora con 4 h | Punto de rocío de GFS | 6 h | -0,20 | [-0,54; +0,14] | 4/8 | -0,28 | +0,03 | no |
| Hora con 4 h | Punto de rocío de GFS | 12 h | -0,15 | [-0,82; +0,41] | 6/8 | -0,24 | +0,09 | no |
| Hora con 4 h | Punto de rocío de GFS | 24 h | -0,24 | [-0,99; +0,40] | 3/8 | -0,24 | -0,24 | no |
| Hora con 4 h | Aeropuerto (T − Td) | 3 h | -0,13 | [-0,37; +0,12] | 1/8 | -0,18 | +0,01 | no |
| Hora con 4 h | Aeropuerto (T − Td) | 6 h | -0,15 | [-0,64; +0,32] | 4/8 | -0,17 | -0,07 | no |
| Hora con 4 h | Aeropuerto (T − Td) | 12 h | +0,18 | [-0,69; +0,98] | 5/8 | +0,08 | +0,48 | no |
| Hora con 4 h | Aeropuerto (T − Td) | 24 h | +0,29 | [-0,64; +1,34] | 5/8 | +0,31 | +0,21 | no |
| Hora con 5 h | Humedad relativa de GFS | 3 h | -0,16 | [-0,71; +0,41] | 1/8 | -0,02 | -0,59 | no |
| Hora con 5 h | Humedad relativa de GFS | 6 h | -0,14 | [-1,43; +0,99] | 4/8 | +0,07 | -0,78 | no |
| Hora con 5 h | Humedad relativa de GFS | 12 h | +0,06 | [-1,37; +1,37] | 3/8 | +0,15 | -0,23 | no |
| Hora con 5 h | Humedad relativa de GFS | 24 h | -0,19 | [-1,11; +0,74] | 2/8 | -0,12 | -0,42 | no |
| Hora con 5 h | Punto de rocío de GFS | 3 h | -0,16 | [-0,30; +0,02] | 0/8 | -0,17 | -0,12 | no |
| Hora con 5 h | Punto de rocío de GFS | 6 h | -0,16 | [-0,54; +0,27] | 4/8 | -0,21 | -0,00 | no |
| Hora con 5 h | Punto de rocío de GFS | 12 h | -0,14 | [-0,94; +0,62] | 5/8 | -0,16 | -0,08 | no |
| Hora con 5 h | Punto de rocío de GFS | 24 h | -0,16 | [-0,96; +0,59] | 5/8 | -0,04 | -0,50 | no |
| Hora con 5 h | Aeropuerto (T − Td) | 3 h | -0,27 | [-0,59; +0,02] | 2/8 | -0,35 | -0,04 | no |
| Hora con 5 h | Aeropuerto (T − Td) | 6 h | -0,10 | [-0,73; +0,57] | 4/8 | -0,01 | -0,37 | no |
| Hora con 5 h | Aeropuerto (T − Td) | 12 h | +0,16 | [-1,02; +1,09] | 4/8 | +0,14 | +0,25 | no |
| Hora con 5 h | Aeropuerto (T − Td) | 24 h | +0,29 | [-0,87; +1,56] | 4/8 | +0,45 | -0,17 | no |
| Hora con 6 h | Humedad relativa de GFS | 3 h | -0,07 | [-0,91; +0,81] | 2/8 | +0,10 | -0,59 | no |
| Hora con 6 h | Humedad relativa de GFS | 6 h | +0,04 | [-1,37; +1,30] | 5/8 | +0,19 | -0,43 | no |
| Hora con 6 h | Humedad relativa de GFS | 12 h | +0,02 | [-1,29; +1,32] | 3/8 | +0,00 | +0,09 | no |
| Hora con 6 h | Humedad relativa de GFS | 24 h | -0,28 | [-1,22; +0,67] | 3/8 | -0,32 | -0,15 | no |
| Hora con 6 h | Punto de rocío de GFS | 3 h | -0,06 | [-0,32; +0,23] | 6/8 | -0,08 | +0,00 | no |
| Hora con 6 h | Punto de rocío de GFS | 6 h | +0,03 | [-0,55; +0,57] | 6/8 | -0,00 | +0,11 | no |
| Hora con 6 h | Punto de rocío de GFS | 12 h | -0,01 | [-0,92; +0,85] | 6/8 | +0,01 | -0,08 | no |
| Hora con 6 h | Punto de rocío de GFS | 24 h | -0,11 | [-0,94; +0,65] | 4/8 | +0,04 | -0,58 | no |
| Hora con 6 h | Aeropuerto (T − Td) | 3 h | -0,11 | [-0,42; +0,21] | 4/8 | -0,08 | -0,19 | no |
| Hora con 6 h | Aeropuerto (T − Td) | 6 h | +0,05 | [-0,87; +0,78] | 4/8 | +0,19 | -0,40 | no |
| Hora con 6 h | Aeropuerto (T − Td) | 12 h | +0,10 | [-1,15; +1,09] | 4/8 | +0,04 | +0,28 | no |
| Hora con 6 h | Aeropuerto (T − Td) | 24 h | +0,14 | [-1,13; +1,51] | 5/8 | +0,27 | -0,25 | no |
