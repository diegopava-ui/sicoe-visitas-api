import json
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

# Nominatim (OpenStreetMap) exige un User-Agent identificable.
# Cambia el contacto por uno real de SICOE antes de producción.
_USER_AGENT = "SICOE-Visitas/1.0 (contacto@sicoe.com.co)"

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

_TIMEOUT_SEGUNDOS = 5


def _construir_consulta(
    direccion: str | None,
    ciudad: str | None,
    departamento: str | None,
) -> str | None:
    partes = [
        parte
        for parte in (direccion, ciudad, departamento, "Colombia")
        if parte and parte.strip()
    ]

    # Sin dirección no tiene sentido geocodificar (ciudad y
    # departamento solos son demasiado imprecisos para dar
    # coordenadas útiles a nivel de tercero).
    if not direccion or not direccion.strip():
        return None

    return ", ".join(partes)


def geocodificar(
    direccion: str | None,
    ciudad: str | None,
    departamento: str | None,
) -> tuple[Decimal | None, Decimal | None, str]:
    """
    Intenta obtener (latitud, longitud) a partir de una
    dirección usando Nominatim (OpenStreetMap).

    Nunca lanza una excepción hacia arriba: si algo falla
    (sin dirección, sin conexión, sin resultados, timeout),
    devuelve (None, None, "SIN_VALIDAR") para que la
    creación/edición del tercero nunca se bloquee por esto.
    """

    consulta = _construir_consulta(
        direccion,
        ciudad,
        departamento,
    )

    if consulta is None:
        return None, None, "SIN_VALIDAR"

    parametros = urllib.parse.urlencode(
        {
            "q": consulta,
            "format": "json",
            "limit": 1,
            "countrycodes": "co",
        }
    )

    url = f"{_NOMINATIM_URL}?{parametros}"

    peticion = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            peticion,
            timeout=_TIMEOUT_SEGUNDOS,
        ) as respuesta:
            cuerpo = respuesta.read()
            resultados = json.loads(cuerpo)
    except Exception:
        # Cualquier falla de red/timeout/parseo: degradar
        # con gracia, no romper la operación del usuario.
        return None, None, "SIN_VALIDAR"

    if not resultados:
        return None, None, "SIN_VALIDAR"

    primero = resultados[0]

    try:
        latitud = Decimal(str(primero["lat"]))
        longitud = Decimal(str(primero["lon"]))
    except (KeyError, InvalidOperation, TypeError):
        return None, None, "SIN_VALIDAR"

    return latitud, longitud, "GEOCODIFICADA"
