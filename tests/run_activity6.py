from __future__ import annotations

import io
import json
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT_DIR / "tests"
RESULT_DIR = ROOT_DIR / "evidencias" / "actividad_6"


class DetailedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.details = []
        self.started_at = {}

    def startTest(self, test):
        self.started_at[test.id()] = time.perf_counter()
        super().startTest(test)

    def _record(self, test, status, detail=""):
        elapsed = time.perf_counter() - self.started_at.get(test.id(), time.perf_counter())
        self.details.append(
            {
                "test": test.id(),
                "estado": status,
                "duracion_segundos": round(elapsed, 3),
                "detalle": detail,
            }
        )

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "APROBADA")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "FALLIDA", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "ERROR", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "OMITIDA", reason)


def preflight() -> None:
    targets = (
        "http://127.0.0.1:8000/api/health",
        "http://127.0.0.1:5500/frontend/index.html",
    )
    for target in targets:
        try:
            with urlopen(target, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"{target} respondió HTTP {response.status}")
        except Exception as exc:
            raise RuntimeError(
                "Los servidores deben estar activos antes de ejecutar la Actividad 6. "
                f"No se pudo acceder a {target}: {exc}"
            ) from exc


def main() -> int:
    preflight()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    suite = unittest.defaultTestLoader.discover(
        str(TEST_DIR), pattern="test_*.py", top_level_dir=str(ROOT_DIR)
    )
    stream = io.StringIO()
    started = time.perf_counter()
    runner = unittest.TextTestRunner(
        stream=stream, verbosity=2, resultclass=DetailedResult
    )
    result = runner.run(suite)
    duration = time.perf_counter() - started
    output = stream.getvalue()
    print(output)

    total = result.testsRun
    approved = len([item for item in result.details if item["estado"] == "APROBADA"])
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success_rate = round((approved / total * 100), 2) if total else 0
    screenshots = sorted(path.name for path in RESULT_DIR.glob("*.png"))

    payload = {
        "actividad": "Actividad 6 - Evaluación de calidad con Selenium",
        "fecha_ejecucion": datetime.now().astimezone().isoformat(timespec="seconds"),
        "duracion_total_segundos": round(duration, 3),
        "total_pruebas": total,
        "aprobadas": approved,
        "fallidas": failed,
        "errores": errors,
        "omitidas": skipped,
        "tasa_exito_porcentaje": success_rate,
        "capturas": screenshots,
        "detalle": result.details,
    }

    (RESULT_DIR / "resultados_pruebas.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RESULT_DIR / "salida_pruebas.txt").write_text(output, encoding="utf-8")

    print(
        f"Resumen: {approved}/{total} aprobadas | "
        f"{failed} fallidas | {errors} errores | éxito {success_rate}%"
    )
    print(f"Resultados: {RESULT_DIR / 'resultados_pruebas.json'}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
