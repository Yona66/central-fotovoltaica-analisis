# Central fotovoltaica: análisis de datos

Programa en Python que lee las medidas de una maqueta de central solar, las limpia,
calcula la física (potencia, energía, eficiencia, errores) y las muestra en un tablero web.

## Uso rápido

- **Ver resultados:** abrir `tablero.html` con doble clic. Funciona sin internet.
- **Sumar una prueba nueva:** copiar su Excel en `datos/` y regenerar el tablero:

```bash
pip install -r requirements.txt   # una sola vez
python tablero.py
```

Requiere Python 3.10 o superior.

## 1. La maqueta

```
6 paneles 5 V (paralelo) → diodo 1N5819 → cargador TP4056 → 2 baterías 18650 → elevador MT3608 (5 V) → carga (LEDs)
```

| Parte | Qué hace |
|---|---|
| Paneles | Convierten la luz del sol en electricidad. |
| Diodo | Deja pasar la corriente en un solo sentido: la batería no se descarga hacia los paneles. |
| TP4056 | Carga las baterías sin dañarlas. |
| Baterías 18650 | Guardan la energía (unos 3.7 V). |
| MT3608 | Sube el voltaje de la batería a 5 V fijos para la carga. |

## 2. Cómo se mide

- Un **ESP32** lee dos sensores **INA260**, que miden voltaje y corriente:
  - **entrada**: en los paneles o en la batería, según la prueba;
  - **salida**: después del elevador, justo antes de la carga.
- El ESP32 publica una página web. Desde el celular se crea una *prueba*, se graba una
  lectura cada pocos segundos y al final se descarga un **Excel** con todas las lecturas.
- Cada Excel trae una hoja por prueba. Esos archivos están en `datos/`.

## 3. Qué hace el análisis (requerimientos 1, 2 y 3)

1. **Procesamiento y modelo físico**
   - Importa los Excel a una sola tabla.
   - Quita lecturas imposibles (picos a 0 V por falsos contactos) y suaviza el ruido.
   - Calcula potencia (P = V · I) y energía (área bajo la potencia en el tiempo).
2. **Análisis y eficiencia**
   - Energía que entra y energía que sale; eficiencia del elevador y pérdidas.
   - Descarga de la batería y autonomía estimada.
   - Teórico contra real, con % de error.
3. **Visualización y validación**
   - Gráficas, estabilidad de la salida de 5 V y caídas bruscas de voltaje.

## 4. Archivos

| Archivo | Qué es |
|---|---|
| `fisica.py` | El núcleo: lee los Excel, limpia y calcula Ohm, potencia, energía, eficiencia, error y caídas. |
| `analizar_prueba.py` | Analiza un solo Excel y guarda una ficha: `python analizar_prueba.py archivo.xlsx [--r 220]` |
| `corte3.ipynb` | Notebook con todo el análisis paso a paso, ya ejecutado. |
| `tablero.py` + `tablero_plantilla.html` | Leen todos los Excel de `datos/` y escriben `tablero.html`. |
| `tablero.html` | El tablero listo para abrir. |
| `datos/` | Excel de las pruebas. |
| `graficas/`, `tablas/`, `resultados.json` | Salidas del notebook. |

## 5. El tablero (`tablero.html`)

- **Inicio:** cifras generales de todas las pruebas.
- **01 Explorar:** se elige una prueba y se ven:
  - voltaje, corriente, potencia y energía (lectura con el puntero; zoom con Ctrl + rueda);
  - teórico contra real, estabilidad, flujo de energía y caídas de voltaje.
- **02 Comparar:** todas las pruebas juntas, en gráfica y en una tabla ordenable que se exporta a CSV.
- **03 Método:** las fórmulas usadas.
- Tema claro y oscuro. Sirve en computador y en celular.

## 6. Notebook

Abrir `corte3.ipynb` (Jupyter o VS Code) y usar *Restart & Run All*. Regenera
`graficas/`, `tablas/` y `resultados.json` con los mismos números.

## 7. Métodos

- **Potencia:** P = V · I en cada lectura.
- **Energía:** área bajo la potencia por trapecios; los huecos de más de 60 s no suman.
- **Eficiencia del MT3608:** E salida / E entrada (solo con la batería como fuente).
- **Error:** |real − teórico| / |teórico| · 100.
- **Ruido:** mediana móvil de 5 muestras y media móvil de 60 s, por tramos.
- **Caídas de voltaje:** saltos entre muestras mayores que 8 desviaciones robustas (MAD).
