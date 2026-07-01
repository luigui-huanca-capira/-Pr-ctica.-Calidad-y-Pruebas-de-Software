from __future__ import annotations

import time
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


ROOT_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT_DIR / "evidencias" / "actividad_6"
DOWNLOAD_DIR = EVIDENCE_DIR / "descargas"
HOME_URL = "http://127.0.0.1:5500/frontend/index.html"
DASHBOARD_URL = "http://127.0.0.1:5500/frontend/prototipo_vialseg.html"


class SeleniumFunctionalTests(unittest.TestCase):
    """Pruebas funcionales de extremo a extremo ejecutadas en Chrome."""

    @classmethod
    def setUpClass(cls) -> None:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1100")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(DOWNLOAD_DIR.resolve()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        cls.driver = webdriver.Chrome(options=options)
        cls.driver.set_page_load_timeout(40)
        cls.wait = WebDriverWait(cls.driver, 30)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.driver.quit()

    def setUp(self) -> None:
        self.driver.get(DASHBOARD_URL)
        self._wait_for_dashboard()

    def _wait_for_dashboard(self) -> None:
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "kpi-accidentes").text
            not in ("", "—")
        )
        self.wait.until(
            lambda driver: any(
                option.text == "CALLAO"
                for option in Select(
                    driver.find_element(By.ID, "f-departamento")
                ).options
            )
        )

    def _select_callao(self) -> None:
        Select(self.driver.find_element(By.ID, "f-departamento")).select_by_visible_text(
            "CALLAO"
        )
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "kpi-accidentes").text == "6"
        )
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "src-registros").text == "6"
        )

    def _capture(self, filename: str) -> None:
        saved = self.driver.save_screenshot(str(EVIDENCE_DIR / filename))
        self.assertTrue(saved)

    def test_01_home_page_loads_real_indicators(self) -> None:
        self.driver.get(HOME_URL)
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "kpiAccidentes").text
            not in ("", "—")
        )
        self.assertIn("SUTRAN VIAL", self.driver.title)
        self.assertEqual(self.driver.find_element(By.ID, "statDep").text, "25")
        self._capture("01_pagina_principal.png")

    def test_02_navigation_opens_analytical_dashboard(self) -> None:
        self.driver.get(HOME_URL)
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-cta"))).click()
        self.wait.until(EC.url_contains("prototipo_vialseg.html"))
        self._wait_for_dashboard()
        self.assertIn("VIALSEG", self.driver.title)
        self._capture("02_dashboard_resumen.png")

    def test_03_callao_filter_colors_only_one_department(self) -> None:
        self._select_callao()
        self.driver.find_element(By.ID, "tab-mapa").click()
        self.wait.until(
            lambda driver: len(
                driver.find_elements(
                    By.CSS_SELECTOR, "#mapHolder .leaflet-overlay-pane path"
                )
            )
            >= 26
        )

        colored_paths = self.driver.execute_script(
            """
            return [...document.querySelectorAll('#mapHolder .leaflet-overlay-pane path')]
              .filter(path => Number(path.getAttribute('fill-opacity') || 0) > 0.1)
              .length;
            """
        )
        self.assertEqual(colored_paths, 1)
        self._capture("03_filtro_callao_mapa.png")

    def test_04_callao_table_contains_six_consistent_records(self) -> None:
        self._select_callao()
        self.driver.find_element(By.ID, "tab-datos").click()
        rows = self.wait.until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, "#tbody-registros tr")
            if len(driver.find_elements(By.CSS_SELECTOR, "#tbody-registros tr")) == 6
            else False
        )
        departments = [
            row.find_elements(By.TAG_NAME, "td")[1].text for row in rows
        ]
        self.assertEqual(departments, ["CALLAO"] * 6)
        self._capture("04_tabla_callao.png")

    def test_05_year_and_modality_filters_are_combined(self) -> None:
        initial_total = self.driver.find_element(By.ID, "kpi-accidentes").text
        Select(self.driver.find_element(By.ID, "f-anio")).select_by_value("2021")
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "kpi-accidentes").text
            != initial_total
        )
        Select(self.driver.find_element(By.ID, "f-modalidad")).select_by_visible_text(
            "CHOQUE"
        )
        self.driver.find_element(By.ID, "tab-datos").click()
        modalities = self.wait.until(
            lambda driver: cells
            if (
                (cells := driver.find_elements(
                    By.CSS_SELECTOR, "#tbody-registros td:nth-child(5)"
                ))
                and all(cell.text == "CHOQUE" for cell in cells)
            )
            else False
        )
        self.assertTrue(modalities)
        self.assertTrue(all(cell.text == "CHOQUE" for cell in modalities))

    def test_06_report_preview_and_excel_export(self) -> None:
        for previous in DOWNLOAD_DIR.glob("reporte-sutran-*.xls"):
            previous.unlink()

        self._select_callao()
        self.driver.find_element(By.ID, "tab-reportes").click()
        preview = self.wait.until(
            EC.visibility_of_element_located((By.ID, "report-preview"))
        )
        self.assertIn("CALLAO", preview.text)
        self.assertIn("6", preview.text)
        self._capture("05_reporte_callao.png")

        self.driver.find_element(By.ID, "btn-download-report").click()
        deadline = time.time() + 15
        downloaded = []
        while time.time() < deadline:
            downloaded = list(DOWNLOAD_DIR.glob("reporte-sutran-*.xls"))
            if downloaded and downloaded[0].stat().st_size > 0:
                break
            time.sleep(0.25)

        self.assertEqual(len(downloaded), 1)
        self.assertGreater(downloaded[0].stat().st_size, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
