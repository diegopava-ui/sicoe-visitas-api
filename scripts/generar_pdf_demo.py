from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.database import SessionLocal
from app.services.visita_pdf_service import generar_pdf_visita


VISITA_ID = 6

OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / f"Informe_Visita_{VISITA_ID}.pdf"


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    db = SessionLocal()

    try:
        contenido_pdf = generar_pdf_visita(
            db=db,
            visita_id=VISITA_ID,
        )

        OUTPUT_FILE.write_bytes(contenido_pdf)

        print("")
        print("PDF generado correctamente")
        print(f"Ruta: {OUTPUT_FILE}")
        print("")

    finally:
        db.close()


if __name__ == "__main__":
    main()