# MENFA PIG MFL — Gasoductos

Primera versión funcional educativa en Streamlit para simular inspección interna MFL en un gasoducto.

## Requisitos
- Python 3.10 o superior
- pip

## Ejecutar en Windows
1. Descomprimir el proyecto.
2. Abrir una terminal dentro de la carpeta `menfa_pig_mfl`.
3. Crear un entorno virtual (recomendado):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Iniciar:
   ```bash
   streamlit run app.py
   ```

## Ejecutar en Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Incluye
- Configuración de gasoducto y corrida
- Generación reproducible de señales MFL sintéticas
- Monitor por canal y mapa de calor
- Detección de candidatos a indicación
- Escenarios de calidad de datos degradada
- Historial local SQLite
- Exportación CSV y resumen TXT

## Limitaciones importantes
Este es un prototipo de entrenamiento. Las señales, defectos, amplitudes y detecciones son sintéticos. No sustituye un sistema MFL comercial, una validación experimental, una herramienta calibrada ni una evaluación de integridad real. La profundidad de pérdida de metal generada es la verdad de referencia del escenario, no una dimensión inferida de forma validada por el detector.

## Próximos pasos sugeridos
1. Validar el motor y mejorar agrupación de indicaciones.
2. Añadir vista longitudinal del gasoducto y estación de lanzamiento/recepción.
3. Añadir evaluación de alumno e instructor.
4. Generar PDF formal con ReportLab.
5. Incorporar calibración con datasets de referencia autorizados.
