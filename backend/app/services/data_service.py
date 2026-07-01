import csv
import re
import subprocess
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from urllib.error import HTTPError, URLError
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import DATA_FILE, DATA_DIR, REMOTE_DATASET_URL
from app.core.logging_config import logger


COLUMN_ALIASES = {
    "fecha_corte": "fecha_corte",
    "fecha": "fecha",
    "hora": "hora",
    "departamento": "departamento",
    "provincia": "provincia",
    "distrito": "distrito",
    "carretera": "carretera",
    "codigo_via": "carretera",
    "codigo_va": "carretera",
    "kilometro": "kilometro",
    "km": "kilometro",
    "modalidad": "modalidad",
    "fallecidos": "fallecidos",
    "num_fallecidos": "fallecidos",
    "n_fallecidos": "fallecidos",
    "nro_fallecidos": "fallecidos",
    "heridos": "heridos",
    "num_heridos": "heridos",
    "n_heridos": "heridos",
    "nro_heridos": "heridos",
}

DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

OFFICIAL_DEPARTMENTS = {
    "AMAZONAS",
    "ANCASH",
    "APURIMAC",
    "AREQUIPA",
    "AYACUCHO",
    "CAJAMARCA",
    "CALLAO",
    "CUSCO",
    "HUANCAVELICA",
    "HUANUCO",
    "ICA",
    "JUNIN",
    "LA LIBERTAD",
    "LAMBAYEQUE",
    "LIMA",
    "LORETO",
    "MADRE DE DIOS",
    "MOQUEGUA",
    "PASCO",
    "PIURA",
    "PUNO",
    "SAN MARTIN",
    "TACNA",
    "TUMBES",
    "UCAYALI",
}

DEPARTMENT_ALIASES = {
    "ANCASH": "ANCASH",
    "APURIMAC": "APURIMAC",
    "CUZCO": "CUSCO",
    "HUANUCO": "HUANUCO",
    "JUNIN": "JUNIN",
    "LIMA METROPOLITANA": "LIMA",
    "LIMA PROVINCIAS": "LIMA",
    "SAN MARTIN": "SAN MARTIN",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().upper().split())


def _normalize_department_key(value: Any) -> str:
    text = _normalize_text(value)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _canonical_department(value: Any) -> str | None:
    key = _normalize_department_key(value)
    key = DEPARTMENT_ALIASES.get(key, key)
    if key in OFFICIAL_DEPARTMENTS:
        return key
    return None


def _normalize_modality(value: Any) -> str:
    text = _normalize_text(value)
    # normalización alineada al CSV real de SUTRAN (en español)
    aliases = {
        "CHOQUE": "CHOQUE",
        "COLISION": "CHOQUE",
        "COLISIÓN": "CHOQUE",
        "DESPISTE": "DESPISTE",
        "ATROPELLO": "ATROPELLO",
        "ESPECIAL": "ESPECIAL",
    }
    return aliases.get(text, text)


def _normalize_key(k: str) -> str:
    raw = str(k or "").strip()
    ascii_key = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", ascii_key).strip("_").lower()
    return COLUMN_ALIASES.get(cleaned, cleaned)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        class FallbackDialect(csv.excel):
            delimiter = ";" if sample.splitlines() and sample.splitlines()[0].count(";") else ","

        return FallbackDialect


def _parse_hour(h: str) -> int | None:
    if h is None:
        return None
    hs = str(h).strip()
    if not hs:
        return None
    part = hs.split(":")[0]
    try:
        n = int(part)
        if 0 <= n <= 23:
            return n
    except ValueError:
        return None
    return None


def _download_with_python_urllib() -> bool:
    req = urllib.request.Request(
        REMOTE_DATASET_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        content = response.read()

    if not content or len(content) < 1024:
        logger.error("Respuesta remota vacía o demasiado pequeña (%s bytes)", len(content) if content else 0)
        return False

    with open(DATA_FILE, "wb") as f:
        f.write(content)

    return True


def _download_with_powershell() -> bool:
    ps_script = (
        "$u='" + REMOTE_DATASET_URL + "';"
        "$h=@{'User-Agent'='Mozilla/5.0'};"
        "$r=Invoke-WebRequest -Uri $u -Headers $h -UseBasicParsing;"
        "$bytes=$r.RawContentStream.ToArray();"
        "[System.IO.File]::WriteAllBytes('" + str(DATA_FILE).replace("\\", "\\\\") + "', $bytes);"
    )
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        logger.error("PowerShell download falló: %s", result.stderr.strip())
        return False
    return True


def refresh_remote_data() -> bool:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Descargando dataset oficial desde %s", REMOTE_DATASET_URL)

        ok = False
        try:
            ok = _download_with_python_urllib()
        except (HTTPError, URLError, TimeoutError) as e:
            logger.warning("Descarga urllib falló (%s). Se intentará fallback PowerShell...", e)
        except Exception as e:
            logger.warning("Descarga urllib falló (%s). Se intentará fallback PowerShell...", e)

        if not ok:
            ok = _download_with_powershell()

        size = Path(DATA_FILE).stat().st_size if Path(DATA_FILE).exists() else 0
        logger.info("Resultado descarga. Tamaño final: %s bytes", size)
        return ok and size > 1024

    except Exception as e:
        logger.error("No se pudo descargar dataset remoto: %s", e)
        return False


@lru_cache(maxsize=1)
def load_data() -> list[dict[str, Any]]:
    data_path = Path(DATA_FILE)
    if not data_path.exists() or data_path.stat().st_size < 1024:
        logger.warning("Data local no válida o inexistente. Intentando descarga remota...")
        refresh_remote_data()

    if not data_path.exists():
        logger.warning("No se encontró el archivo de datos en %s", data_path)
        return []

    logger.info("Cargando datos desde %s", data_path)
    rows: list[dict[str, Any]] = []

    def read_with_encoding(enc: str) -> list[dict[str, Any]]:
        with open(data_path, "r", encoding=enc, newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            reader = csv.DictReader(f, dialect=_detect_dialect(sample))
            out = []
            for r in reader:
                normalized = {_normalize_key(k): v for k, v in r.items()}
                fecha_dt = _parse_date(normalized.get("fecha", ""))
                hora_num = _parse_hour(normalized.get("hora", ""))
                normalized["fecha_dt"] = fecha_dt
                normalized["anio"] = fecha_dt.year if fecha_dt else None
                normalized["mes"] = fecha_dt.month if fecha_dt else None
                normalized["dia_semana"] = DAYS_ES[fecha_dt.weekday()] if fecha_dt else None
                normalized["hora_num"] = hora_num
                canonical_dep = _canonical_department(normalized.get("departamento", ""))
                normalized["departamento_canonico"] = canonical_dep
                normalized["departamento_norm"] = canonical_dep or _normalize_text(normalized.get("departamento", ""))
                normalized["modalidad_norm"] = _normalize_modality(normalized.get("modalidad", ""))
                normalized["fallecidos"] = _to_int(normalized.get("fallecidos", 0))
                normalized["heridos"] = _to_int(normalized.get("heridos", 0))
                normalized["kilometro"] = _to_int(normalized.get("kilometro", 0))
                out.append(normalized)
            return out

    try:
        rows = read_with_encoding("utf-8-sig")
    except UnicodeDecodeError:
        try:
            rows = read_with_encoding("utf-8")
        except UnicodeDecodeError:
            rows = read_with_encoding("latin-1")

    logger.info("Datos cargados: %s filas", len(rows))
    return rows


def apply_filters(
    data: list[dict[str, Any]],
    anio: int | None = None,
    departamento: str | None = None,
    modalidad: str | None = None,
) -> list[dict[str, Any]]:
    filtered = data

    if anio is not None:
        filtered = [r for r in filtered if r.get("anio") == anio]

    if departamento:
        dep = _canonical_department(departamento) or _normalize_text(departamento)
        filtered = [r for r in filtered if r.get("departamento_norm", "") == dep]

    if modalidad:
        mod = _normalize_modality(modalidad)
        filtered = [r for r in filtered if r.get("modalidad_norm", "") == mod]

    return filtered


def get_kpis(filtered: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_accidentes": len(filtered),
        "total_fallecidos": sum(_to_int(r.get("fallecidos", 0)) for r in filtered),
        "total_heridos": sum(_to_int(r.get("heridos", 0)) for r in filtered),
    }


def get_monthly_series(filtered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    c = Counter()
    for r in filtered:
        dt = r.get("fecha_dt")
        if dt:
            c[f"{dt.year:04d}-{dt.month:02d}"] += 1
    return [{"periodo": k, "accidentes": c[k]} for k in sorted(c.keys())]


def get_by_departamento(filtered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    c = Counter()
    for r in filtered:
        dep = r.get("departamento_canonico") or _canonical_department(r.get("departamento", ""))
        if dep:
            c[dep] += 1
    return [{"departamento": k, "accidentes": v} for k, v in c.most_common()]


def get_by_modalidad(filtered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    c = Counter(str(r.get("modalidad", "")).strip() or "SIN_DATO" for r in filtered)
    return [{"modalidad": k, "accidentes": v} for k, v in c.most_common()]


def get_temporal_heatmap(filtered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grid = defaultdict(int)
    for r in filtered:
        dia = r.get("dia_semana")
        hora = r.get("hora_num")
        if dia in DAYS_ES and isinstance(hora, int):
            grid[(dia, hora)] += 1

    result = []
    for dia in DAYS_ES:
        for h in range(24):
            result.append({"dia_semana": dia, "hora": h, "accidentes": grid[(dia, h)]})
    return result


def get_table_records(filtered: list[dict[str, Any]], limite: int = 200) -> list[dict[str, Any]]:
    columns = [
        "fecha",
        "hora",
        "departamento",
        "provincia",
        "distrito",
        "carretera",
        "kilometro",
        "modalidad",
        "fallecidos",
        "heridos",
    ]
    out = []
    for r in filtered[:limite]:
        out.append({k: r.get(k, "") for k in columns})
    return out
