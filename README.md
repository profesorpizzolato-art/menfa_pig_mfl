# MENFA PIG MFL — Suite avanzada v0.2

Aplicación Streamlit para formación y experimentación educativa con inspección interna de gasoductos mediante un modelo híbrido de señales MFL sintéticas y una vista 3D esquemática.

> **Uso exclusivamente educativo.** No es un solver electromagnético validado y no debe usarse para evaluar integridad, definir reparaciones ni tomar decisiones operacionales en gasoductos reales.

## Requisitos
- Python 3.10–3.13 recomendado.
- pip actualizado.
- Navegador moderno.

## Instalación en Windows
1. Descomprimir el ZIP en una carpeta nueva. No reemplazar la carpeta del proyecto v0.1.
2. Abrir CMD o PowerShell dentro de `menfa_pig_mfl_v0_2`.
3. Crear entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   Si PowerShell bloquea la activación, usar CMD y ejecutar `\.venv\Scripts\activate.bat`.
4. Iniciar la aplicación:

   ```powershell
   streamlit run app.py
   ```
5. Streamlit abrirá una URL local, normalmente `http://localhost:8501`.

## Instalación en Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Ejecutar pruebas
Desde la raíz del proyecto, con el entorno virtual activado:

```bash
python -m unittest discover -s tests -v
```

## Módulos
- **Centro de control 3D:** parámetros, escenarios, PIG móvil, soldaduras y anomalías sintéticas; guarda corridas y exporta CSV.
- **Laboratorio MFL:** señales por canal, mapa de amplitud, indicaciones por umbral y anomalías de referencia.
- **Informe de corrida:** descarga de informe JSON y tabla de anomalías CSV.
- **Historial:** corridas persistidas en SQLite.
- **Acerca del modelo:** arquitectura y limitaciones.

## Arquitectura
- `app.py`: interfaz y navegación.
- `core/engine.py`: generación de anomalías, señales sintéticas, detector didáctico y geometría 3D Plotly.
- `data/database.py`: persistencia SQLite.
- `tests/`: pruebas unitarias del motor y la base de datos.
- `requirements.txt`: dependencias Python.

La base de datos se crea automáticamente en `data/menfa_pig_mfl.db` al iniciar la app. No se versiona una base con datos de usuarios.

## Qué representa el modelo híbrido
La amplitud sintética depende de profundidad de referencia, sensibilidad, posición circunferencial, ruido y posición longitudinal. Esto aporta relaciones didácticas para explorar señales, pero **no sustituye** ecuaciones electromagnéticas, geometría/materiales calibrados, validación experimental ni criterios de evaluación de inspección industrial.

## Solución de problemas
- `streamlit` no se reconoce: activar `.venv` y volver a instalar `requirements.txt`.
- Puerto ocupado: `streamlit run app.py --server.port 8502`.
- Vista 3D vacía: actualizar navegador y comprobar que Plotly se instaló con `pip show plotly`.
- Reiniciar el entorno si se mezclaron dependencias: eliminar `.venv`, crearla de nuevo e instalar `requirements.txt`.

