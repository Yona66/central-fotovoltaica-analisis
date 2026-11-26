# Resumen ejecutivo

Se construyó una maqueta de central fotovoltaica para medir cómo se genera, se almacena y se entrega energía a una carga. La campaña final usó seis paneles de 5 V en paralelo, un cargador TP4056, dos celdas 18650, un elevador MT3608, un ESP32 y dos sensores INA260. El sensor de entrada se ubicó en el circuito de los paneles o en la entrada del elevador según el ensayo. El segundo permaneció a la salida del elevador.

La página local del ESP32 permitió guardar y exportar lecturas a Excel. Los ocho archivos del 19 al 23 de noviembre de 2026 contienen **33 682 lecturas**, con un intervalo configurado de 5 s. El análisis conservó **33 564 lecturas válidas** para comparar la entrada y la salida. Los registros abarcan 80,10 h transcurridas y cubren 46,47 h mediante intervalos válidos de hasta 60 s. [Tabla de resultados](../tablas/resumen_pruebas.csv)

La potencia media de entrada en los cuatro ensayos solares fue **280,2 mW**. En las tres descargas elegibles, el elevador obtuvo **86,40 % de eficiencia media por potencia**, con **66,6 mW** de pérdida media. Los tramos continuos seleccionados duraron **6,69 h en promedio**, frente a **6,38 h calculadas** con la energía media de las otras descargas. El error absoluto medio por ensayo fue **32,3 %**. [Resultados reproducibles](../resultados.json)

Se dispone de un notebook, tablas exportables y un tablero sin conexión. La comparación con multímetro y la caracterización completa de carga solar de la batería quedan pendientes. Tampoco se midieron irradiancia o temperatura junto a los sensores en esta campaña. [Informe técnico](INFORME_TECNICO.md)
