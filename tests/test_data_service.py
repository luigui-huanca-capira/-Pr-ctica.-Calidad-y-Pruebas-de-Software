from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.data_service import (  # noqa: E402
    apply_filters,
    get_by_departamento,
    get_kpis,
    load_data,
)


class DataServiceUnitTests(unittest.TestCase):
    """Pruebas unitarias de limpieza, filtros y agregaciones."""

    @classmethod
    def setUpClass(cls) -> None:
        load_data.cache_clear()
        cls.data = load_data()

    def test_dataset_contains_expected_number_of_records(self) -> None:
        self.assertEqual(len(self.data), 8155)

    def test_department_catalog_includes_callao(self) -> None:
        rows = get_by_departamento(self.data)
        by_name = {row["departamento"]: row["accidentes"] for row in rows}
        self.assertEqual(len(rows), 25)
        self.assertEqual(by_name.get("CALLAO"), 6)

    def test_department_filter_returns_only_callao(self) -> None:
        filtered = apply_filters(self.data, departamento="CALLAO")
        self.assertEqual(len(filtered), 6)
        self.assertTrue(
            all(row.get("departamento_canonico") == "CALLAO" for row in filtered)
        )

    def test_combined_filters_respect_year_and_modality(self) -> None:
        filtered = apply_filters(self.data, anio=2021, modalidad="CHOQUE")
        self.assertGreater(len(filtered), 0)
        self.assertTrue(all(row.get("anio") == 2021 for row in filtered))
        self.assertTrue(
            all(row.get("modalidad_norm") == "CHOQUE" for row in filtered)
        )

    def test_kpis_are_consistent_with_filtered_records(self) -> None:
        filtered = apply_filters(self.data, departamento="AREQUIPA")
        kpis = get_kpis(filtered)
        self.assertEqual(kpis["total_accidentes"], len(filtered))
        self.assertGreaterEqual(kpis["total_fallecidos"], 0)
        self.assertGreaterEqual(kpis["total_heridos"], 0)

    def test_unknown_department_returns_empty_result(self) -> None:
        filtered = apply_filters(self.data, departamento="DEPARTAMENTO INEXISTENTE")
        self.assertEqual(filtered, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
