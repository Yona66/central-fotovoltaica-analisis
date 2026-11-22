# Central fotovoltaica: análisis de datos

Visualización y analítica de las medidas de una maqueta de central fotovoltaica
(2 paneles de 5 V, TP4056, 2 baterías 18650, elevador MT3608 a 5 V). Un ESP32 con
sensores INA260 mide la entrada y la salida, y su página web exporta cada prueba a Excel.

## Uso rápido

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador. Por defecto muestra las pruebas de `datos/`; en la barra
lateral se pueden subir otros Excel del ESP32.

- **Una prueba:** voltaje, corriente, potencia y energía (con zoom), teórico contra real
  con % de error, estadística, caídas de tensión y descarga de la ficha en Excel.
- **Todas las pruebas:** clasificación por fuente (paneles, batería, carga) y comparación.

## Archivos

| Archivo | Qué es |
|---|---|
| `app.py` | Visor web (Streamlit) |
| `fisica.py` | Ohm, potencia, energía, eficiencia, error, lectura de los Excel y filtros |
| `analizar_prueba.py` | Lo mismo que el visor, por consola: `python analizar_prueba.py archivo.xlsx [--r 220]` |
| `corte3.ipynb` | Notebook comentado con todo el análisis, ya ejecutado |
| `datos/` | Excel de las pruebas (`lote2/` y las pruebas 8 y 9) |
| `graficas/`, `tablas/`, `resultados.json` | Salidas del notebook |

## Notebook

Abrir `corte3.ipynb` (Jupyter o VS Code) y usar *Restart & Run All*. Regenera
`graficas/`, `tablas/` y `resultados.json` con los mismos números.

## Métodos

- **Potencia:** P = V · I en cada lectura.
- **Energía:** área bajo la potencia por trapecios; los huecos de más de 60 s no suman.
- **Eficiencia del MT3608:** E salida / E entrada (solo con la batería como fuente).
- **Error:** |real − teórico| / |teórico| · 100.
- **Ruido:** mediana móvil de 5 muestras y media móvil de 60 s, por tramos.
- **Caídas de tensión:** saltos entre muestras mayores que 8 desviaciones robustas (MAD).

Requiere Python 3.10 o superior.
