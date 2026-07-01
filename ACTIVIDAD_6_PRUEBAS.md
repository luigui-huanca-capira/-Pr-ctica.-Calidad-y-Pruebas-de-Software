# Actividad 6 - Pruebas de calidad con Selenium

## Herramienta seleccionada

Selenium WebDriver 4.45.0 con Google Chrome en modo automatizado.

## Tipos de prueba implementados

1. Pruebas unitarias del servicio de datos.
2. Pruebas de integración de la API REST.
3. Pruebas funcionales de extremo a extremo con Selenium.

## Preparación

Desde la raíz del proyecto, con el entorno virtual activado:

```powershell
python -m pip install -r requirements-test.txt
```

Mantener activos el backend en el puerto 8000 y el frontend en el puerto 5500.

## Ejecución completa

```powershell
python tests\run_activity6.py
```

Los resultados, capturas y el Excel de evidencia se generan en:

```text
evidencias\actividad_6\
```

El proceso devuelve código `0` cuando todas las pruebas son satisfactorias y código `1` cuando existe al menos una prueba fallida o con error.
