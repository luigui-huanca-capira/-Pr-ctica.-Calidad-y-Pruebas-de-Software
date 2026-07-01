# Plataforma Web de Monitoreo de Accidentes SUTRAN (2020-2021)

Prototipo orientado al curso de **Calidad de Software** para analizar accidentes de tránsito en carreteras del Perú con datos abiertos de SUTRAN.

## Características implementadas

- API backend con FastAPI (arquitectura por capas)
- Carga y limpieza de datos CSV con pandas
- Filtros por año, departamento y modalidad
- KPIs:
  - total de accidentes
  - total de fallecidos
  - total de heridos
- Visualizaciones:
  - tendencia mensual (línea)
  - accidentes por departamento (barras)
  - accidentes por modalidad (barras)
  - heatmap temporal día/hora (visualización no común)
- Tabla de registros filtrados

## Estructura

- `backend/app/main.py` - inicio de API
- `backend/app/api/routes.py` - endpoints
- `backend/app/services/data_service.py` - lógica de datos
- `backend/app/models/filters.py` - validación de filtros
- `backend/app/core/*` - configuración y logging
- `frontend/*` - dashboard web

## Requisitos

- Python 3.10+
- Archivo CSV en: `backend/data/accidentes_2020_2021.csv`

## Ejecución local

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`

### 2) Frontend

Abrir `frontend/index.html` en navegador (o usar Live Server de VSCode).

## Endpoints principales

- `GET /api/health`
- `GET /api/filters/options`
- `GET /api/dashboard/summary?anio=&departamento=&modalidad=`
- `GET /api/accidentes?anio=&departamento=&modalidad=&limite=300`

## Enfoque de calidad aplicado

- Validación de entradas con Pydantic
- Manejo básico de errores
- Logging centralizado
- Separación de responsabilidades (API / servicios / modelos / config)
- Tareas trazables en `TODO.md`
