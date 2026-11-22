# Central fotovoltaica: análisis de datos

Visualización y analítica de las medidas de una maqueta de central fotovoltaica
(2 paneles de 5 V, TP4056, 2 baterías 18650, elevador MT3608 a 5 V). Un ESP32 con
sensores INA260 mide la entrada y la salida, y su página web exporta cada prueba a Excel.

## Uso rápido

Abrir `tablero.html` con doble clic: gráficas y analítica de todas las pruebas, sin internet.

Para sumar una prueba nueva, copiar su Excel en `datos/` y regenerar el tablero:

```bash
pip install -r requirements.txt   # una sola vez
python tablero.py
```

- **Una prueba:** voltaje, corriente, potencia y energía (lectura con el puntero, zoom con Ctrl + rueda),
  teórico contra real con % de error, estadística y caídas de tensión.
- **Todas las pruebas:** clasificación por fuente (paneles, batería, carga) y comparación.

## Archivos

| Archivo | Qué es |
|---|---|
| `tablero.py`, `tablero_plantilla.html` | Python lee los Excel, calcula todo y escribe `tablero.html` |
| `tablero.html` | Resultado listo para abrir |
| `fisica.py` | Ohm, potencia, energía, eficiencia, error, lectura de los Excel y filtros |
| `analizar_prueba.py` | Teórico contra real y ficha en Excel de una prueba: `python analizar_prueba.py archivo.xlsx [--r 220]` |
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
