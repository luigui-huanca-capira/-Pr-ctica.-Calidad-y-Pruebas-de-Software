# Práctica: Calidad y Pruebas de Software

## Actividad desarrollada

Este repositorio contiene únicamente los códigos utilizados para evaluar la calidad del proyecto **SUTRAN VIAL**, una plataforma web de monitoreo y visualización de accidentes de tránsito en carreteras del Perú durante el periodo 2020-2021.

La práctica corresponde a la **Actividad 6: Verificación y Mantenimiento de Software** del curso Calidad de Software, semestre 2026-I.

## Objetivo

Instalar y utilizar Selenium para implementar pruebas automatizadas sobre el proyecto del semestre. La evaluación incluye pruebas unitarias, pruebas de integración de la API y pruebas funcionales de extremo a extremo.

## Herramientas utilizadas

- Python 3.14.
- Selenium WebDriver 4.45.0.
- `unittest`, incluido en Python.
- Google Chrome.
- Apache JMeter 5.6.3 para el plan complementario `Thread Group.jmx`.

## Archivos incluidos

```text
.
├── README.md
├── requirements-test.txt
├── Thread Group.jmx
└── tests
    ├── __init__.py
    ├── run_activity6.py
    ├── test_api.py
    ├── test_data_service.py
    └── test_selenium.py
```

### Códigos de prueba

- `test_data_service.py`: seis pruebas unitarias de carga, filtros, departamentos y KPI.
- `test_api.py`: cinco pruebas de integración sobre los endpoints REST.
- `test_selenium.py`: seis pruebas funcionales de navegación, filtros, mapa, tabla y exportación.
- `run_activity6.py`: ejecuta toda la batería y genera el resumen de resultados.

En total se implementaron **17 casos de prueba**.

### Plan Thread Group

`Thread Group.jmx` es un plan de Apache JMeter configurado con:

- 100 usuarios concurrentes.
- Ramp-up de 60 segundos.
- Duración de 300 segundos.
- Solicitud HTTP GET de prueba.
- Aggregate Report y View Results Tree.

## Instalación

Activar el entorno virtual e instalar Selenium:

```powershell
python -m pip install -r requirements-test.txt
```

## Ejecución

El proyecto SUTRAN VIAL debe encontrarse activo en:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5500
```

Ejecutar todas las pruebas desde la raíz del proyecto:

```powershell
python tests\run_activity6.py
```

## Resultado registrado

La ejecución final obtuvo:

```text
17 pruebas ejecutadas
17 pruebas aprobadas
0 pruebas fallidas
100 % de éxito
```

Los informes y capturas de pantalla se presentan como entregables separados y no forman parte de este repositorio de código.
