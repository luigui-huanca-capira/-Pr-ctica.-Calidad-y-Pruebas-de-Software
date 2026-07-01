from pydantic import BaseModel, Field
from typing import Optional


class AccidentFilterParams(BaseModel):
    anio: Optional[int] = Field(default=None, ge=2020, le=2021)
    departamento: Optional[str] = None
    modalidad: Optional[str] = None
    limite: int = Field(default=200, ge=1, le=10000)
