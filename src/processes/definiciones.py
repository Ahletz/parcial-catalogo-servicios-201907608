"""Siete flujos con estados, actores, entradas, salidas y evidencias propios."""

from . import guardas as g
from .catalogo import CategoriaEvento as E, Proceso
from .motor import Actor, DefinicionProceso, Transicion as T

APROBAR = Actor.APROBAR
SOLICITANTE = Actor.SOLICITANTE
AMBOS = Actor.SOLICITANTE_O_ATENDER

NUEVOS_SERVICIOS = DefinicionProceso(
    proceso=Proceso.NUEVOS_SERVICIOS,
    detalle="DetalleNuevoServicio",
    estado_inicial="SOLICITADO",
    estados=("SOLICITADO", "ANALISIS", "PENDIENTE_APROBACION", "APROBADO", "RECHAZADO",
             "IMPLEMENTACION", "CERRADO"),
    campos_entrada=("necesidad",),
    campos_editables=("viabilidad", "modo_resultado", "servicio_resultante",
                      "propuesta_codigo", "propuesta_nombre", "propuesta_nivel1",
                      "propuesta_seccion", "propuesta_descripcion"),
    entrada=(g.requiere("necesidad"),),
    estados_con_aprobacion=frozenset({"APROBADO", "IMPLEMENTACION"}),
    transiciones=(
        T("analizar", ("SOLICITADO",), "ANALISIS"),
        T("enviar_aprobacion", ("ANALISIS",), "PENDIENTE_APROBACION",
          campos=("viabilidad", "modo_resultado", "servicio_resultante", "propuesta_codigo",
                  "propuesta_nombre", "propuesta_nivel1", "propuesta_seccion",
                  "propuesta_descripcion"),
          guardas=(g.requiere("viabilidad"), g.nuevo_servicio_sin_duplicado)),
        T("aprobar", ("PENDIENTE_APROBACION",), "APROBADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="APROBADA"),
        T("rechazar", ("PENDIENTE_APROBACION",), "RECHAZADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="RECHAZADA", requiere_motivo=True),
        T("implementar", ("APROBADO",), "IMPLEMENTACION", guardas=(g.aprobacion_vigente,)),
        T("cerrar", ("IMPLEMENTACION",), "CERRADO", campos=("resolucion",),
          guardas=(g.aprobacion_vigente, g.requiere("ticket.resolucion")),
          efectos=(g.crear_o_vincular_servicio,)),
        T("cerrar", ("RECHAZADO",), "CERRADO", campos=("resolucion",),
          guardas=(g.requiere("ticket.resolucion"),)),
    ),
)

CAMBIOS = DefinicionProceso(
    proceso=Proceso.CAMBIOS,
    detalle="DetalleCambio",
    estado_inicial="SOLICITADO",
    estados=("SOLICITADO", "EVALUACION", "PENDIENTE_APROBACION", "APROBADO", "RECHAZADO",
             "PLANIFICADO", "EJECUCION", "VALIDACION", "REVERSION", "CERRADO"),
    campos_editables=("impacto", "riesgo", "analisis_impacto", "plan_pruebas",
                      "plan_reversion", "fecha_planificada"),
    estados_con_aprobacion=frozenset({"APROBADO", "PLANIFICADO", "EJECUCION"}),
    estados_resolucion=frozenset(),
    transiciones=(
        T("evaluar", ("SOLICITADO",), "EVALUACION", guardas=(g.ci_o_justificacion,)),
        T("enviar_aprobacion", ("EVALUACION",), "PENDIENTE_APROBACION",
          campos=("impacto", "riesgo", "analisis_impacto", "plan_pruebas", "plan_reversion"),
          guardas=(g.ci_o_justificacion,
                   g.requiere("impacto", "riesgo", "plan_pruebas", "plan_reversion"))),
        T("aprobar", ("PENDIENTE_APROBACION",), "APROBADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="APROBADA"),
        T("rechazar", ("PENDIENTE_APROBACION",), "RECHAZADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="RECHAZADA", requiere_motivo=True),
        T("planificar", ("APROBADO",), "PLANIFICADO", campos=("fecha_planificada",),
          guardas=(g.aprobacion_vigente, g.requiere("fecha_planificada"))),
        T("reevaluar", ("APROBADO", "PLANIFICADO"), "EVALUACION", requiere_motivo=True),
        # Regla obligatoria: nunca ejecutar sin aprobación vigente del contenido.
        T("ejecutar", ("PLANIFICADO",), "EJECUCION", guardas=(g.aprobacion_vigente,)),
        T("validar", ("EJECUCION",), "VALIDACION",
          campos=("resultado_validacion", "exitoso"),
          guardas=(g.requiere("resultado_validacion", "exitoso"),)),
        T("revertir", ("VALIDACION",), "REVERSION", campos=("evidencia_reversion",),
          guardas=(g.requiere("evidencia_reversion"),), requiere_motivo=True),
        T("cerrar", ("VALIDACION", "REVERSION", "RECHAZADO"), "CERRADO",
          campos=("resolucion",), guardas=(g.requiere("ticket.resolucion"),)),
    ),
)

INCIDENTES = DefinicionProceso(
    proceso=Proceso.INCIDENTES,
    detalle="DetalleIncidente",
    estado_inicial="REGISTRADO",
    estados=("REGISTRADO", "CLASIFICADO", "DIAGNOSTICO", "ATENCION", "ESCALADO",
             "RECUPERADO", "RESUELTO", "CERRADO"),
    campos_entrada=("afectacion", "duracion_estimada"),
    campos_editables=("afectacion", "duracion_estimada", "duracion_real", "redundancia",
                      "diagnostico"),
    estados_resolucion=frozenset({"RESUELTO"}),
    transiciones=(
        T("clasificar", ("REGISTRADO",), "CLASIFICADO",
          campos=("afectacion", "categoria", "motivo_categoria", "duracion_estimada",
                  "redundancia", "prioridad"),
          guardas=(g.categoria_incidente, g.interrupcion_declarada)),
        T("diagnosticar", ("CLASIFICADO", "ESCALADO"), "DIAGNOSTICO"),
        T("atender", ("DIAGNOSTICO",), "ATENCION", campos=("diagnostico",),
          guardas=(g.requiere("diagnostico"),)),
        T("escalar", ("ATENCION",), "ESCALADO", campos=("nivel_escalamiento",),
          guardas=(g.requiere("nivel_escalamiento"),), requiere_motivo=True),
        T("recuperar", ("ATENCION",), "RECUPERADO"),
        T("resolver", ("RECUPERADO",), "RESUELTO",
          campos=("solucion_aplicada", "duracion_real", "resolucion"),
          guardas=(g.requiere("solucion_aplicada", "ticket.resolucion"),)),
        T("reabrir", ("RESUELTO",), "ATENCION", actor=AMBOS, requiere_motivo=True),
        T("cerrar", ("RESUELTO",), "CERRADO", actor=AMBOS, guardas=(g.ci_o_justificacion,)),
    ),
)

EVENTOS = DefinicionProceso(
    proceso=Proceso.EVENTOS,
    detalle="DetalleEvento",
    estado_inicial="REGISTRADO",
    estados=("REGISTRADO", "CLASIFICADO", "EVALUADO", "RESPONDIDO", "CERRADO"),
    campos_entrada=("clave_evento", "fuente", "categoria"),
    entrada=(g.requiere("clave_evento"),),
    transiciones=(
        T("clasificar", ("REGISTRADO",), "CLASIFICADO", campos=("categoria",),
          guardas=(g.requiere("categoria"),)),
        # E0: registro únicamente.
        T("cerrar", ("CLASIFICADO",), "CERRADO", campos=("resolucion",),
          guardas=(g.categoria_evento(E.E0),)),
        T("evaluar", ("CLASIFICADO",), "EVALUADO", campos=("evaluacion",),
          guardas=(g.categoria_evento(E.E1, E.E2, E.E3), g.requiere("evaluacion"))),
        # E1: evaluación sin respuesta operativa obligatoria.
        T("cerrar", ("EVALUADO",), "CERRADO", campos=("resolucion",),
          guardas=(g.categoria_evento(E.E1),)),
        # E2/E3: respuesta = incidente creado o vinculado (idempotente).
        T("responder", ("EVALUADO",), "RESPONDIDO", campos=("respuesta",),
          guardas=(g.categoria_evento(E.E2, E.E3), g.incidente_vinculado)),
        T("cerrar", ("RESPONDIDO",), "CERRADO", campos=("resolucion",),
          guardas=(g.incidente_vinculado,)),
    ),
)

PROBLEMAS = DefinicionProceso(
    proceso=Proceso.PROBLEMAS,
    detalle="DetalleProblema",
    estado_inicial="REGISTRADO",
    estados=("REGISTRADO", "INVESTIGACION", "CAUSA_IDENTIFICADA", "ERROR_CONOCIDO",
             "SOLUCION_PLANIFICADA", "RESUELTO", "CERRADO"),
    campos_editables=("causa_raiz", "workaround", "solucion_definitiva",
                      "justificacion_sin_cambio"),
    estados_resolucion=frozenset({"RESUELTO"}),
    transiciones=(
        T("investigar", ("REGISTRADO",), "INVESTIGACION", guardas=(g.incidentes_relacionados,)),
        T("identificar_causa", ("INVESTIGACION",), "CAUSA_IDENTIFICADA",
          campos=("causa_raiz",), guardas=(g.requiere("causa_raiz"),)),
        T("registrar_error_conocido", ("CAUSA_IDENTIFICADA",), "ERROR_CONOCIDO",
          campos=("workaround",), guardas=(g.requiere("workaround"),)),
        T("planificar_solucion", ("CAUSA_IDENTIFICADA", "ERROR_CONOCIDO"),
          "SOLUCION_PLANIFICADA", campos=("solucion_definitiva", "justificacion_sin_cambio"),
          guardas=(g.requiere("solucion_definitiva"), g.cambio_o_justificacion)),
        T("resolver", ("SOLUCION_PLANIFICADA",), "RESUELTO", campos=("resolucion",),
          guardas=(g.requiere("ticket.resolucion"), g.cambio_o_justificacion)),
        T("reabrir", ("RESUELTO",), "INVESTIGACION", requiere_motivo=True),
        T("cerrar", ("RESUELTO",), "CERRADO"),
    ),
)

ACCESOS = DefinicionProceso(
    proceso=Proceso.ACCESOS,
    detalle="DetalleAcceso",
    estado_inicial="SOLICITADO",
    estados=("SOLICITADO", "PENDIENTE_APROBACION", "APROBADO", "RECHAZADO",
             "PROVISIONADO", "REVOCADO", "VALIDADO", "CERRADO"),
    campos_entrada=("beneficiario", "recurso", "permiso", "accion"),
    entrada=(g.requiere("beneficiario", "recurso", "permiso", "accion"),),
    estados_con_aprobacion=frozenset({"APROBADO", "PROVISIONADO", "REVOCADO"}),
    transiciones=(
        T("enviar_aprobacion", ("SOLICITADO",), "PENDIENTE_APROBACION",
          guardas=(g.requiere("beneficiario", "recurso", "permiso", "accion"),)),
        # Regla obligatoria: el solicitante no puede autoaprobarse.
        T("aprobar", ("PENDIENTE_APROBACION",), "APROBADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="APROBADA"),
        T("rechazar", ("PENDIENTE_APROBACION",), "RECHAZADO", actor=APROBAR,
          guardas=(g.aprobador_distinto,), decision="RECHAZADA", requiere_motivo=True),
        T("provisionar", ("APROBADO",), "PROVISIONADO", campos=("evidencia_ejecucion",),
          guardas=(g.aprobacion_vigente, g.accion_acceso("PROVISION"),
                   g.requiere("evidencia_ejecucion"))),
        T("revocar", ("APROBADO",), "REVOCADO", campos=("evidencia_ejecucion",),
          guardas=(g.aprobacion_vigente, g.accion_acceso("REVOCACION"),
                   g.requiere("evidencia_ejecucion"))),
        T("validar", ("PROVISIONADO", "REVOCADO"), "VALIDADO",
          campos=("resultado_validacion",), guardas=(g.requiere("resultado_validacion"),)),
        T("cerrar", ("VALIDADO", "RECHAZADO"), "CERRADO", campos=("resolucion",),
          guardas=(g.requiere("ticket.resolucion"),)),
    ),
)

SERVICIOS_TECNOLOGIA = DefinicionProceso(
    proceso=Proceso.SERVICIOS_TECNOLOGIA,
    detalle="DetalleServicioTecnologia",
    estado_inicial="SOLICITADO",
    estados=("SOLICITADO", "VALIDADO", "ASIGNADO", "EN_CUMPLIMIENTO", "CUMPLIDO",
             "CONFIRMADO", "CERRADO"),
    estados_resolucion=frozenset({"CUMPLIDO", "CONFIRMADO"}),
    transiciones=(
        T("validar", ("SOLICITADO",), "VALIDADO", campos=("resultado_validacion",),
          guardas=(g.servicio_activo, g.requiere("resultado_validacion"))),
        T("asignar", ("VALIDADO",), "ASIGNADO", guardas=(g.responsable_asignado,)),
        T("iniciar_cumplimiento", ("ASIGNADO",), "EN_CUMPLIMIENTO"),
        T("cumplir", ("EN_CUMPLIMIENTO",), "CUMPLIDO",
          campos=("detalle_cumplimiento", "resolucion"),
          guardas=(g.requiere("detalle_cumplimiento", "ticket.resolucion"),)),
        T("confirmar", ("CUMPLIDO",), "CONFIRMADO", actor=SOLICITANTE),
        T("rechazar_cumplimiento", ("CUMPLIDO",), "EN_CUMPLIMIENTO", actor=SOLICITANTE,
          requiere_motivo=True),
        T("cerrar", ("CONFIRMADO",), "CERRADO"),
    ),
)

DEFINICIONES = {
    d.proceso: d for d in (
        NUEVOS_SERVICIOS, CAMBIOS, INCIDENTES, EVENTOS, PROBLEMAS, ACCESOS,
        SERVICIOS_TECNOLOGIA,
    )
}
