"""Autorización Service Desk evaluada siempre en servidor.

Orden: autenticado y activo → CONSULTA bloquea toda escritura (aunque tenga
membresías) → capacidades efectivas en la cola → propiedad/estado del ticket.
Denegación por defecto.
"""

from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q

from accounts.models import Usuario
from .models import AsignacionRolSD, MembresiaCola


class Capacidad(models.TextChoices):
    CONSULTAR = "CONSULTAR", "Consultar"
    ATENDER = "ATENDER", "Atender"
    TRANSFERIR = "TRANSFERIR", "Transferir"
    APROBAR = "APROBAR", "Aprobar"
    ADMINISTRAR = "ADMINISTRAR", "Administrar"


OPERATIVAS = frozenset({
    Capacidad.ATENDER, Capacidad.TRANSFERIR, Capacidad.APROBAR, Capacidad.ADMINISTRAR,
})
BANDERAS = {
    "puede_consultar": Capacidad.CONSULTAR,
    "puede_atender": Capacidad.ATENDER,
    "puede_transferir": Capacidad.TRANSFERIR,
    "puede_aprobar": Capacidad.APROBAR,
    "puede_administrar": Capacidad.ADMINISTRAR,
}


def habilitado(usuario):
    return bool(
        usuario is not None and usuario.is_authenticated and usuario.is_active
        and usuario.rol in Usuario.Rol.values
    )


def puede_escribir(usuario):
    return habilitado(usuario) and usuario.rol != Usuario.Rol.CONSULTA


def roles_sd(usuario):
    if not habilitado(usuario):
        return set()
    return set(AsignacionRolSD.objects.filter(usuario_id=usuario.pk, activo=True)
               .values_list("rol", flat=True))


def capacidades(usuario, cola):
    if not habilitado(usuario):
        return frozenset()
    caps = set()
    filas = MembresiaCola.objects.filter(cola_id=cola.pk, activo=True).filter(
        Q(usuario_id=usuario.pk) | Q(rol__in=roles_sd(usuario))
    ).values(*BANDERAS)
    for fila in filas:
        caps |= {cap for bandera, cap in BANDERAS.items() if fila[bandera]}
    if caps & OPERATIVAS:
        caps.add(Capacidad.CONSULTAR)
    if usuario.rol == Usuario.Rol.ADMINISTRADOR:
        caps |= {Capacidad.CONSULTAR, Capacidad.ADMINISTRAR}
    if usuario.rol == Usuario.Rol.CONSULTA:
        caps &= {Capacidad.CONSULTAR}  # La membresía nunca eleva a CONSULTA.
    if not cola.estado:
        caps -= {Capacidad.ATENDER, Capacidad.TRANSFERIR, Capacidad.APROBAR}
    return frozenset(caps)


def puede_crear_tickets(usuario):
    return puede_escribir(usuario) and (
        usuario.rol == Usuario.Rol.ADMINISTRADOR or bool(roles_sd(usuario))
    )


def es_solicitante(usuario, ticket):
    return habilitado(usuario) and usuario.pk in {ticket.solicitante_id, ticket.creador_id}


def puede_ver(usuario, ticket):
    return es_solicitante(usuario, ticket) or (
        Capacidad.CONSULTAR in capacidades(usuario, ticket.cola)
    )


def puede_ver_internas(usuario, ticket):
    return puede_escribir(usuario) and bool(capacidades(usuario, ticket.cola) & OPERATIVAS)


def exigir(condicion, mensaje="No autorizado."):
    if not condicion:
        raise PermissionDenied(mensaje)


def exigir_capacidad(usuario, ticket, *requeridas):
    """Exige al menos una de las capacidades y bloquea a CONSULTA."""
    exigir(puede_escribir(usuario), "La cuenta es de solo lectura.")
    exigir(capacidades(usuario, ticket.cola) & set(requeridas),
           f"Se requiere capacidad {' o '.join(requeridas)} en la cola.")
