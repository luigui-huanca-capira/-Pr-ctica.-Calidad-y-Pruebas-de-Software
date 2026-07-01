from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


API_BASE = "http://127.0.0.1:8000/api"


def api_get(path: str, **params):
    query = f"?{urlencode(params)}" if params else ""
    with urlopen(f"{API_BASE}{path}{query}", timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


class ApiIntegrationTests(unittest.TestCase):
    """Pruebas de integración entre servidor HTTP, servicio y datos CSV."""

    def test_health_endpoint(self) -> None:
        status, payload = api_get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_filter_options_expose_25_departments(self) -> None:
        status, payload = api_get("/filters/options")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["departamentos"]), 25)
        self.assertIn("CALLAO", payload["departamentos"])

    def test_callao_summary_contains_six_accidents(self) -> None:
        status, payload = api_get("/dashboard/summary", departamento="CALLAO")
        self.assertEqual(status, 200)
        self.assertEqual(payload["kpis"]["total_accidentes"], 6)
        self.assertEqual(
            payload["por_departamento"],
            [{"departamento": "CALLAO", "accidentes": 6}],
        )

    def test_callao_records_are_consistent(self) -> None:
        status, payload = api_get("/accidentes", departamento="CALLAO", limite=100)
        self.assertEqual(status, 200)
        self.assertEqual(payload["total_filtrado"], 6)
        self.assertEqual(len(payload["registros"]), 6)
        self.assertTrue(
            all(row["departamento"] == "CALLAO" for row in payload["registros"])
        )

    def test_invalid_year_is_rejected(self) -> None:
        with self.assertRaises(HTTPError) as context:
            api_get("/dashboard/summary", anio=2019)
        self.assertEqual(context.exception.code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
