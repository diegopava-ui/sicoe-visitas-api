from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    pagina: int = Query(
        default=1,
        ge=1,
        description="Número de página",
    )

    limite: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Cantidad de registros por página",
    )

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.limite