from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "accidentes_2020_2021.csv"

REMOTE_DATASET_URL = "https://www.datosabiertos.gob.pe/sites/default/files/Accidentes%20de%20tr%C3%A1nsito%20en%20carreteras-2020-2021-Sutran.csv"

API_PREFIX = "/api"
APP_NAME = "SUTRAN Accidentes API"
APP_VERSION = "1.0.0"
