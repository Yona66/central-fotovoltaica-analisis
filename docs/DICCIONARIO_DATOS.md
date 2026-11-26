# Diccionario de datos

## Excel crudos de la campaña final

Los ocho archivos de [datos/lote3](../datos/lote3) siguen la convención `central_pv_pruebaN_fuente_fecha-hora.xlsx`. La marca temporal del nombre corresponde a la exportación. Para la hora de inicio usar el encabezado o la primera lectura. El programa asigna C1 a C8 según el número de prueba. La fuente de C2 y C4 se interpreta como batería a partir del nombre y del contexto de la prueba.

| Hoja | Campos y significado |
| --- | --- |
| Información | Texto de equipo, resolución, exactitud, ecuaciones y referencias. |
| Resumen | Número (entero), nombre y fuente (texto), inicio (fecha/hora), duración y tiempo con sol (h), periodo (s), muestras y muestras sin dato (enteros), energía (mWh), potencia media y máxima (mW), tensión mínima y máxima (V), cociente de salida/entrada exportado (%). |
| Prueba N | Una fila por lectura. Los campos se desglosan abajo. |
| Notas | Número de prueba, fecha/hora local, tiempo transcurrido (s) y texto libre. |

| Columnas de Prueba N | Tipo y unidad | Significado |
| --- | --- | --- |
| `n` | Entero | Número de lectura |
| `fecha` | Fecha/hora local | Hora de lectura si el ESP32 la conocía |
| `t` | Real, s | Tiempo acumulado del registro |
| `V`, `Vs` | Real, V | Tensión de entrada 0x40 y salida 0x44 |
| `I`, `Is` | Real con signo, mA | Corriente de entrada y salida |
| `P_esp`, `Ps_esp` | Real, mW | Potencia exportada en cada punto |
| `E_esp`, `Es_esp` | Real, mWh | Energía acumulada exportada |

El cociente mostrado en el Excel original puede provenir de energía acumulada. Su campo histórico se preserva como parte del archivo crudo. El análisis vigente calcula la eficiencia del convertidor a partir de potencia.

## Resultados procesados

| Archivo | Contenido |
| --- | --- |
| [resumen_pruebas.csv](../tablas/resumen_pruebas.csv) | Una fila por prueba, UTF-8 con BOM, coma separadora y punto decimal. |
| [tablas_corte3.xlsx](../tablas/tablas_corte3.xlsx) | Hojas Resumen, Por fuente, Rendimiento y Autonomía. |
| [resultados.json](../resultados.json) | Pruebas, medias por fuente, autonomía y totales consumidos al generar la presentación local. |

| Campo del resumen | Tipo, unidad y significado |
| --- | --- |
| `prueba`, `nombre`, `fuente`, `archivo` | Texto. Identificador, etiqueta cruda, fuente clasificada y Excel original. |
| `inicio`, `duracion_h`, `horas_validas_h` | Fecha/hora local y reales en h. Inicio, tiempo transcurrido y suma de intervalos positivos válidos de hasta 60 s. |
| `lecturas`, `validas`, `saltos` | Enteros. Filas crudas, filas que pasan validación de ambos puntos y saltos detectados. |
| `v_ent_V`, `v_sal_V`, `i_ent_mA`, `i_sal_mA` | Reales. Medias de tensión y corriente válidas para cada punto. |
| `p_ent_mW`, `p_sal_mW`, `perdida_mW` | Reales. Potencias medias y pérdida de potencia en descargas elegibles. |
| `energia_ent_mWh`, `energia_sal_mWh`, `energia_esp_mWh` | Reales. Energías acumuladas integradas en Python y energía de entrada exportada por el ESP32. |
| `r_carga_ohm`, `sigma_sal_mV`, `i_max_cruda_mA` | Reales. Mediana de resistencia equivalente, desviación estándar de la tensión de salida y corriente de entrada máxima de la serie cruda. |
| `error_energia_pct`, `error_potencia_pct`, `error_salida_pct`, `eficiencia_pct` | Reales en %. Error frente al ESP32 o la consigna y eficiencia por potencia, cuando aplica. |

La hoja «Por fuente» agrupa por fuente con peso igual por prueba. «Rendimiento» incluye las potencias medias, pérdida y eficiencia de C4, C6 y C8. «Autonomía» indica duración medida y calculada (h), energía de entrada del tramo (Wh), potencia del tramo (mW) y error porcentual. Una celda vacía o `null` indica que la métrica no se aplica o carece de referencia válida.
