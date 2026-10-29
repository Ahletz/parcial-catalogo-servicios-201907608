# Registro inicial de decisiones

> El registro PP2 siguiente es histórico. La actualización vigente de alcance
> Service Desk está al final (D31–D56); [V6](contexto/CONTEXTO_V6.md) vigente, V4/V5 históricos.
> Las autorizaciones de implementación/cierre citadas en fases antiguas no
> se aplican automáticamente a otras fases. La solicitud CMDB autoriza modelo, migración y controles ligeros; sin carga masiva ni suite.

Fecha: 2026-10-04. Estado: dominio/importación y funcionalidad web implementados;
P01–P11 automatizadas, P12 dirigido aprobado; cierre final en FASE_CIERRE. Resultados en evidencias de cada fase.
Autorización: solicitud del usuario de creación de contexto, posterior al análisis.
Requisitos normativos en [REQUISITOS.md](REQUISITOS.md); evidencia del Excel en
[ANALISIS_EXCEL.md](ANALISIS_EXCEL.md). La aprobación de arquitectura no autoriza
implementarla durante V1. La fase posterior autorizó base/modelos/migraciones;
la fase de importación autorizó importador completo y P06–P08. La nueva solicitud
autoriza autenticación, roles, mantenimientos, UI, demo y P01–P05/P09–P11.
La solicitud final autoriza P12/Docker/harness/documentación. Publicación y
acceso GitHub permanecen pendientes; no se autoriza push/tag.

## Cómo interpretar este registro

## Cierre autorizado — decisiones previas a implementar

Base: 140af56c804ef4086637c1ea2c2af404e5b14327, main, 2026-10-04.
La nueva solicitud autoriza Docker definitivo, P12, harness y documentación;
prevalece sobre los límites históricos de las fases anteriores. No push/tag.

- D26: Dockerfile final conserva versiones/digests y código aprobado, copia
  fuentes de datos inmutables y recolecta estáticos; usuario no root. Compose
  final db/init/web: PostgreSQL autenticado, volumen, healthcheck, migraciones
  antes de web. Importación/demo explícitas; nunca reset automático. Solo web
  publica localhost:8000. Configuración por variables y .env.example pública.
- D27: verify.sh usa exclusivamente .env.example y valores sintéticos públicos
  definidos por el harness, proyecto/volumen nuevos separados por ejecución,
  puerto de verificación 18000. No lee .env ni reutiliza la base normal. Ejecuta
  una suite completa, doble importación/demo, HTTP real y P12. Conserva volumen.
- D28: P12 crea Empresa sintética de código controlado, compara PK/nombre y
  conteos antes/después de stop y up --force-recreate de db/init/web. Verifica
  cambio de IDs de contenedores y conservación del volumen/dato. No down -v.
- D29: PDF por nombre/ubicación parece material del parcial; §7 exige el Excel,
  no ese PDF. Se conserva sin leer contenido/modificar/incluir en commit; regla
  explícita en .gitignore evita que bloquee el árbol de entrega limpio.
- D30: documentación final con matriz completa y auditoría sin adjudicar nota;
  acceso GitHub, publicación/etiqueta e identidad/metadatos no comprobables
  quedan explícitos. No inventar nombre completo ni versión exacta de IA.

Respaldo: ENUNCIADO §4–§8. Referencias oficiales:
[orden de arranque](https://docs.docker.com/compose/how-tos/startup-order/),
[volúmenes](https://docs.docker.com/engine/storage/volumes/).


- Requisito (R): obligación del enunciado, con sección e ID verificables.
- Decisión (D): elección para cumplir un requisito; no atribuible al enunciado.
- Inferencia (I): conclusión de datos que no aparece explícita en una celda.
  Debe conservar evidencia, regla y resultado; una inferencia aprobada sigue
  siendo inferencia, no un dato original.

Por ejemplo: conservar 12/46 es R; Django 5.2 es D; padre SE.12 para fila 101 es I.
El análisis anterior incluyó propuestas; solo lo aprobado expresamente en la
solicitud actual se marca APROBADO. El resto queda PROPUESTO/PENDIENTE.

## Decisiones aprobadas

| ID | Tipo / estado | Decisión | Justificación, respaldo e impacto |
|---|---|---|---|
| D01 | D / APROBADO | Monolito modular: accounts, organization, catalog, imports, config. | §1/§5 permiten elegir tecnología; integra alcance sin separar despliegues innecesarios. |
| D02 | D / APROBADO | Python 3.13, Django 5.2 LTS, PostgreSQL 17, Gunicorn, WhiteNoise, openpyxl, Docker Compose. | PostgreSQL cumple preferencia §1; Django integra auth/ORM/formularios/migraciones; openpyxl leerá fuente; servidor/estáticos y Compose permiten ejecución requerida. |
| D03 | R / CONFIRMADO | Empresa → Área → Departamento → Sección → Puesto → Usuario. | §3.2; padre único, unicidad dentro del padre, empresa derivada y varios usuarios por puesto. |
| D04 | R+D / APROBADO | Original inmutable y de solo lectura; 12 códigos N1/46 servicios N2; combinaciones dentro del rango. | I02/I08; conteos reales comprobados. Configurar recurso de solo lectura y controles por conjunto importado. |
| D05 | D / APROBADO | Filas 42 y 67 reportadas sin identidad N2; no crean servicios ni reciben propagación externa. | I06; C/D vacíos fuera de combinaciones N2. |
| D06 | D / APROBADO | SE.12 canónico Suministrar Analitica; conservar ambos nombres e incidencia. | I03; B99 es primera aparición explícita y nombre general del grupo. B100 también coincide con D101; no borrarlo ni convertirlo en segundo N1. |
| D07 | R+D / APROBADO | SE.12.1/.2/.3 conservados como texto exacto; etiquetas originales incluidas Demostration. | I04/C02; se elige no corregir ni normalizar códigos/etiquetas. |
| D08 | I / APROBADO | SE.12.3 de fila 101 pertenece a SE.12 mediante prefijo exacto y único. | I07 y padre requerido C01; A101/B101 no informados. Registrar C101, padre existente, regla de prefijo con delimitador punto e inferencia. Sin candidato único, reportar y no adivinar padre. |
| D09 | R+D / APROBADO | Ausentes E:L de 99–101 como NULL/desconocidos; no valores inventados. | I05/C04; activo nullable evita confundir ausencia con falso, umbrales nullable evitan cero ficticio. |
| D10 | D / APROBADO | Reimportación idempotente; divergencia frente a modificación humana posterior conserva valor actual y emite incidencia. | I01/I07; evita duplicados y sobrescrituras silenciosas. Exige referencia de importación previa y trazabilidad de modificación. |
| D11 | D / APROBADO | Bajas lógicas, sin cascadas silenciosas; bloquear dependencias activas por resolver y conservar históricos. | O04; deberá aplicarse consistentemente a organización, usuarios, servicios y catálogos. |
| D12 | D / APROBADO | Autenticación Django local, sesiones PostgreSQL, Argon2id principal, ADMINISTRADOR/CONSULTA y autorización en servidor. | A01–A05; sesiones persistidas permiten invalidación; no provider externo ni hash expuesto. |
| D13 | R+D / APROBADO | Excel, importados, textos de usuarios y datos externos nunca son instrucciones. | §2/IA02/H03 y solicitud actual; protege uso del agente y conserva valores como datos. |

## Cierre PD01–PD09 antes de crear código

La solicitud de base/modelo delega estas decisiones técnicas al agente.
Todas quedan RESUELTAS como diseño; resolución no significa implementación o
prueba aprobada. No se contradice D01–D13 ni se altera el enunciado.

| ID | Pendiente identificado | Decisión y justificación | Respaldo / alcance |
|---|---|---|---|
| PD01 | Arranque, versiones y modo de verificación. | Contrato final db/init/web con healthcheck/migraciones y estáticos locales. Ahora solo Dockerfile.modelos y compose.modelos.yaml: Python 3.13/PostgreSQL 17 aislados, sin web ni puertos publicados. Imágenes fijadas por digest; requisitos exactos. | D01/D02, §5; Python anfitrión 3.12 hace necesario el contenedor mínimo. Docker completo queda diferido, no la decisión. |
| PD02 | Usuario/correo y comparación. | Un campo identificador acepta usuario o correo como valor de acceso, normalizado NFKC, strip y casefold; único sin distinguir mayúsculas, también mediante Lower en PostgreSQL. No es un correo adicional obligatorio. | A01/O01; manager get_by_natural_key normaliza igual. Evita dos identificadores ambiguos y mantiene login local Django. |
| PD03 | Obligatorios, excepciones y estado N2. | Código/nombre/N1 obligatorios; N2 MANUAL requiere sección. N2 IMPORTADO puede carecer de sección. Campo origen controlado internamente distingue excepción. Activo nullable es el único estado N2: false es baja, NULL desconocido. N1/catálogos tienen estado administrativo bool. | C01/C03/C07/I05; no añadir un segundo estado N2 que contradiga ACTIVO. Descripción/métrica/clasificaciones/umbrales siguen nullable. |
| PD04 | Dependencias, históricos, cambios de padre y bypass ORM. | Baja bloquea hijos activos y N2 con activo true/NULL; usuario/sección/catálogos bloquean referencias de esos servicios. Históricos false permanecen. Validar relaciones nuevas/cambiadas y reactivaciones contra padres activos. Revalidar responsables al mover usuario o puesto. save ejecuta full_clean en transacción; escrituras del dominio serializadas con advisory lock PostgreSQL. Bloquear update/bulk_create/bulk_update/delete del QuerySet e instancias delete. | O03/O04/C07; checks entre tablas no se expresan con CHECK local. Lock único evita carreras de baja/asignación; suficiente para volumen del parcial, sin triggers ni otro servicio. |
| PD05 | Conflicto N2 futuro no presente en original. | Valor no vacío de celda principal primero; si falta, primera no vacía en orden de fila dentro de la identidad/rango autorizado. Reportar todos los valores discordantes y la regla. Fuera del rango no rellenar. | I02/I07; regla determinista compatible, todavía no hay lector/importador. |
| PD06 | Detectar modificaciones humanas y comparar sin pisarlas. | Snapshot previo por campo, actual y nueva fuente: actual=previo permite actualizar; actual=nueva omite; divergencia humana conserva actual y observa. Primera colisión con registro manual conserva y observa. revision_manual aumenta en cambios de negocio normales; guardar desde importación se declara explícitamente y no aumenta esa revisión. RegistroOrigen conserva snapshot normalizado/importado, aplicado y revisión capturada. | D10/I01/I07; timestamp solo no identifica cambios humanos. Esta fase prepara campos y mecanismo de escritura, no implementa reimportación. |
| PD07 | Esquema de procedencia y métricas. | EjecucionImportacion con hash/hoja/fechas/estado/contadores; RegistroOrigen separado con entidad/código, vínculo N1/N2 opcional, coordenadas, original/importado/aplicado y transformaciones; IncidenciaImportacion con regla/valores/resultado. Orígenes e incidencias anexados son inmutables por dominio. Contadores de filas separados de entidades; observaciones pueden superponerse. | I01/I07; preservar historia al editar servicios y distinguir 97 filas de 46 N2. |
| PD08 | Aislamiento y niveles de prueba. | Ahora solo pruebas internas de modelos con Django/PostgreSQL y settings_test; BD test_ separada, --keepdb, sin borrar volúmenes. P01–P12 siguen pendientes; futura integración/E2E y P12 tendrán entorno independiente. | H02/§6; no convertir pruebas de modelo en aceptación funcional. |
| PD09 | Usuario inicial y sesiones. | AbstractBaseUser/PermissionsMixin, puesto obligatorio sin excepción superusuario, rol ADMINISTRADOR/CONSULTA con CHECK. Hash Argon2id mediante set_password, rechazar valores sin formato de hasher. Sesiones PostgreSQL, 2 h, HttpOnly/SameSite=Lax, Secure activable para HTTPS y falso en local HTTP; CSRF/escape estándar. SECRET_KEY requerida por entorno, sin valor real en Git. | A02–A05/O02; usuario en primera migración, empresa derivada. Backend local preparado; vistas y mensajes de login/logout pendientes. |

Referencias técnicas consultadas: [validación y save](https://docs.djangoproject.com/en/5.2/ref/models/instances/),
[constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/),
[usuario personalizado](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/) y
[operaciones QuerySet](https://docs.djangoproject.com/en/5.2/ref/models/querysets/).
No implementar una alternativa que omita validación en save ni resolver reglas
cruzadas únicamente con formularios. SQL directo continúa sujeto a constraints
locales, pero no es una API autorizada para reglas cruzadas.

Versiones directas seleccionadas tras consultar PyPI: Django 5.2.17,
psycopg 3.3.6 (binary), gunicorn 26.2.0, WhiteNoise 6.12.0, openpyxl 3.1.5,
argon2-cffi 25.1.0. Las transitivas quedaron fijadas tras resolver la instalación
en Python 3.13/Linux y comprobar pip check; ver requirements.txt.
Python oficial: sha256:5024f48ba9441d4b13a95d3945abc6365538e3a31109833367a1923523c6efed;
PostgreSQL oficial: sha256:639ab7ceb90e13123085b741fb31ef493fba25463002f6da665352e7b534b652.
Son identificadores públicos de imágenes, no credenciales.

## Concreción de importación — antes de implementar

Solicitud actual: implementar importador y automatizar P06–P08; no autoriza
login/logout, interfaz completa, push ni tag. Base observada: b08a1e5, main,
árbol limpio; origin apunta al repositorio GitHub Ahletz del proyecto.

Hallazgo → motivo → decisión → impacto, sin cambiar D01–D13 ni PD01–PD09:

- D14: RegistroOrigen distingue valores_importados y valores_aplicados. Si una
  divergencia conservada se toma después como nuevo baseline aplicado, una
  tercera importación podría sobrescribir el valor humano. Concretar PD06:
  comparar por campo con el último snapshot IMPORTADO de una ejecución
  COMPLETADA, nunca con el valor aplicado divergente. Actual=nuevo omite;
  actual=importado previo permite actualizar; divergencia conserva y observa.
  Primera colisión sin procedencia conserva diferencias. Comparar Decimal por
  valor canónico, manteniendo valor/tipo originales en evidencia. Las
  asignaciones organizacionales y estados N1/catálogos no pertenecen al Excel.
- D15: una ejecución creada dentro de la misma transacción que falla también
  desaparece por rollback. Crear ejecución antes de procesar; importar entidades,
  procedencia, incidencias y cierre exitoso en una transacción con el lock ya
  aprobado. Ante fallo, rollback funcional y registrar FALLIDA/incidencia después.
  Archivo inexistente no permite calcular hash ni crear ejecución válida.
- D16: leer bytes una sola vez, calcular hash y abrir esos mismos bytes con
  openpyxl (data_only=False, keep_links=False). No guardar libro ni evaluar
  fórmulas; fórmulas en las regiones del contrato producen error fatal explícito,
  no se sustituyen por valores cacheados. Textos se conservan exactamente.
- D17: códigos/etiquetas identifican origen; snapshots guardan ID aplicado para
  enlazarlo también si una edición humana cambia el código o etiqueta. El código
  del nuevo RegistroOrigen coincide con el servicio actual; el código de la
  fuente se conserva en valores_importados/originales. Sin inferencias de
  renombre de la fuente; colisiones de dos identidades hacia una entidad fallan.
- D18: creados/actualizados/omitidos cuentan entidades funcionales, separados por
  NIVEL1/NIVEL2/CLASE/CRITICIDAD/TIPO. Observados cuentan unidades con incidencia
  y pueden superponerse; incidencias cuentan eventos. Filas físicas,
  continuaciones y huérfanas se cuentan aparte. 12/46 son cardinalidades del
  conjunto original, no límites a registros manuales adicionales en PostgreSQL.

Impacto: servicios de parser/normalización/importación/trazabilidad y tests;
no hace falta cambiar modelos ni generar migraciones. CONTEXTO_V3 registrará
estos hallazgos reales. P06–P08 solo se cerrarán tras ejecutar pruebas reales.
Referencias: documentación oficial de
[openpyxl](https://openpyxl.readthedocs.io/en/stable/api/openpyxl.reader.excel.html)
y [transacciones Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

## Concreción funcional — antes de implementar

Base observada: f034c5af968dae920c94377c383095d5a7d98b29, main y árbol limpio.
La solicitud funcional sustituye el límite histórico de no implementar HTTP.
No rehacer dominio/importador ni ejecutar suites completas tras cada cambio.

- D20: LoginView/LogoutView locales y AuthenticationForm adaptado al identificador
  aprobado. Logout exclusivamente POST con CSRF. Guarda común comprueba sesión,
  estado activo y rol; ADMINISTRADOR escribe, CONSULTA lee. GET nunca modifica
  entidades. No exponer hash, origen interno, revisión, permisos ni flags de staff.
- D21: ModelForms con listas explícitas de campos; referencias activas y la
  referencia histórica actual disponibles. Conservar textos de servicios y
  NULL. El dominio sigue validando padres, bajas, umbrales y responsables.
  Validación/guardado y baja bajo domain_transaction; convertir ValidationError
  en mensajes de formulario. No usar update/delete ni introducir modelos nuevos.
- D22: seed_demo requiere credenciales por variables de entorno, crea jerarquía
  DEMO y dos roles, y garantiza tres asignaciones válidas de importados. Repetir
  no rota passwords ni pisa asignaciones humanas, no revive bajas ni cambia
  identidades existentes incompatibles. Sin servicios disponibles, falla con
  instrucción de importar primero y rollback completo. Nunca imprime credenciales.
- D23: plantillas Django/CSS local, registro explícito de mantenimientos y filtros
  validados, paginación estable y ficha completa. Perfil web local del Compose
  interno para revisar funcionalidad; Docker final/P12 quedan para el cierre.
  Pruebas dirigidas durante desarrollo; una ejecución completa al finalizar.

Motivo/impacto: completar §3.1–3.3 sin alterar decisiones de dominio ni ampliar
funciones. Se añadirán vistas/formularios/templates, comando demo y tests HTTP;
solo rutas/settings, Compose, variables de ejemplo y documentos necesarios.
Referencias oficiales consultadas:
[auth Django 5.2](https://docs.djangoproject.com/en/5.2/topics/auth/default/),
[ModelForms](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/) y
[extends de Compose](https://docs.docker.com/compose/how-tos/multiple-compose-files/extends/).
No se crean V4 ni nuevas dependencias.

Hallazgo real → motivo → decisión D24 → impacto: P02 detectó _auth_user_id
residual cuando ModelBackend devuelve AnonymousUser por cuenta inactiva.
Concretar D20: ante rechazo, logout si hay usuario autenticado o SESSION_KEY
residual. Evita restaurar esa sesión al reactivar; no modifica modelo/backend.
Guarda accounts/access.py y regresión HTTP; revisión P04_REVISION_SESIONES.

Hallazgo operativo D25: Gunicorn escuchaba en 0.0.0.0:8000, pero el puerto
efectivo estaba vacío (docker port sin salida y NetworkSettings.Ports={}).
El perfil heredaba exclusivamente la red internal de las pruebas. Añadir
una red bridge de interfaz solo a web, manteniendo modelos/db en su red
internal y publicación limitada a 127.0.0.1:8000. No cambia Django ni datos.
Control dirigido adicional desde la red del anfitrión Docker para cubrir el
puerto publicado; no repetir la suite de Django sin cambios en src/tests.
Referencia: [red internal](https://docs.docker.com/reference/cli/docker/network/create/#network-internal-mode---internal).

## Pendientes de entrega y evidencia

### Hallazgo real de pruebas: obligatoriedad heredada (resuelto)

La suite de importación falló por IncidenciaImportacion.codigo opcional según
blank=True, pero obligatorio según DomainValidationMixin.clean. Nueva D19:
la guarda común respeta ausencia cuando el campo tiene blank=True; mantiene
validación de texto obligatorio en códigos/nombres/etiquetas restantes.
Motivo: registrar filas sin identidad y errores sin inventar códigos.
Impacto: ajuste mínimo de config/domain.py, ninguna migración. La suite fallida
pasó con 60 tests, las 63 regresiones del modelo pasaron y P06–P08 pasaron.
Documentado como hallazgo V3 y revisión real del prompt de trabajo.

- Nombre completo/carné del integrante, rama final y medio de entrega. Remoto
  observado: origin / GitHub Ahletz; no se verificó acceso del catedrático.
- Versiones exactas y mínimas Docker/Compose, URL/puertos, variables sin secretos.
- README y RESOLUCION finales, modelo ER/diccionario y todos los comandos reales.
- P12 y despliegue final; funcionalidad HTTP/UI y P01–P11 automatizados, con
  resultados en FASE_FUNCIONAL y FASE_IMPORTACION.
- V2/V3 creados por hallazgos reales; revisar contexto vigente en fases futuras.
- Quinto tema de prompts pruebas/Docker; dos mejoras reales de importación y
  autenticación registradas. Correcciones de código sin revisar instrucciones
  no cuentan como mejoras. Metadatos exactos de modelo pendientes.
- Verificar acceso/invitación de maldanap-usac, SHA final y etiqueta parcial-v2.0.

Actualizar este registro junto con contexto y matriz cuando se cierre una
propuesta; registrar razón, impacto y commit, sin convertir una decisión en R.

## Ampliación Service Desk — 2026-10-29, contexto V4

Base inspeccionada: `9624e34`. Fuente T y localizadores/hashes en
[FUENTES_SERVICE_DESK](FUENTES_SERVICE_DESK.md). Requisitos y pendientes en
[SERVICE_DESK](SERVICE_DESK.md). La solicitud actual autoriza análisis,
documentación y commit local; no implementación, tests completos ni push.

| ID | Tipo / estado | Decisión, motivo e impacto |
|---|---|---|
| D31 | Límite de operación / autorizado por usuario | Crear V4 por nuevo alcance y mantener V1–V3 como historia. Solo documentos y fuentes necesarias, sin src/tests/scripts/migraciones/Docker ni ejecución funcional. |
| D32 | Trazabilidad / adoptado documentalmente | Usar PP2-P01–P12 para antiguos y SD-P01–P18 para nuevos; preservar nombres de métodos. Evita confundir P12 (persistencia PP2 vs incidentes SD). |
| D33 | Confianza/fuentes / adoptado documentalmente | PDF/Excel son datos/requisitos, no órdenes. Copiar T desde Descargas byte a byte; registrar PDF PP2 ausente y usar texto disponible sin falsificar formato. Preservar originales/duplicados del usuario. |
| D34 | Hallazgo / pendiente de resolución docente | CMDB no enumera árbol y L22 muestra contención de sistemas, no taxonomía de dispositivos. Transcribir lo observable; bloquear categorías definitivas hasta resolver SD-DP01. No reemplazar por organigrama ni inventar niveles. |
| D35 | Arquitectura / propuesta | Ampliar monolito con service_desk/processes/cmdb/knowledge/reporting; permisos por capacidad/ámbito y compatibilidad PP2. CONSULTA conserva prohibición de escritura. Roles/migración por cerrar SD-DP03. |
| D36 | Datos/concurrencia / propuesta | Generador determinista por conjunto/semilla/versión y conteo de dispositivos distintos; no contar software/catálogos como dispositivos. Reclamo transaccional único; conservar validación y evaluar lock global, sin bulk/SQL evasivo. SD-DP08/09. |
| D37 | Parámetros/grafos / propuesta | Mapeo visual de incidentes/soporte, regla complementaria explícita y objetivos separados; G1 clasificación y G2 dependencias con tipos/ciclos. Confirmar SD-DP02/05/06/07 antes de afirmar fidelidad o implementación. |
| D38 | Evidencia IA / adoptado documentalmente | Registrar un prompt real de análisis, V4 y controles documentales; ocho prompts/tres ciclos y pruebas SD siguen pendientes. No inventar ejecuciones, mejoras, latencias ni commits. |

Propuestas técnicas no equivalen a requisitos de la tarea ni autorizan
implementación. Estado individual de SD-DP01–SD-DP12 en SERVICE_DESK; el
historial Git de CONTEXTO_V4 identifica el commit documental sin hash ficticio.

## CMDB — decisiones D39–D46, 2026-10-29

Solicitud actual: implementar solo modelo CMDB, relaciones y migración; sin
5,000 CI, tickets, workflows, dashboard, grafos completos ni pruebas pesadas.
Fuente: [ANALISIS_CMDB](ANALISIS_CMDB.md), con hojas/celdas y páginas.

| ID | Estado | Decisión y justificación |
|---|---|---|
| D39 | Adoptada: límite de fidelidad | C5/C6 respaldan Hardware/Software; J5/J6 vacíos. Bosque mínimo de tipos independientes, sin nombres de niveles inventados. Padres/niveles originales adicionales no demostrables; SD-P04 y esa parte de SD-DP01 siguen pendientes de fuente. |
| D40 | Adoptada: clasificación | ClasificacionCI con código único, padre PROTECT, orden, nivel derivado, estado/procedencia y esquema JSON. Organigrama y SKMS/CMS no se reutilizan como clases. |
| D41 | Adoptada: atributos | JSON consultable y validado por clase, sin herencia tácita ni IP universal. Cambiar esquema o marca de dispositivo no puede invalidar/redefinir CI existentes silenciosamente. Campos nuevos identificados como extensiones. |
| D42 | Adoptada: ubicación/responsable | UbicacionCI plana; responsable reutiliza Usuario. Textos de equipo/K6 del Excel requieren mapeo futuro, no inferencia automática. |
| D43 | Adoptada: relaciones | Tipo configurable con dirección/política de ciclos; CI–CI único por tipo/par, sin autoenlace. No dirigida exige extremos por PK. Semántica congelada con relaciones; se preservan históricos. |
| D44 | Adoptada: ciclos/grafos | Clasificación acíclica y subgrafo técnico activo de tipos restrictivos acíclico, incluso mezclando tipos. G1/G2 definidos para proyecto; interpretación docente de ambos grafos permanece por confirmar. Sin recorrido público aún. |
| D45 | Adoptada: integración/persistencia | ServicioCI M:N a N2 existente; DomainModel/lock/PROTECT/bajas/bulk guardas se conservan. Sin Ticket artificial, seed ni generador. Migración solo de esquema. |
| D46 | Adoptada: evidencia/entorno | Solo check y migraciones ligeras. Docker/repositorio original bloqueados por aislamiento: preparar copia y parche, sin afirmar aplicación original ni migración PostgreSQL aprobada. Dependencias oficiales solo en scratch. Máximo dos commits locales, sin push. |

SD-DP08 queda resuelto para distinguir dispositivo por clasificación explícita;
distribución y carga siguen pendientes. SD-DP09 adopta guardas actuales para
esta fase, sin afirmar rendimiento a 5,000. Las decisiones no crean datos fuente.

## Service Desk — decisiones D47–D56, 2026-10-29 (V6)

Solicitud SD-PE03: integrar CMDB e implementar tickets, colas, permisos,
asignación concurrente y siete procesos. Contexto [V6](contexto/CONTEXTO_V6.md);
evidencia [FASE_SERVICE_DESK](evidencias/FASE_SERVICE_DESK.md).

| ID | Estado | Decisión y justificación |
|---|---|---|
| D47 | Adoptada: integración | CMDB por bundle y `merge --ff-only` (commits 2fb2521/35403e6 intactos); parche no aplicado. Reproducción manual descartada al localizar los artefactos. |
| D48 | Adoptada: roles (SD-DP03) | `Usuario.rol` añade OPERATIVO (sin escritura PP2). Solicitante/agente/aprobador son `AsignacionRolSD` aditivas; admin y consulta siguen siendo valores globales. CONSULTA recorta toda capacidad a CONSULTAR aunque tenga roles o membresías. |
| D49 | Adoptada: colas/capacidades | `ColaServiceDesk` con un único `proceso` (choices), nivel 0–4, orden PRIORIDAD_ANTIGUEDAD y objetivos de primera atención/resolución. `MembresiaCola` con exactamente un sujeto (usuario o rol) y cinco banderas separadas. Admin global obtiene CONSULTAR+ADMINISTRAR; atender/transferir/aprobar solo por membresía. |
| D50 | Adoptada: concurrencia (SD-DP09 parcial) | Operaciones en `service_desk.servicios`: `domain_transaction` (lock advisory) y luego `select_for_update(of=self)`. `tomar_ticket` falla con `ConflictoAsignacion` si ya hay responsable. Sin bypass de full_clean ni bulk. Rendimiento a escala no medido. |
| D51 | Adoptada: transferencia (SD-DP10) | Solo a cola activa distinta del mismo proceso; motivo obligatorio; `TransferenciaTicket` guarda colas, responsables, actor y fecha. Reclasificación entre procesos no implementada. Cola/usuario no se desactivan ni pasan a consulta con tickets abiertos asignados; tampoco se retira la capacidad atender que los sostiene. |
| D52 | Adoptada: Ticket | N1 derivado (`ticket.nivel1`), número `SD-000001` desde secuencia serializada por el lock, UUID público, campos de alta inmutables, estado validado contra la definición y aprobación vigente exigida también en `Ticket.clean`. Sin CI → `motivo_sin_ci` obligatorio; no se crean CI ficticios. |
| D53 | Adoptada: nuevos servicios (SD-DP04) | El ticket atiende un N2 existente; el resultado (crear o vincular) vive en `DetalleNuevoServicio`. Crear valida código único y nombre no repetido en el mismo N1 antes de aprobar y al cerrar. |
| D54 | Adoptada: incidentes (SD-DP05) | Tabla L25-16 como referencia. Regla complementaria: bandas consecutivas (I1 ≤3 h, I2 ≤8 h, I3 ≤2 d, I4 ≤1 sem, I5 ≥30 d), hueco 1 sem–30 d sin sugerencia; seguridad→I6, sin interrupción→I0. Solo sugiere; si la persona elige otra o no hay sugerencia, exige motivo. Configurable con `SD_BANDAS_INCIDENTE`. |
| D55 | Adoptada: soporte (SD-DP06) | `NivelSoporte` 0–4 (L25-11) y `EQUIVALENCIA_SOPORTE_0_3` (L25-12/13: 2 y 3 → 2; 4 → 3). Sin cuotas 20/70/5/5. |
| D56 | Adoptada: adjuntos (SD-DP07 parcial) | Máx. 10 MiB (`SD_ADJUNTO_MAX_BYTES`), PDF/PNG/JPEG/TXT (`SD_ADJUNTO_EXTENSIONES`), MIME declarado y firma de contenido comprobados, nombre saneado, ruta física UUID en `SD_ADJUNTOS_DIR` privado, descarga solo por vista autenticada y autorizada. Volumen Docker para adjuntos pendiente. |

Aprobación (todas las decisiones de proceso): el aprobador no puede ser el
solicitante ni el creador; en accesos tampoco el beneficiario. La aprobación
guarda una huella SHA-256 del contenido aprobado (en cambios incluye los CI);
modificarlo invalida la aprobación para ejecutar/implementar/provisionar.

## Cierre Service Desk — decisiones D57–D62, 2026-10-29 (SD-PE04)

| ID | Estado | Decisión y justificación |
|---|---|---|
| D57 | Adoptada: clases sintéticas | El generador necesita clases con atributos propios. Bajo las raíces Hardware/Software (fuente) se crean Servidor, Estación, Red, Almacenamiento, Impresora y Aplicación marcadas `decision_proyecto_D57`; no se presentan como taxonomía docente (D39 sigue vigente). |
| D58 | Adoptada: idempotencia del generador | Código por semilla+ordinal; registros existentes se conservan sin sobrescribir; relaciones y vínculos por clave natural. Validación completa por registro (≈85 s para 5,000 en el entorno local), sin bulk. |
| D59 | Adoptada: demo | `seed_service_desk` recorre los flujos con los servicios de aplicación (no escribe estados), 8 colas (dos de incidentes para transferir), 37 tickets demo + 2 incidentes derivados de E2/E3. Nuevos servicios vincula N2 existentes para preservar 12/46. Cuentas SD con `DEMO_SD_PASSWORD`. |
| D60 | Adoptada: interfaces | Plantillas Django y CSS local; grafos en SVG generado por el servidor (sin JS ni librerías). Administración reutiliza los mantenimientos genéricos PP2. |
| D61 | Adoptada: indicadores | Tiempo calendario, primera atención por bitácora excluyendo acciones administrativas, sin pausas (no modeladas), cumplimiento solo sobre resueltos con objetivo. |
| D62 | Adoptada: harness | verify.sh añade probe SD (5,000 CI dos veces, demo dos veces, tiempos P16) y la suite incluye SD-P01–P17; P18 amplía el registro de persistencia a CMDB, tickets e historial. |
