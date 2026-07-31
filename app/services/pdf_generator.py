from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML


BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


class PDFGeneratorError(RuntimeError):
    """Error controlado durante la generación de un PDF."""


class PDFGenerator:
    """
    Motor reutilizable para generar documentos PDF
    a partir de plantillas HTML de Jinja2.
    """

    def __init__(
        self,
        templates_dir: Path = TEMPLATES_DIR,
        static_dir: Path = STATIC_DIR,
    ) -> None:
        self.templates_dir = templates_dir
        self.static_dir = static_dir

        self.environment = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def renderizar_html(
        self,
        plantilla: str,
        contexto: dict[str, Any],
    ) -> str:
        """
        Renderiza una plantilla HTML utilizando un contexto.
        """
        try:
            template = self.environment.get_template(plantilla)

        except TemplateNotFound as exc:
            raise PDFGeneratorError(
                f"No se encontró la plantilla: {plantilla}"
            ) from exc

        return template.render(
            **contexto,
            static_dir=self.static_dir.as_uri(),
        )

    def generar_pdf(
        self,
        plantilla: str,
        contexto: dict[str, Any],
    ) -> bytes:
        """
        Renderiza la plantilla y devuelve el PDF en memoria.
        """
        html_renderizado = self.renderizar_html(
            plantilla=plantilla,
            contexto=contexto,
        )

        try:
            return HTML(
                string=html_renderizado,
                base_url=str(BASE_DIR),
            ).write_pdf()

        except Exception as exc:
            raise PDFGeneratorError(
                "No fue posible convertir la plantilla HTML en PDF."
            ) from exc