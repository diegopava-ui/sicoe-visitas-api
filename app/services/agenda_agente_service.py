import calendar
import re
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.services.calendario_service import listar_eventos
from app.schemas.agenda_agente import (
    AgendaAgenteRespuesta,
    AgendaAgenteVisita,
)


ZONA_COLOMBIA = ZoneInfo("America/Bogota")

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return re.sub(r"\s+", " ", texto)


def _codigo_visita(visita_id: int) -> str:
    return f"VIS-{visita_id:06d}"


def _valor_ubicacion(
    ubicacion,
    atributo: str,
    predeterminado=None,
):
    return getattr(
        ubicacion,
        atributo,
        predeterminado,
    )


def _convertir_visita(evento) -> AgendaAgenteVisita:
    ubicacion = evento.ubicacion

    latitud = _valor_ubicacion(
        ubicacion,
        "latitud",
    )
    longitud = _valor_ubicacion(
        ubicacion,
        "longitud",
    )

    return AgendaAgenteVisita(
        id=evento.id,
        codigo=_codigo_visita(evento.id),
        fecha=evento.fecha_visita,
        hora_inicio=evento.hora_inicio,
        hora_fin=evento.hora_fin,
        empresa=evento.cliente.empresa,
        servicio=evento.servicio,
        tipo_visita=evento.tipo_visita,
        estado=evento.estado,
        ciudad=ubicacion.ciudad,
        departamento=ubicacion.departamento,
        ubicacion_validada=bool(
            _valor_ubicacion(
                ubicacion,
                "ubicacion_validada",
                False,
            )
        ),
        tiene_coordenadas=(
            latitud is not None
            and longitud is not None
        ),
    )


def _ordenar_eventos(eventos: list) -> list:
    return sorted(
        eventos,
        key=lambda evento: (
            evento.fecha_visita,
            evento.hora_inicio is None,
            evento.hora_inicio,
            evento.id,
        ),
    )


def _hora_texto(valor) -> str:
    if valor is None:
        return "sin hora definida"

    return valor.strftime("%H:%M")


def _ubicacion_texto(visita: AgendaAgenteVisita) -> str:
    partes = [
        visita.ciudad,
        visita.departamento,
    ]

    ubicacion = ", ".join(
        parte
        for parte in partes
        if parte
    )

    return ubicacion or "sin ubicación registrada"


def _resumen_visitas(
    visitas: list[AgendaAgenteVisita],
) -> str:
    if not visitas:
        return "No tienes visitas programadas para ese período."

    lineas: list[str] = []

    for visita in visitas:
        lineas.append(
            (
                f"{_hora_texto(visita.hora_inicio)} "
                f"{visita.codigo}, "
                f"{visita.empresa}, "
                f"{_ubicacion_texto(visita)}."
            )
        )

    if len(visitas) == 1:
        encabezado = "Tienes 1 visita: "
    else:
        encabezado = (
            f"Tienes {len(visitas)} visitas: "
        )

    return encabezado + " ".join(lineas)


def _inicio_fin_semana(
    referencia: date,
) -> tuple[date, date]:
    inicio = referencia - timedelta(
        days=referencia.weekday()
    )
    fin = inicio + timedelta(days=6)

    return inicio, fin


def _inicio_fin_mes(
    anio: int,
    mes: int,
) -> tuple[date, date]:
    ultimo = calendar.monthrange(anio, mes)[1]
    return (
        date(anio, mes, 1),
        date(anio, mes, ultimo),
    )


def _mes_explicito(
    texto: str,
    hoy: date,
) -> tuple[int, int] | None:
    """
    Extrae un mes escrito en español y resuelve el año.

    Si no se escribe el año, se interpreta el próximo
    mes con ese nombre dentro de una agenda futura.
    Para el mes actual se conserva el año actual.
    """

    for nombre, numero in MESES.items():
        if not re.search(rf"\b{nombre}\b", texto):
            continue

        coincidencia_anio = re.search(
            rf"\b{nombre}\s+(20\d{{2}})\b",
            texto,
        )

        if coincidencia_anio:
            return numero, int(
                coincidencia_anio.group(1)
            )

        anio = hoy.year

        if numero < hoy.month:
            anio += 1

        return numero, anio

    return None


def _es_resto_mes(texto: str) -> bool:
    expresiones = (
        "resto de",
        "resto del mes",
        "resto de este mes",
        "lo que queda de",
        "lo que queda del mes",
        "lo que queda este mes",
        "de aqui a fin de mes",
        "hasta fin de mes",
    )

    return any(
        expresion in texto
        for expresion in expresiones
    )


def _respuesta_rango(
    db: Session,
    asesor_id: int,
    desde: date,
    hasta: date,
    intencion: str,
) -> AgendaAgenteRespuesta:
    eventos = _consultar(
        db,
        asesor_id,
        desde,
        hasta,
    )

    visitas = [
        _convertir_visita(evento)
        for evento in eventos
    ]

    return AgendaAgenteRespuesta(
        respuesta=_resumen_visitas(visitas),
        intencion=intencion,
        fecha_desde=desde,
        fecha_hasta=hasta,
        total_visitas=len(visitas),
        visitas=visitas,
    )


def _respuesta_periodo_no_interpretado() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Entendí que preguntas por tu agenda, pero no "
            "pude identificar con seguridad el período. "
            "Puedes preguntarme, por ejemplo: hoy, mañana, "
            "esta semana, este mes, el resto de agosto, "
            "septiembre o mi próxima visita."
        ),
        intencion="PERIODO_NO_INTERPRETADO",
        fuera_de_dominio=False,
    )


def _consultar(
    db: Session,
    asesor_id: int,
    desde: date,
    hasta: date,
) -> list:
    return _ordenar_eventos(
        listar_eventos(
            db=db,
            desde=desde,
            hasta=hasta,
            asesor_id=asesor_id,
        )
    )


def _respuesta_fuera_dominio() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Soy el Asistente de Agenda de SICOE. "
            "Puedo ayudarte únicamente con tus visitas, "
            "horarios, ubicaciones y actividades programadas."
        ),
        intencion="FUERA_DE_DOMINIO",
        fuera_de_dominio=True,
    )


def _respuesta_solo_mi_agenda() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Por seguridad solo puedo consultar "
            "tu propia agenda de visitas."
        ),
        intencion="OTRO_ASESOR_NO_AUTORIZADO",
        fuera_de_dominio=False,
    )


def _parece_consulta_otro_asesor(
    texto: str,
) -> bool:
    """
    Detecta intentos explícitos de consultar la agenda
    de otra persona.

    Ejemplos:
    - agenda de Natalia
    - visitas de Natalia
    - que visitas tiene Natalia hoy
    - que tiene Natalia manana
    """

    patrones = (
        r"\bagenda de [a-z][a-z\s]{1,60}\b",
        r"\bvisitas de [a-z][a-z\s]{1,60}\b",
        r"\bque visitas tiene [a-z][a-z\s]{1,60}(?: hoy| manana| esta semana)?\b",
        r"\bque tiene [a-z][a-z\s]{1,60}(?: hoy| manana| esta semana)?\b",
    )

    # Evitar falsos positivos sobre expresiones propias.
    referencias_propias = (
        "mi agenda",
        "mis visitas",
        "que visitas tengo",
        "que tengo hoy",
        "que tengo manana",
    )

    if any(
        referencia in texto
        for referencia in referencias_propias
    ):
        return False

    return any(
        re.search(patron, texto)
        for patron in patrones
    )


def _es_dominio_agenda(texto: str) -> bool:
    palabras = (
        "agenda",
        "visita",
        "visitas",
        "tengo hoy",
        "tengo manana",
        "tengo mañana",
        "proxima",
        "proximo",
        "siguiente",
        "horario",
        "ubicacion",
        "ubicación",
        "donde queda",
        "dónde queda",
        "a que hora",
        "qué hora",
        "termino hoy",
        "semana",
        "mes",
        "resto",
        "fin de mes",
        *MESES.keys(),
    )

    return any(
        palabra in texto
        for palabra in palabras
    )


def responder_pregunta_agenda(
    db: Session,
    usuario_actual: Usuario,
    pregunta: str,
) -> AgendaAgenteRespuesta:
    """
    Motor cerrado de Agenda.

    Regla crítica:
    - No acepta asesor_id desde request.
    - Siempre usa usuario_actual.asesor_id.
    - Por lo tanto no puede consultar otro asesor.
    """

    texto = _normalizar(pregunta)

    # Primero se aplica la política del dominio.
    # Así, incluso un usuario sin asesor asociado recibe
    # la respuesta de seguridad correcta si intenta
    # consultar a otra persona o salir del dominio Agenda.
    if _parece_consulta_otro_asesor(texto):
        return _respuesta_solo_mi_agenda()

    if not _es_dominio_agenda(texto):
        return _respuesta_fuera_dominio()

    # Solo después se valida si el usuario tiene una
    # agenda personal que pueda ser consultada.
    if usuario_actual.asesor_id is None:
        return AgendaAgenteRespuesta(
            respuesta=(
                "Tu usuario no tiene un asesor asociado. "
                "No puedo consultar una agenda personal "
                "hasta que se configure esa asociación."
            ),
            intencion="USUARIO_SIN_ASESOR",
        )

    hoy = datetime.now(
        ZONA_COLOMBIA
    ).date()

    asesor_id = usuario_actual.asesor_id

    # RANGOS MENSUALES EXPLÍCITOS.
    # Se procesan antes de HOY para evitar que una frase
    # válida como "resto de agosto" caiga por defecto
    # en la consulta del día actual.
    mes_explicito = _mes_explicito(texto, hoy)

    if mes_explicito is not None:
        mes, anio = mes_explicito
        inicio_mes, fin_mes = _inicio_fin_mes(
            anio,
            mes,
        )

        desde = inicio_mes

        if (
            _es_resto_mes(texto)
            and anio == hoy.year
            and mes == hoy.month
        ):
            desde = hoy

        intencion = (
            "AGENDA_RESTO_MES"
            if _es_resto_mes(texto)
            else "AGENDA_MES"
        )

        return _respuesta_rango(
            db,
            asesor_id,
            desde,
            fin_mes,
            intencion,
        )

    if (
        "proximo mes" in texto
        or "mes siguiente" in texto
    ):
        if hoy.month == 12:
            mes = 1
            anio = hoy.year + 1
        else:
            mes = hoy.month + 1
            anio = hoy.year

        desde, hasta = _inicio_fin_mes(
            anio,
            mes,
        )

        return _respuesta_rango(
            db,
            asesor_id,
            desde,
            hasta,
            "AGENDA_PROXIMO_MES",
        )

    if (
        "este mes" in texto
        or "mes actual" in texto
        or "resto del mes" in texto
        or "resto de este mes" in texto
        or "lo que queda del mes" in texto
        or "lo que queda este mes" in texto
        or "de aqui a fin de mes" in texto
        or "hasta fin de mes" in texto
    ):
        inicio_mes, fin_mes = _inicio_fin_mes(
            hoy.year,
            hoy.month,
        )

        desde = (
            hoy
            if _es_resto_mes(texto)
            else inicio_mes
        )

        intencion = (
            "AGENDA_RESTO_MES"
            if _es_resto_mes(texto)
            else "AGENDA_MES"
        )

        return _respuesta_rango(
            db,
            asesor_id,
            desde,
            fin_mes,
            intencion,
        )

    if "manana" in texto:
        objetivo = hoy + timedelta(days=1)

        eventos = _consultar(
            db,
            asesor_id,
            objetivo,
            objetivo,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        return AgendaAgenteRespuesta(
            respuesta=_resumen_visitas(visitas),
            intencion="AGENDA_MANANA",
            fecha_desde=objetivo,
            fecha_hasta=objetivo,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if (
        "esta semana" in texto
        or "semana" in texto
    ):
        desde, hasta = _inicio_fin_semana(hoy)

        eventos = _consultar(
            db,
            asesor_id,
            desde,
            hasta,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        return AgendaAgenteRespuesta(
            respuesta=_resumen_visitas(visitas),
            intencion="AGENDA_SEMANA",
            fecha_desde=desde,
            fecha_hasta=hasta,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if (
        "proxima" in texto
        or "proximo" in texto
        or "siguiente" in texto
    ):
        hasta = hoy + timedelta(days=60)

        eventos = _consultar(
            db,
            asesor_id,
            hoy,
            hasta,
        )

        futuras = [
            _convertir_visita(evento)
            for evento in eventos
            if evento.estado != "CANCELADA"
        ]

        if not futuras:
            return AgendaAgenteRespuesta(
                respuesta=(
                    "No encontré próximas visitas "
                    "en los siguientes 60 días."
                ),
                intencion="PROXIMA_VISITA",
                fecha_desde=hoy,
                fecha_hasta=hasta,
            )

        visita = futuras[0]

        if (
            "donde" in texto
            or "ubicacion" in texto
        ):
            respuesta = (
                f"Tu siguiente visita es "
                f"{visita.codigo} con "
                f"{visita.empresa}, "
                f"en {_ubicacion_texto(visita)}, "
                f"a las {_hora_texto(visita.hora_inicio)}."
            )
        else:
            respuesta = (
                f"Tu siguiente visita es "
                f"{visita.codigo} con "
                f"{visita.empresa}, el "
                f"{visita.fecha.strftime('%d/%m/%Y')} "
                f"a las {_hora_texto(visita.hora_inicio)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="PROXIMA_VISITA",
            fecha_desde=hoy,
            fecha_hasta=hasta,
            total_visitas=1,
            visitas=[visita],
        )

    # Si el usuario menciona una unidad temporal que todavía
    # no está soportada, no debemos responder falsamente con
    # la agenda de HOY. Es preferible pedir precisión.
    periodos_no_soportados = (
        "quincena",
        "trimestre",
        "semestre",
        "ano",
        "año",
        "fin de semana",
    )

    if any(
        periodo in texto
        for periodo in periodos_no_soportados
    ):
        return _respuesta_periodo_no_interpretado()

    # Consultas sobre HOY: por defecto dentro del dominio.
    eventos = _consultar(
        db,
        asesor_id,
        hoy,
        hoy,
    )

    visitas = [
        _convertir_visita(evento)
        for evento in eventos
    ]

    if "termino" in texto or "ultima" in texto:
        if not visitas:
            respuesta = (
                "No tienes visitas programadas para hoy."
            )
        else:
            ultima = visitas[-1]
            fin = (
                ultima.hora_fin
                or ultima.hora_inicio
            )
            respuesta = (
                f"Tu última visita de hoy es "
                f"{ultima.codigo} con "
                f"{ultima.empresa}. "
                f"Tu jornada de visitas termina "
                f"aproximadamente a las "
                f"{_hora_texto(fin)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="FIN_JORNADA_HOY",
            fecha_desde=hoy,
            fecha_hasta=hoy,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if "primera" in texto:
        if not visitas:
            respuesta = (
                "No tienes visitas programadas para hoy."
            )
            seleccionadas: list[
                AgendaAgenteVisita
            ] = []
        else:
            primera = visitas[0]
            seleccionadas = [primera]
            respuesta = (
                f"Tu primera visita de hoy es "
                f"{primera.codigo} con "
                f"{primera.empresa} a las "
                f"{_hora_texto(primera.hora_inicio)}, "
                f"en {_ubicacion_texto(primera)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="PRIMERA_VISITA_HOY",
            fecha_desde=hoy,
            fecha_hasta=hoy,
            total_visitas=len(seleccionadas),
            visitas=seleccionadas,
        )

    return AgendaAgenteRespuesta(
        respuesta=_resumen_visitas(visitas),
        intencion="AGENDA_HOY",
        fecha_desde=hoy,
        fecha_hasta=hoy,
        total_visitas=len(visitas),
        visitas=visitas,
    )
