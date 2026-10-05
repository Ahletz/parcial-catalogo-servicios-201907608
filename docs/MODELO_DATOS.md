# Modelo persistente inicial

Implementación de dominio: [config/domain.py](../src/config/domain.py).
Estado: modelo/migraciones implementados; controles y resultados se registran
en [FASE_MODELO.md](evidencias/FASE_MODELO.md). P06–P08 aprobadas: ver
[FASE_IMPORTACION.md](evidencias/FASE_IMPORTACION.md); otros nueve P pendientes.

## Relaciones

~~~mermaid
erDiagram
    Empresa ||--o{ Area : contiene
    Area ||--o{ Departamento : contiene
    Departamento ||--o{ Seccion : contiene
    Seccion ||--o{ Puesto : contiene
    Puesto ||--o{ Usuario : asigna
    ServicioNivel1 ||--o{ ServicioNivel2 : agrupa
    Seccion o|--o{ ServicioNivel2 : responsable
    Usuario o|--o{ ServicioNivel2 : responsable_opcional
    ClaseServicio o|--o{ ServicioNivel2 : clasifica
    CriticidadServicio o|--o{ ServicioNivel2 : clasifica
    TipoServicio o|--o{ ServicioNivel2 : clasifica
    EjecucionImportacion ||--o{ RegistroOrigen : registra
    EjecucionImportacion ||--o{ IncidenciaImportacion : observa
    RegistroOrigen o|--o{ IncidenciaImportacion : contextualiza
    ServicioNivel1 o|--o{ RegistroOrigen : procedencia
    ServicioNivel2 o|--o{ RegistroOrigen : procedencia
~~~

## Diccionario resumido

Todos los modelos tienen PK BigAutoField. Los de DomainModel añaden created_at,
updated_at y revision_manual; Usuario usa password/last_login de AbstractBaseUser
y compatibilidad de permisos de PermissionsMixin. No tiene columna empresa.

| Modelo / módulo | Campos de negocio y nulabilidad |
|---|---|
| Empresa / organization | codigo único (64), nombre (255), estado bool. |
| Area / organization | codigo, nombre, estado, empresa FK obligatoria. |
| Departamento / organization | codigo, nombre, estado, area FK obligatoria. |
| Seccion / organization | codigo, nombre, estado, departamento FK obligatoria. |
| Puesto / organization | codigo, nombre, estado, seccion FK obligatoria. |
| Usuario / accounts | identificador único (150), nombre, rol, is_active, puesto obligatorio; password hash, last_login nullable, is_staff/is_superuser y permisos Django. |
| ServicioNivel1 / catalog | codigo único, nombre, estado administrativo bool. |
| ServicioNivel2 / catalog | codigo único, nombre, nivel1 obligatorio; activo nullable; clase/criticidad/tipo/descripcion/metrica/minimo/maximo/seccion_responsable/usuario_responsable nullable; origen MANUAL/IMPORTADO interno. |
| ClaseServicio / catalog | etiqueta original única (100), estado bool. |
| CriticidadServicio / catalog | etiqueta original única (100), estado bool. |
| TipoServicio / catalog | etiqueta original única (100), estado bool. |
| EjecucionImportacion / imports | archivo, sha256, hoja, fecha/fecha_fin nullable, estado, creados/actualizados/omitidos/observados, contadores por entidad y filas. |
| RegistroOrigen / imports | ejecucion obligatoria, entidad/codigo/hoja; vínculos N1/N2 opcionales y excluyentes; filas/celdas/rangos, JSON original/importado/aplicado/transformaciones, revisión capturada, regla y resultado. |
| IncidenciaImportacion / imports | ejecucion obligatoria, registro opcional de esa ejecución, tipo/entidad/codigo/hoja, coordenadas, valores, regla y resultado. |

Mínimo/máximo: Decimal(20,6), sin unidad, positividad ni cero inventados; seis
decimales son una decisión de almacenamiento. El original tiene enteros y se
conservará el valor textual original en procedencia. JSON normalizado futuro
deberá representar decimales sin pérdida (por ejemplo, texto decimal).

## Constraints PostgreSQL

- Unique de columnas: Empresa.codigo, Usuario.identificador, códigos N1/N2 y
  etiquetas de las tres clasificaciones.
- Unique compuestos: area_empresa_codigo_uniq, departamento_area_codigo_uniq,
  seccion_departamento_codigo_uniq y puesto_seccion_codigo_uniq.
- Unique funcional: usuario_identificador_ci_uniq sobre Lower(identificador).
- Usuario: usuario_rol_valido y usuario_superusuario_admin.
- N2: servicio_umbrales_ordenados, servicio_usuario_requiere_seccion,
  servicio_manual_requiere_seccion y servicio_origen_valido.
- Ejecución: ejecucion_estado_valido y ejecucion_fechas_ordenadas.
- Origen: origen_un_solo_nivel, origen_n1_entidad_coherente,
  origen_n2_entidad_coherente y origen_entidad_valida.
- NOT NULL de padres/obligatorios, FK para relaciones y CHECK no negativo de
  PositiveInteger/PositiveBigInteger. Todas las FK de dominio usan PROTECT.

Un FK no comprueba estado ni pertenencia a sección: esas reglas entre tablas
viven en clean/save. save valida en transacción con un advisory lock común del
dominio, que serializa escrituras de negocio. Se bloquean operaciones masivas
y borrado físico; no se pretende que SQL directo valide reglas entre tablas.
Las consultas siguen sin ese bloqueo. Es una decisión simple para el tamaño
del parcial; ampliar concurrencia requeriría revisar la estrategia.

## Históricos y procedencia

desactivar() bloquea dependientes activos/desconocidos. Relaciones sin cambios
en registros históricos permanecen válidas; asociaciones nuevas/reactivaciones
requieren toda la jerarquía activa. Mover usuario o puesto no puede invalidar
responsables, incluidos históricos.

revision_manual identifica cambios de negocio mediante save() normal; una
escritura futura de importación declarará source="IMPORTACION". El snapshot
importado anterior permitirá comparación por campo. El modelo no ejecuta esa
comparación ni lee el Excel directamente; ahora lo hacen imports/services
mediante parser/normalizer/importer/traceability. No cambiaron campos/migraciones.

RegistroOrigen/IncidenciaImportacion son anexables e inmutables mediante dominio.
Un cambio de código/nombre del servicio no reescribe el código/valores originales.
Cada futura reimportación añadirá nueva ejecución y procedencia.
