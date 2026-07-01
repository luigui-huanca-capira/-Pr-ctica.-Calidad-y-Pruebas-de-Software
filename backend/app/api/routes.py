from fastapi import APIRouter, HTTPException, Query

from app.models.filters import AccidentFilterParams
from app.services.data_service import (
    apply_filters,
    get_by_departamento,
    get_by_modalidad,
    get_kpis,
    get_monthly_series,
    get_table_records,
    get_temporal_heatmap,
    load_data,
)

router = APIRouter(prefix="/api", tags=["Accidentes SUTRAN"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/filters/options")
def filter_options():
    data = load_data()
    if not data:
        return {"anios": [], "departamentos": [], "modalidades": []}

    anios = sorted(set([r.get("anio") for r in data if r.get("anio") is not None]))
    departamentos = sorted(set([r.get("departamento_canonico") for r in data if r.get("departamento_canonico")]))
    modalidades = sorted(set([str(r.get("modalidad", "")).strip() for r in data if str(r.get("modalidad", "")).strip()]))

    return {
        "anios": anios,
        "departamentos": departamentos,
        "modalidades": modalidades,
    }


@router.get("/dashboard/summary")
def dashboard_summary(
    anio: int | None = Query(default=None),
    departamento: str | None = Query(default=None),
    modalidad: str | None = Query(default=None),
):
    params = AccidentFilterParams(
        anio=anio,
        departamento=departamento,
        modalidad=modalidad,
        limite=200,
    )

    data = load_data()
    if not data:
        raise HTTPException(status_code=404, detail="No se encontró data cargada en backend/data/accidentes_2020_2021.csv")

    filtered = apply_filters(
        data,
        anio=params.anio,
        departamento=params.departamento,
        modalidad=params.modalidad,
    )

    return {
        "filtros": params.model_dump(),
        "kpis": get_kpis(filtered),
        "series_mensual": get_monthly_series(filtered),
        "por_departamento": get_by_departamento(filtered),
        "por_modalidad": get_by_modalidad(filtered),
        "heatmap_temporal": get_temporal_heatmap(filtered),
    }


@router.get("/accidentes")
def accidentes(
    anio: int | None = Query(default=None),
    departamento: str | None = Query(default=None),
    modalidad: str | None = Query(default=None),
    limite: int = Query(default=200, ge=1, le=10000),
):
    params = AccidentFilterParams(
        anio=anio,
        departamento=departamento,
        modalidad=modalidad,
        limite=limite,
    )

    data = load_data()
    if not data:
        raise HTTPException(status_code=404, detail="No se encontró data cargada en backend/data/accidentes_2020_2021.csv")

    filtered = apply_filters(
        data,
        anio=params.anio,
        departamento=params.departamento,
        modalidad=params.modalidad,
    )

    return {
        "total_filtrado": int(len(filtered)),
        "registros": get_table_records(filtered, limite=params.limite),
    }
