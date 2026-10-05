# Requisitos del proyecto

Fuente normativa: [ENUNCIADO.md](../ENUNCIADO.md), secciones 1–10.
Fecha de registro: 2026-10-04, America/Guatemala.
Estado: funcionalidad completa; P01–P11 y P12 dirigido aprobados; cierre final
registrado en FASE_CIERRE. Acceso/publicación/entrega GitHub pendientes humanos.
Los IDs son etiquetas de trazabilidad, no requisitos adicionales.
Decisiones aprobadas e inferencias: [DECISIONES.md](DECISIONES.md).

## Alcance y datos mínimos

Proyecto individual de Software Avanzado; valor 25 puntos; entrega indicada
04/10/2026 23:00. Aplicación web de catálogo, organización y usuarios, autenticación
local, base persistente y ejecución Docker. PostgreSQL es preferencia del
enunciado; su versión 17 es una decisión aprobada. Tickets, facturación y consumo
no son necesarios. No añadir obligaciones funcionales sin respaldo del enunciado.

| Entidad | Datos mínimos según §3.2 |
|---|---|
| Empresa | Identificador, código único, nombre, estado. |
| Área | Identificador, código, nombre, estado, empresa. |
| Departamento | Identificador, código, nombre, estado, área. |
| Sección | Identificador, código, nombre, estado, departamento. |
| Puesto | Identificador, código, nombre, estado, sección. |
| Usuario | Identificador, nombre, usuario o correo único, hash de contraseña, rol, estado, puesto. |

Los doce campos del Excel están detallados en [ANALISIS_EXCEL.md](ANALISIS_EXCEL.md).
Organización y responsables son requisitos nuevos; no existen como datos del Excel.

## Requisitos funcionales

| ID | Obligación | Fuente |
|---|---|---|
| A01 | Inicio y cierre de sesión con usuario o correo y contraseña contra base propia; sin Google/GitHub u otro proveedor externo. | §3.1 |
| A02 | Hash especializado con sal; sin texto plano ni cifrado reversible. | §3.1 |
| A03 | Proteger en servidor rutas/operaciones autenticadas; ocultar botones no equivale a autorización. | §3.1 |
| A04 | Administrador mantiene usuarios, organización y catálogos; consulta solo lee datos funcionales sin hashes ni secretos. | §3.1 |
| A05 | Impedir acceso a inactivos; logout invalida sesión o evita reutilizar su credencial. | §3.1 |
| A06 | Procedimiento reproducible de cuentas demo de ambos roles; credenciales configuradas localmente, sin secretos reales en Git. | §3.1 |
| O01 | Altas, consultas, modificaciones y bajas lógicas de las seis entidades con sus datos mínimos. | §3.2 |
| O02 | Jerarquía Empresa → Área → Departamento → Sección → Puesto → Usuario; padre único, varios usuarios por puesto, empresa del usuario derivada. | §3.2 |
| O03 | Código empresarial único; códigos subordinados únicos dentro del padre; sin huérfanos ni asociaciones nuevas a padres inactivos. | §3.2 |
| O04 | Política coherente de desactivación con dependencias, documentada e implementada, sin eliminar información silenciosamente. | §3.2 |
| C01 | Mantener N1/N2 con padre N1 para cada N2, todos los campos del Excel y códigos únicos en cada entidad. | §3.3 |
| C02 | Mantener Clase/Criticidad/Tipo y opciones controladas en formularios; preservar etiquetas o documentar mapeo de corrección. | §2, §3.3 |
| C03 | Crear, consultar, editar y desactivar servicios; validar obligatorios y referencias en servidor. | §3.3 |
| C04 | Si ambos umbrales existen, mínimo ≤ máximo; ausencia distinta de cero. | §3.3 |
| C05 | Buscar por código/nombre; filtrar por N1, estado, clase, criticidad y tipo; paginación o equivalente. | §3.3 |
| C06 | Ficha con todos los atributos y relación con N1. | §3.3 |
| C07 | Sección responsable por N2 y usuario opcional perteneciente a ella; importados pueden quedar sin asignación; demo con al menos tres asignaciones válidas. | §3.3 |
| I01 | Importador por comando o aplicación, repetible sin duplicados, con creados/actualizados/omitidos/observados. | §3.4 |
| I02 | Resolver combinaciones por celda principal dentro del rango; no crear entidad por fila ni propagar fuera del rango sin regla explícita. | §3.4.1 |
| I03 | Resolver nombre canónico SE.12, justificarlo, preservar ambos nombres y emitir observación; no duplicar código. | §3.4.2 |
| I04 | Conservar SE.12.1/.2/.3 como texto; original y mapeo verificable ante normalización. | §3.4.3 |
| I05 | Filas 99–101 con desconocidos/revisión; no inventar clase, criticidad, tipo, métrica ni activo. | §3.4.4 |
| I06 | Separar continuaciones/opciones; documentar filas sin código fuera de combinaciones y no asignarlas automáticamente. | §3.4.5 |
| I07 | Registrar hoja, fila/rango y transformaciones; conflictos de atributos reportados y regla documentada. | §3.4.6 |
| I08 | Conservar 12 códigos N1 y 46 N2 con incidencias; original intacto en el repositorio para repetición. | §2, §3.4 |

## Requisitos no funcionales, IA y verificación

| ID | Obligación | Fuente |
|---|---|---|
| IA01 | Contexto versionado con objetivo, alcance, requisitos, modelo, reglas, Excel, arquitectura, convenciones y comandos; AGENTS.md o equivalente; explicar documentos suministrados por fase. | §4.1 |
| IA02 | Dos actualizaciones motivadas del contexto y regla que separe instrucciones de datos externos no confiables. | §4.1 |
| IA03 | Cinco prompts realmente usados: Excel, modelo, autenticación, importación y pruebas/Docker; objetivo, contexto, instrucciones, restricciones, salida y aceptación de cada uno. | §4.2 |
| IA04 | Dos mejoras con prompt inicial, problema, revisión y resultado comprobado; herramienta, modelo/versión disponible y fecha. | §4.2 |
| H01 | Harness con instrucciones para ubicar contexto y automatizar preparación, migración, carga, pruebas y calidad; Docker solo no basta. | §4.3 |
| H02 | Controles observables, códigos de salida y datos controlados; aislar pruebas de información de evaluación y explicar niveles unitario/integración/E2E. | §4.3, §6 |
| H03 | No leer/publicar secretos, alterar Excel ni realizar acciones destructivas fuera de pruebas. | §4.3 |
| H04 | Un ciclo real tarea → cambio IA → controles → fallo → corrección → ejecución satisfactoria; declarar fallo deliberado si corresponde. | §4.3 |
| D01 | Fuente, Dockerfile necesarios, .dockerignore, Compose y .env.example sin secretos; construir desde repositorio. | §5 |
| D02 | docker compose up --build -d; procesamiento mediante contenedores, sin lenguaje/framework/BD instalados en anfitrión. | §5 |
| D03 | Base con volumen persistente; arranque considera disponibilidad de dependencias. | §5 |
| D04 | Documentar variables, migración/importación/cuentas/pruebas, URL/puertos, versiones Docker/Compose, logs, apagado, reinicio y recuperación; separar reinicio destructivo de pruebas. | §5, §8.9 |
| D05 | Aplicación funcional sin suscripción de IA ni claves de proveedor de modelos. | §4.3 |
| P01–P12 | Automatizar los doce escenarios obligatorios; interfaz también revisada en evaluación. | §6 |
| GEN01 | Trabajo individual, comprender código y justificar decisiones tomadas con IA. | §1, §8.10 |

P01–P12 y sus resultados esperados están en
[AGENTS.md](../AGENTS.md#estado-de-aceptación-p01p12); su implementación, prueba y
evidencia futuras se relacionan en [MATRIZ_TRAZABILIDAD.md](MATRIZ_TRAZABILIDAD.md).
P01–P12 se relacionan individualmente en la matriz; evidencias reales en
FASE_IMPORTACION, FASE_FUNCIONAL y FASE_CIERRE.

## GitHub y documentación

| ID | Obligación | Fuente |
|---|---|---|
| G01 | Repositorio identificable; incluir fuente, Docker, migraciones, pruebas, Excel y documentos; excluir dependencias, .env reales y secretos. | §7.1–2 |
| G02 | maldanap-usac con acceso para clonar/revisar; verificar invitación si privado e informar aceptación pendiente. | §7.3 |
| G03 | Entregar URL, nombre, carné, rama y SHA final por el medio indicado; parcial-v2.0 sobre ese commit. | §7.4 |
| G04 | Mantener repositorio y commit entregado disponibles durante calificación. | §7.5 |
| DOC01 | README reproducible desde clon limpio: integrante, requisitos, configuración, comandos exactos, URL, cuentas y pruebas. | §8 |
| DOC02 | docs/RESOLUCION.md completo, Markdown, extractos seleccionados sin información sensible ni resultados inventados. | §8 |

RESOLUCION.md deberá contener los diez apartados normativos:

1. Problema, alcance y supuestos.
2. Arquitectura y justificación tecnológica.
3. Diagrama ER y diccionario con claves, relaciones y restricciones.
4. Mapeo Excel/BD, combinaciones, conflictos, ausencias y reporte.
5. Autenticación, autorización, contraseñas y sesiones.
6. Evidencias separadas de contexto/prompts/harness, con archivos y commits.
7. Matriz requisito → implementación → prueba → evidencia.
8. Resultados reales: comando, fecha, commit, resultado, fallos y correcciones.
9. Docker, persistencia y recuperación del entorno.
10. Limitaciones, aporte individual y reflexión sobre errores de IA/decisiones humanas.

Estos documentos iniciales no sustituyen el README ni RESOLUCION finales.

## Evaluación y cierre

Rúbrica §9: modelo/importación 15; funcionalidad 20; autenticación 10; contexto 10;
prompts 10; harness 10; pruebas 10; Docker 10; GitHub/Markdown 5 (total 100).
Se califica 100/75/50/25/0 % por criterio según evidencia. Funciones que no puedan
ejecutarse no se consideran demostradas; documentación se evalúa por separado.

Recorrido §10: clonar → seleccionar commit → README → Docker → migrar/importar →
ambos roles → relaciones/catálogo → repetir carga → persistencia → pruebas →
contrastar RESOLUCION y evidencias. Terminado cuando otra persona puede clonar,
ejecutar, verificar y comprender usando exclusivamente el repositorio.
