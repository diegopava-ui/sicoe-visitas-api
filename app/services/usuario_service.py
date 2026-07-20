from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.usuario_repository import (
    buscar_asesor_activo,
    buscar_usuario_por_asesor,
    buscar_usuario_por_email,
    buscar_usuario_por_username,
    guardar_usuario,
    listar_usuarios as listar_usuarios_repository,
    actualizar_usuario as actualizar_usuario_repository,
    buscar_usuario_por_id,
)
from app.schemas.usuario import UsuarioCrear
from app.security import generar_hash_password

from app.repositories.usuario_repository import (
    buscar_usuario_por_id,
)

from app.schemas.usuario import UsuarioActualizar, UsuarioCrear

def crear_usuario(
    db: Session,
    datos: UsuarioCrear,
) -> Usuario:
    username = datos.username.strip().lower()
    email = str(datos.email).strip().lower()

    if buscar_usuario_por_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está registrado",
        )

    if buscar_usuario_por_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado",
        )

    if datos.asesor_id is not None:
        asesor = buscar_asesor_activo(db, datos.asesor_id)

        if asesor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El asesor indicado no existe o está inactivo",
            )

        if buscar_usuario_por_asesor(db, datos.asesor_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El asesor ya tiene un usuario asociado",
            )

    usuario = Usuario(
        asesor_id=datos.asesor_id,
        username=username,
        email=email,
        password_hash=generar_hash_password(datos.password),
        rol=datos.rol,
        activo=datos.activo,
    )

    try:
        return guardar_usuario(db, usuario)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el usuario por datos duplicados",
        ) from exc
    
def obtener_usuarios(
    db: Session,
    buscar: str | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[Usuario]:
    return listar_usuarios_repository(
        db=db,
        buscar=buscar,
        limite=limite,
        offset=offset,
    )

def obtener_usuario(
    db: Session,
    usuario_id: int,
) -> Usuario:

    usuario = buscar_usuario_por_id(
        db,
        usuario_id,
    )

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return usuario    

def actualizar_usuario(
    db: Session,
    usuario_id: int,
    datos: UsuarioActualizar,
) -> Usuario:
    usuario = buscar_usuario_por_id(
        db,
        usuario_id,
    )

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    cambios = datos.model_dump(
        exclude_unset=True,
    )

    if "username" in cambios:
        nuevo_username = cambios["username"]

        usuario_existente = buscar_usuario_por_username(
            db,
            nuevo_username,
        )

        if (
            usuario_existente is not None
            and usuario_existente.id != usuario.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El nombre de usuario ya está registrado",
            )

    if "email" in cambios:
        nuevo_email = str(
            cambios["email"]
        ).strip().lower()

        cambios["email"] = nuevo_email

        usuario_existente = buscar_usuario_por_email(
            db,
            nuevo_email,
        )

        if (
            usuario_existente is not None
            and usuario_existente.id != usuario.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico ya está registrado",
            )

    if "asesor_id" in cambios:
        nuevo_asesor_id = cambios["asesor_id"]

        if nuevo_asesor_id is not None:
            asesor = buscar_asesor_activo(
                db,
                nuevo_asesor_id,
            )

            if asesor is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="El asesor indicado no existe o está inactivo",
                )

            usuario_existente = buscar_usuario_por_asesor(
                db,
                nuevo_asesor_id,
            )

            if (
                usuario_existente is not None
                and usuario_existente.id != usuario.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El asesor ya tiene un usuario asociado",
                )

    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)

    try:
        return actualizar_usuario_repository(
            db,
            usuario,
        )

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible actualizar el usuario",
        ) from exc