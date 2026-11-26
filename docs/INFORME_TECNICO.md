# Informe técnico de la central fotovoltaica

## 1. Objetivo y alcance

Documentar el circuito, la adquisición con ESP32 y el análisis de generación y descarga de una central fotovoltaica en miniatura. Las magnitudes **medidas** son tiempo, tensión y corriente. Las de **cálculo** incluyen potencia, energía, eficiencia, resistencia equivalente, estabilidad y autonomía estimada. Las referencias **teóricas** provienen de ecuaciones, consignas y hojas de datos. Los resultados vigentes corresponden a C1–C8. Los cortes anteriores aportan contexto sobre el desarrollo.

## 2. Arquitectura y materiales

```text
Paneles 5 V en paralelo
       ↓
Diodo Schottky 1N5819 → TP4056 → dos celdas 18650 → MT3608 → carga
        [entrada solar]                             [salida]
                              [entrada en descarga]     │
                         INA260 0x40           INA260 0x44
                                  └── I²C ── ESP32 ── exportación Excel
```

| Componente | Función y alcance |
| --- | --- |
| Seis paneles de 5 V en paralelo | Fuente solar del montaje de noviembre. El cableado en paralelo conserva la tensión nominal y suma corriente disponible. Corriente y potencia nominales por panel, por confirmar. |
| Schottky 1N5819 | Reduce la corriente inversa hacia los paneles cuando cae la iluminación. |
| Módulo TP4056 | Carga de una celda o conjunto en paralelo con perfil de corriente y tensión constantes. La protección contra descarga y cortocircuito depende del módulo instalado y debe confirmarse. |
| Dos celdas 18650 y portapilas | Almacenamiento. El montaje se documentó en paralelo. La capacidad útil se estima de los registros de descarga y la capacidad nominal requiere verificación. |
| MT3608 | Eleva la tensión de batería a una salida ajustada a 5 V. |
| ESP32 DevKit y dos INA260 | Capturan tensión y corriente, muestran el estado y guardan el registro. |
| Carga, interruptor y fusible | Los cortes anteriores documentan cargas LED. El diseño prevé interruptor y fusible de 1 A. La carga exacta de cada ensayo y la protección instalada requieren confirmación. |

## 3. Conexiones y protección

| Punto | Conexión prevista |
| --- | --- |
| Bus I²C | SDA en GPIO 21, SCL en GPIO 22, reloj de 100 kHz y masa común. |
| Alimentación de los INA260 | 3,3 V desde el ESP32. Verificar que las líneas I²C queden a 3,3 V. |
| Entrada, 0x40 | Puentes A0 y A1 en su configuración de fábrica. En generación, en serie después del diodo y antes del TP4056. En descarga, en serie en la entrada del elevador. |
| Salida, 0x44 | Puente A1 a VDD. En serie entre VOUT+ del elevador y el positivo de la carga. |
| Batería, 0x41 | Dirección reservada para un tercer sensor. Nodo desactivado en el firmware. |
| Alimentación del ESP32 | USB en banco o 5 V regulados en VIN, conforme a la placa usada. |

Comprobar la polaridad, la protección del conjunto de celdas y la salida ajustada del elevador con la carga desconectada. Para ramas LED, comprobar la resistencia en serie con cada rama según la caída del LED y su corriente. La resistencia de 330 Ω figura como referencia previa y requiere verificación en la maqueta. Identificar los terminales de batería y salida protegida del módulo específico antes de reproducir el cableado.

## 4. Medición y adquisición

El INA260 usa un shunt interno de 2 mΩ y convierte la caída de tensión en corriente. El ADC es de 16 bits y los pasos nominales son 1,25 mA y 1,25 mV. El firmware configura promediado de 64 conversiones y 1,1 ms por conversión de corriente y de tensión. Intenta hasta tres lecturas por medida, promedia las válidas y representa como cero corrientes con magnitud inferior a 2,5 mA tras retirar el desplazamiento. [Ficha técnica de Texas Instruments, §§ 7.5 y 8.3](https://www.ti.com/lit/ds/symlink/ina260.pdf)

El periodo interno nominal del firmware es 500 ms, el intervalo de registro por defecto es 1 s y **cada Excel del lote C declara 5 s**. En memoria, la tensión se guarda en pasos de 1 mV y la corriente en pasos de 0,1 mA. El formato de guardado admite cifras más finas que la resolución nominal del sensor. [Archivos del lote vigente](../datos/lote3)

La página local muestra las magnitudes y gestiona inicio, pausa, notas y descarga. El registro queda en la memoria del ESP32 y el navegador arma el archivo `.xlsx`. Las hojas son **Información**, **Resumen**, **Prueba N** y **Notas**. Existen también salida serie, envío configurable a ThingSpeak y un registrador opcional en SQLite. La entrega del corte 3 se reproduce con los Excel, sin depender de esos canales. [Diccionario](DICCIONARIO_DATOS.md)

## 5. Ecuaciones y criterios

- Ley de Ohm para la resistencia equivalente, `R = V / I`. Con corriente en mA se convierte primero a A.
- Potencia instantánea, `P = V · I`. Voltios por miliamperios dan milivatios.
- Energía, `E = ∫P dt`. El registro integra por rectángulos y Python por trapecios usando tiempo real. El análisis omite intervalos mayores a 60 s.
- Eficiencia del MT3608, `η = 100 × media(P_salida) / media(P_entrada)`. Se aplica a las lecturas pareadas válidas de cada descarga elegible y se promedia por prueba.
- Pérdida de potencia, `media(P_entrada) − media(P_salida)`. En generación esa diferencia puede incluir almacenamiento y otros componentes.
- Error porcentual, `100 × |real − referencia| / |referencia|`. Se omiten referencias nulas o insuficientes.
- Tiempo con sol en la exportación, intervalos con potencia del sensor de panel superior a 10 mW. En archivos con fuente mal rotulada esa columna no representa irradiación.

## 6. Campaña vigente

El punto de salida se mantuvo después del MT3608. En generación, 0x40 corresponde a la rama situada después del diodo. En consumo, 0x40 corresponde a la entrada del elevador. La orientación del sensor determina el signo. En la entrada del elevador, corriente positiva representa entrega de la batería hacia el elevador. En la línea de carga histórica, el signo dependió de cómo se orientó el sensor y se interpretó con el punto de conexión. En esta campaña se alternaron pruebas de generación y consumo con seis paneles y registro a 5 s. Se conservan los rótulos crudos en los Excel y se corrigió la clasificación de C2 y C4 en Python.

| Prueba | Inicio según Excel | Fuente y punto 0x40 | Duración (h) | Lecturas válidas / crudas | Condiciones y carga |
| --- | --- | --- | ---: | ---: | --- |
| C1 | 19-nov 12:35 | Paneles, después del diodo | 5,07 | 3 649 / 3 649 | Generación diurna, carga por confirmar |
| C2 | 19-nov 17:40 | Batería, entrada del MT3608 | 4,61 | 13 / 16 | Consumo, cobertura escasa, carga por confirmar |
| C3 | 20-nov 13:49 | Paneles, después del diodo | 2,34 | 1 683 / 1 683 | Generación diurna, carga por confirmar |
| C4 | 20-nov 16:10 | Batería, entrada del MT3608 | 14,61 | 4 485 / 4 498 | Consumo con huecos, carga por confirmar |
| C5 | 21-nov 06:48 | Paneles, después del diodo | 9,31 | 5 547 / 5 611 | Generación diurna, carga por confirmar |
| C6 | 21-nov 16:07 | Batería, entrada del MT3608 | 15,77 | 4 954 / 4 974 | Consumo con huecos, carga por confirmar |
| C7 | 22-nov 07:54 | Paneles, después del diodo | 7,96 | 5 699 / 5 704 | Generación diurna, carga por confirmar |
| C8 | 22-nov 16:09 | Batería, entrada del MT3608 | 20,44 | 7 534 / 7 547 | Consumo con huecos, carga por confirmar |

Las hojas «Notas» aparecen vacías. Quedan por confirmar la temperatura, irradiancia, orientación, sombreados y los detalles de cableado de cada ensayo. [Registros originales](../datos/lote3) · [Tabla calculada](../tablas/resumen_pruebas.csv)

## 7. Resultados

### Generación solar y carga

C1, C3, C5 y C7 registraron potencia media de entrada de 193,9, 289,2, 315,8 y 321,8 mW respectivamente. Su promedio por ensayo fue **280,2 mW**. El máximo crudo de corriente en entrada solar fue **161,3 mA** en C5. Es un máximo observado bajo esas condiciones. El lote final no instrumentó simultáneamente entrada solar y línea de carga de la batería, así que quedan pendientes la curva completa de carga, el tiempo requerido y la eficiencia del TP4056. [Curvas de tensión y corriente](../graficas/paneles.png) · [Resultados](../tablas/resumen_pruebas.csv)

### Consumo, rendimiento y autonomía

| Descarga | P entrada media (mW) | P salida media (mW) | η por potencia | Tramo medido (h) | Estimado (h) |
| --- | ---: | ---: | ---: | ---: | ---: |
| C4 | 544,7 | 472,0 | 86,66 % | 5,83 | 5,52 |
| C6 | 547,5 | 472,6 | 86,32 % | 3,95 | 6,75 |
| C8 | 379,6 | 327,4 | 86,24 % | 10,31 | 6,88 |
| Promedio | 490,6 | 424,0 | 86,40 % | 6,69 | 6,38 |

C2 aporta contexto de consumo y se excluye del cálculo de eficiencia por sus 13 lecturas válidas. En las otras tres descargas, la pérdida media fue **66,6 mW**. La autonomía registra la duración del bloque continuo seleccionado. Se ajustó un polinomio de grado 4 por serie y se estimó el tiempo con `t = E / P`, usando para cada ensayo la energía media de los otros dos. El error medio **32,3 %** caracteriza esta prueba cruzada con tres descargas, sensible a condición inicial, huecos y carga. La salida durante las tres descargas tuvo medias entre **4,938 y 4,966 V** y desviaciones de **2,7 a 21,5 mV**. [Descarga y autonomía](../graficas/r2_descarga_autonomia.png) · [Estabilidad](../graficas/r3_estabilidad.png) · [Datos calculados](../resultados.json)

### Validación de cálculos y sensores

La potencia recalculada coincide a dos decimales porcentuales con la columna de potencia exportada. La energía de entrada difiere **0,68 %** en promedio respecto al acumulado del ESP32. El error medio de la salida frente a la consigna de 5 V es **0,90 %** en las descargas elegibles. Las tres métricas usan los registros de la propia maqueta y sirven para comprobar cálculos y regulación. **La comparación experimental INA260–multímetro quedó pendiente.** [Comparación](../graficas/r3_teorico_vs_real.png) · [Resultados](../resultados.json)

## 8. Incertidumbre y confiabilidad

A 25 °C, se estima el límite lineal como `offset / lectura + ganancia`. Los valores típicos describen la especificación típica del fabricante. Este presupuesto excluye cableado, calibración, resolución de guardado y condiciones fuera de la especificación. [Ficha INA260, § 7.5](https://www.ti.com/lit/ds/symlink/ina260.pdf)

| Magnitud | Offset típico / máximo | Ganancia típica / máxima | Ejemplo típico / máximo |
| --- | --- | --- | --- |
| Corriente | 1,25 / 5 mA | 0,02 / 0,15 % | 22,5 mA → 5,58 / 22,37 % |
| Corriente | 1,25 / 5 mA | 0,02 / 0,15 % | 26,3 mA → 4,77 / 19,16 % |
| Corriente | 1,25 / 5 mA | 0,02 / 0,15 % | 40 mA → 3,15 / 12,65 % |
| Tensión | 1,25 / 7,5 mV | 0,02 / 0,10 % | 5 V → 0,045 / 0,25 % |
| Tensión | 1,25 / 7,5 mV | 0,02 / 0,10 % | 3,9 V → 0,052 / 0,292 % |

El offset fijo pesa más cuando la corriente es baja. La temperatura puede cambiar el offset y la ganancia. Para validar, medir 8 a 10 puntos con un multímetro de referencia en cada nodo, cubrir cargas bajas y altas, repetir mediciones y ajustar `referencia = a · sensor + b`. Registrar resolución, temperatura, repetibilidad y residuales antes de aplicar la corrección. Los valores históricos de incertidumbre de rendimiento y las causas propuestas para cortes o saltos requieren mediciones independientes.

## 9. Maqueta

El diorama representa una central con paneles en diagonal y soportes para cargas luminosas. Las fotos locales documentan un montaje físico. Las medidas y el estado definitivo del montaje requieren verificación.

| Elemento | Descripción del equipo por confirmar |
| --- | --- |
| Base | Cartón, 60 × 43 cm tras una revisión desde 60 × 45 cm |
| Central | Caja de 24 × 15 cm para alojar parte del circuito y la batería |
| Cargas visibles | Cuatro torres con LEDs en paralelo |

## 10. Limitaciones y próximos pasos

- Documentar el estado de la maqueta, la ficha de los paneles, la capacidad real de las celdas, el fusible y las protecciones instaladas.
- Verificar carga, resistencia, posición y polaridad de los sensores en cada prueba con el equipo.
- Validar con multímetro, caracterizar la carga solar de la batería y registrar irradiancia y temperatura.
- Revisar los contactos y verificar la protección de descarga ante las caídas registradas. Identificar su causa con medición directa.
- Considerar un tercer INA260 para medir entrada solar, batería y salida simultáneamente.
- Confirmar formato de inscripción y declaración de herramientas, si se requiere. El equipo puede añadir la declaración antes de entregar.

El corte 1 queda documentado por el montaje, dos sensores, programa y registros exportados. El corte 2 aporta ensayos de generación y consumo, con comparación instrumental y carga completa pendientes. El corte 3 entrega procesamiento, análisis y visualización reproducibles para ocho registros. [Análisis en Python](ANALISIS_PYTHON.md) · [Cambios](../CHANGELOG.md)
