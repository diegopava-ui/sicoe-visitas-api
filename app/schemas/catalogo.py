from pydantic import BaseModel


class DepartamentoRespuesta(BaseModel):
    codigo: str
    nombre: str


class MunicipioRespuesta(BaseModel):
    codigo: str
    nombre: str
    departamento_codigo: str


class CatalogoUbicacionMeta(BaseModel):
    departamentos_incluidos: int
    departamentos_totales_colombia: int
    municipios_incluidos: int
