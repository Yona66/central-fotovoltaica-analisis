# Análisis de las pruebas en Python

## Flujo reproducible

1. `fisica.py` abre Excel con openpyxl y convierte las hojas «Prueba N» en tablas Pandas. Interpreta las pruebas de consumo como batería aunque C2 y C4 tengan el rótulo «Paneles solares».
2. `analisis_vigente.py` usa `datos/lote3/`. Calcula Ohm, potencia y energía. Exige lecturas presentes, tensión mayor a 0,05 V y corrientes positivas mayores a 1 mA para los cálculos pareados. Las gráficas de señal usan mediana de cinco muestras y media de doce por tramo.
3. La energía usa trapecios sobre las series crudas y omite intervalos mayores a 60 s. La eficiencia usa potencias medias válidas y requiere al menos 100 lecturas de una prueba de batería. Los promedios por fuente dan el mismo peso a cada prueba del grupo.
4. En descarga, se selecciona el tramo continuo más largo con al menos 100 lecturas y se ajusta un polinomio de grado cuatro. El cálculo de autonomía `E/P` usa como referencia las otras descargas con inicio por encima de 3,3 V y final por debajo de 3,0 V. Se compara con lo observado en el tramo.
5. La función `caidas` detecta saltos de tensión mediante desviación absoluta mediana con piso de 0,05 V. Los saltos son candidatos para inspección y pueden incluir transiciones o puntos a ambos lados de una pausa. La desviación estándar poblacional con NumPy cuantifica la estabilidad de salida.
6. Se generan curvas superpuestas y comparaciones con el registro, tablas CSV y Excel y un JSON de resultados. `tablero.py` crea un HTML local que permite identificar, explorar y comparar las ocho pruebas.

```bash
python -m pip install -r requirements.txt
python analisis_vigente.py
python tablero.py --sin-abrir
```

El [notebook](../corte3.ipynb) ejecuta los mismos cálculos paso a paso y muestra las figuras. Para una ficha individual usar `python analizar_prueba.py archivo.xlsx [--fuente bateria] [--r OHM]`.

## Análisis histórico

El `analisis/graficas.py` del proyecto original recibe, opcionalmente, una carpeta como primer argumento. Por defecto lee los diez archivos de la carpeta local original `DATOS OBTENIDOS/` y genera siete gráficos y `analisis/graficas/resumen_pruebas.csv`. Para reproducir esa edición histórica desde el proyecto original usar `python analisis/graficas.py`. Sus valores describen el corte 2 y quedan fuera de los resultados vigentes.
