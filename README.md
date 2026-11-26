# Central fotovoltaica de baja potencia

Una maqueta registra tensión y corriente en dos puntos del circuito. El ESP32 sirve una página local y exporta los ensayos a Excel. Python calcula potencia, energía, eficiencia del elevador y autonomía a partir de las lecturas.

```text
6 paneles de 5 V en paralelo → diodo 1N5819 → TP4056 → 2 celdas 18650 → MT3608 → carga
                                      INA260 0x40 en la entrada elegida     INA260 0x44 en la salida
```

## Resultados del lote vigente

El análisis usa los ocho Excel registrados del 19 al 23 de noviembre de 2026. Los lotes A y B se conservan como archivo histórico. Las ocho pruebas suman 33 682 lecturas, de las que 33 564 pasan el filtro para comparar puntos de medida. En las tres descargas elegibles, el MT3608 obtuvo **86,40 % de eficiencia media**, calculada con las potencias medias de salida y entrada. [Tabla de resultados](tablas/resumen_pruebas.csv)

## Cómo reproducir el análisis

1. Abrir `tablero.html` desde el repositorio descargado para explorar las ocho pruebas sin internet.
2. Instalar Python 3.10 o superior y ejecutar los comandos desde la raíz del repositorio.

```bash
python -m pip install -r requirements.txt
python analisis_vigente.py
python tablero.py --sin-abrir
```

También se puede abrir `corte3.ipynb` en Jupyter y ejecutar todas sus celdas. El análisis actualiza `graficas/`, `tablas/` y `resultados.json`. La opción `python analizar_prueba.py archivo.xlsx` genera una ficha individual.

## Montaje y documentación

Materiales principales: seis paneles de 5 V, diodo Schottky 1N5819, módulo TP4056, dos celdas 18650 con portapilas, elevador MT3608, dos INA260, ESP32 DevKit, carga y elementos de protección. La corriente nominal de los paneles, la capacidad de las celdas y la protección instalada requieren confirmación. Consultar el esquema y las verificaciones del [informe técnico](docs/INFORME_TECNICO.md) antes de reproducir el cableado.

| Documento | Contenido |
| --- | --- |
| [Resumen ejecutivo](docs/RESUMEN_EJECUTIVO.md) | Solución, resultados y limitaciones |
| [Informe técnico en Word con formato IEEE](docs/INFORME_TECNICO_IEEE.docx) · [Versión Markdown](docs/INFORME_TECNICO.md) | Electrónica, adquisición, pruebas y análisis |
| [Análisis en Python](docs/ANALISIS_PYTHON.md) | Métodos y reproducción |
| [Diccionario de datos](docs/DICCIONARIO_DATOS.md) | Excel del ESP32 y tablas generadas |
| [Estructura](docs/ESTRUCTURA.md) | Organización actual y propuesta |
| [Registro de cambios](CHANGELOG.md) | Evolución y decisiones |
