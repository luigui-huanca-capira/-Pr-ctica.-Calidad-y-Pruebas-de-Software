import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from app.services.data_service import (
    apply_filters,
    get_by_departamento,
    get_by_modalidad,
    get_kpis,
    get_monthly_series,
    get_table_records,
    get_temporal_heatmap,
    load_data,
    refresh_remote_data,
)


def _json(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _parse_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/health":
            return _json(self, {"status": "ok", "service": "sutran-accidentes-api"})

        if path == "/api/data/refresh":
            ok = refresh_remote_data()
            load_data.cache_clear()
            reloaded = load_data()
            return _json(
                self,
                {
                    "actualizado": ok,
                    "registros_cargados": len(reloaded),
                },
                200 if ok else 500,
            )

        data = load_data()
        if not data:
            return _json(self, {"detail": "No se encontró data cargada en backend/data/accidentes_2020_2021.csv"}, 404)

        anio = _parse_int((qs.get("anio") or [None])[0], None)
        departamento = (qs.get("departamento") or [""])[0] or None
        modalidad = (qs.get("modalidad") or [""])[0] or None
        limite = _parse_int((qs.get("limite") or ["200"])[0], 200)

        if anio is not None and anio not in (2020, 2021):
            return _json(self, {"detail": "anio fuera de rango (2020-2021)"}, 422)

        if limite < 1 or limite > 10000:
            return _json(self, {"detail": "limite fuera de rango (1-10000)"}, 422)

        filtered = apply_filters(data, anio=anio, departamento=departamento, modalidad=modalidad)

        if path == "/api/filters/options":
            anios = sorted(set([r.get("anio") for r in data if r.get("anio") is not None]))
            deps = sorted(set([r.get("departamento_canonico") for r in data if r.get("departamento_canonico")]))
            mods = sorted(set([str(r.get("modalidad", "")).strip() for r in data if str(r.get("modalidad", "")).strip()]))
            return _json(self, {"anios": anios, "departamentos": deps, "modalidades": mods})

        if path == "/api/dashboard/summary":
            return _json(
                self,
                {
                    "filtros": {
                        "anio": anio,
                        "departamento": departamento,
                        "modalidad": modalidad,
                        "limite": 200,
                    },
                    "kpis": get_kpis(filtered),
                    "series_mensual": get_monthly_series(filtered),
                    "por_departamento": get_by_departamento(filtered),
                    "por_modalidad": get_by_modalidad(filtered),
                    "heatmap_temporal": get_temporal_heatmap(filtered),
                },
            )

        if path == "/api/accidentes":
            return _json(
                self,
                {
                    "total_filtrado": len(filtered),
                    "registros": get_table_records(filtered, limite=limite),
                },
            )

        return _json(self, {"detail": "Not Found"}, 404)


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    while True:
        try:
            server = HTTPServer((host, port), Handler)
            print(f"Servidor iniciado en http://{host}:{port}")
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido por el usuario.")
            break
        except OSError as e:
            print(f"Error al iniciar servidor en {host}:{port}: {e}")
            print("Reintentando en 2 segundos...")
            import time
            time.sleep(2)
