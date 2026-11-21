# Evidencias de Entrega 9

Todos los datos son ficticios. Las cuatro capturas son pantallas reales de la aplicación conectada a la base entregada y están embebidas en Bitácora desde la fila 560.

- `01_consulta.jpg`: consulta consolidada del paciente HC 3, con signos y prescripciones locales/externas.
- `02_fhir.jpg`: resumen real de primera importación y reimportación. La pantalla volvió a ejecutar el intercambio antes de mostrar el resumen guardado en `resultado_intercambio.json`.
- `03_dicom.jpg`: metadatos del archivo anonimizado; conserva años 1984/2026 y sexo F.
- `04_auditoria.jpg`: acciones Q, I y E de consulta, intercambio y DICOM, con usuario autor y fecha UTC.
- `imagen_sintetica.png`, `generado.dcm`: patrón artificial y su conversión Secondary Capture.
- `entrada_identificada_ficticia.dcm`: copia de prueba con identificadores y privado ficticios agregados para verificar su eliminación.
- `anonimizado.dcm`, `metadatos_anonimizados.json`, `verificacion_dicom.json`: salida, metadatos y comparación de píxeles/UID.

El intercambio exportado JSON/XML y el recibido sintético están en `intercambio/`. El procedimiento, alcance y limitaciones están en `docs/entrega-9.md`.
