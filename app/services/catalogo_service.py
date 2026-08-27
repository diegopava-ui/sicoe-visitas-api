import json
from functools import lru_cache
from pathlib import Path

from app.schemas.catalogo import (
    DepartamentoRespuesta,
    MunicipioRespuesta,
)

_RUTA_CATALOGO = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "divipola.json"
)


@lru_cache(maxsize=1)
def _cargar_catalogo() -> dict:
    with open(_RUTA_CATALOGO, encoding="utf-8") as archivo:
        return json.load(archivo)


def listar_departamentos() -> list[DepartamentoRespuesta]:
    datos = _cargar_catalogo()

    return [
        DepartamentoRespuesta(**dep)
        for dep in datos["departamentos"]
    ]


def listar_municipios(
    departamento_codigo: str | None = None,
) -> list[MunicipioRespuesta]:
    datos = _cargar_catalogo()

    municipios = datos["municipios"]

    if departamento_codigo:
        municipios = [
            m
            for m in municipios
            if m["departamento_codigo"] == departamento_codigo
        ]

    return [
        MunicipioRespuesta(**mun)
        for mun in municipios
    ]


def obtener_metadata() -> dict:
    datos = _cargar_catalogo()
    return datos["meta"]
