from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ResultadoWhatsApp:
    exitoso: bool
    proveedor: str
    proveedor_message_id: str | None
    estado: str
    error: str | None = None


class WhatsAppService:
    """Adaptador inicial. En esta entrega solo simula; no consume servicios pagos."""

    proveedor = "SIMULADOR_SICOE"

    def enviar(self, telefono: str, mensaje: str) -> ResultadoWhatsApp:
        if not telefono:
            return ResultadoWhatsApp(
                exitoso=False,
                proveedor=self.proveedor,
                proveedor_message_id=None,
                estado="FALLIDA",
                error="No se recibió teléfono de destino.",
            )
        if not mensaje.strip():
            return ResultadoWhatsApp(
                exitoso=False,
                proveedor=self.proveedor,
                proveedor_message_id=None,
                estado="FALLIDA",
                error="El mensaje está vacío.",
            )
        return ResultadoWhatsApp(
            exitoso=True,
            proveedor=self.proveedor,
            proveedor_message_id=f"SIM-{uuid4().hex}",
            estado="SIMULADA",
        )
