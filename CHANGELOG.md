# Registro de cambios

## Septiembre de 2026 · Adquisición y montaje inicial

- Se implementó la adquisición con ESP32 y se pasó de INA219 a INA260. El montaje se consolidó con dos direcciones en un único bus I²C, 0x40 para entrada y 0x44 para salida. La dirección 0x41 quedó reservada y desactivada.
- Se añadieron página local, exportación, ThingSpeak y el registrador SQLite. En el ESP32 se incorporaron las pruebas con notas, el registro en memoria, alarmas y configuración WiFi desde la página.

## Octubre y comienzos de noviembre · Ensayos exploratorios

- Se corrigieron problemas con las alarmas al ocultar el panel y las descargas en móvil. Se ensayaron dos perfiles de carga A/B y después configuraciones de tres y cuatro LEDs, junto con otros ensayos. El historial documenta 22,5 y 26,3 mA para configuraciones previas. Se conservan los registros para trazabilidad.
- La comparación exploratoria de incertidumbre utilizó 3,9 V como referencia de batería y la ganancia de tensión correcta del INA260 de 0,1 % máxima a 25 °C. El punto previo de 400 mA y el techo de aproximadamente 44 mA quedan como referencias históricas del borrador. El lote final alcanzó 161,3 mA crudos en C5. La causa de la eficiencia baja observada en la prueba histórica B22 quedó por confirmar.
- El rediseño de la maqueta reportó el cambio de cartón y base de 60 × 45 a 60 × 43 cm. Las medidas físicas finales están pendientes de confirmación.

## 19–26 de noviembre · Campaña final y análisis

- Se documentaron seis paneles en paralelo y ocho ensayos en archivos separados. C2 y C4 se clasificaron como consumo con batería por su nombre y el contexto de medición.
- Se archivaron los lotes anteriores. El notebook, las tablas, las gráficas y el tablero vigentes se regeneran solo con C1–C8.
- La eficiencia del MT3608 se calculó a partir de potencia. El análisis presenta medias por fuente y conserva el detalle de cobertura y régimen experimental.
- La presentación del equipo incorporó una vista previa de resultados y del programa y redujo las animaciones a una entrada por diapositiva. El repositorio público añade la documentación técnica y la reproducción del análisis.
