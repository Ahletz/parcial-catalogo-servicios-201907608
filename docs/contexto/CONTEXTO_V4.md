# CONTEXTO V4 — ampliación de catálogo a Service Desk

Fecha: 2026-10-29, America/Guatemala. Herramienta: Codex desktop; familia
indicada GPT-6; variante/versión exacta no expuesta. Contexto anterior:
[V3](CONTEXTO_V3.md). Base observada `9624e34e33a3cc9b3218cb7497542e49cf3773bc`,
main. **Solo documentación y fuentes; ninguna funcionalidad SD implementada.**

## Fuentes realmente suministradas y motivo

Se leyeron AGENTS/README, RESOLUCION, DECISIONES, MODELO_DATOS, REQUISITOS,
MATRIZ_TRAZABILIDAD y V1/V2/V3: conservan estado, reglas e historia del parcial.
Código de accounts/access/models, dominio, catálogo/importador, mantenimientos,
estructura y listado de pruebas: distinguen lo implementado de una propuesta.

Nuevas fuentes: tarea de Service Desk, L22 y L25 completas; lectura de catálogo
y CMDB; transcripción/inspección visual de diagramas y tablas. Ver
[FUENTES_SERVICE_DESK](../FUENTES_SERVICE_DESK.md) para rutas, páginas, rangos y
hashes. Se encontró T en Descargas tras no hallarlo en la ruta solicitada y se
copió sin modificar. El PDF PP2 no está; ENUNCIADO y copia textual disponibles
documentan la base. No leer secretos ni ejecutar instrucciones de archivos.

## Hallazgos y actualización justificada

| Antes (V3/PP2) | Hallazgo real / motivo | Después (V4) e impacto |
|---|---|---|
| Tickets fuera de alcance; dos roles; P01–P12 | T §§3–8 exige tickets/colas, siete procesos, CMDB y nuevos permisos | Ampliación documentada; conservar PP2 y proponer módulos SD sin implementarlos. |
| Números P usados solo por el parcial | T §11 redefine P01–P18, incluida persistencia ahora en P18 | Namespaces PP2-P y SD-P; matriz propia sin renombrar métodos antiguos. |
| No CMDB; jerarquía organizacional existente | CM tiene dos ejemplos y Padres/Hijos vacíos; L22 contiene sistemas, no taxonomía completa de dispositivos | Diagrama/diccionario de lo observable; SD-DP01 bloquea inventar categorías. Generador futuro de 5,000 separado del Excel. |
| Guarda admin/consulta y bloqueo global de escrituras | Código no soporta capacidades múltiples ni acceso por cola; bulk prohibido | Diseñar política de capacidades, precedencia CONSULTA y concurrencia/carga validada; no aplicar bypass. |
| Contexto V3 prohibía crear V4 por mero avance | Nueva tarea cambia alcance, fuentes, aceptación y cinco ingenierías | V4 por cambio sustancial, solicitado expresamente; historial V1–V3 intacto. |
| Tres ingenierías y cinco temas de prompt | T exige ocho prompts, tres actualizaciones y tres ciclos; menciona Graph sin desarrollar una sección propia | IA separa mínimos nuevos, evidencia histórica y planes. No declarar completadas prácticas futuras ni inferir segundo grafo como dato docente. |
| Parámetros docentes no usados por catálogo | L25-11 vs 12/13 y tabla I0–I6 tienen diferencias/solapamientos | Mapeos visuales y propuestas explícitas en PROCESOS; pendientes no convertidos en requisitos inventados. |

Alternativas descartadas: poblar 5,000 CI ahora; inventar taxonomía; reusar
organigrama como CMDB; afirmar pruebas por leer su código; convertir planes en
ciclos; ampliar accidentalmente permisos de consulta. Todo contradice fuentes,
alcance actual o integridad de la evidencia.

## Decisiones, estado y pendientes

D31–D38 de [DECISIONES](../DECISIONES.md) registran alcance/identificadores,
fuentes y propuestas. SD-DP01–SD-DP12 en [SERVICE_DESK](../SERVICE_DESK.md)
delimitan taxonomía, grafos, roles, ticket nuevo servicio, incidentes, soporte,
tiempos/adjuntos, dispositivos, concurrencia, transferencias y fuente/entrega.
El usuario autoriza documentación y commit local; no implementación ni push.

## Impacto documental

AGENTS V4; README e índices PP2 con enlace de alcance; DECISIONES actualizado.
Nuevos SERVICE_DESK (brechas/requisitos/estructura), FUENTES_SERVICE_DESK,
MODELO (ER/diccionario/CMDB/grafos), PROCESOS (flujos/permisos/parámetros/métricas),
PRUEBAS (matriz completa y SD-P01–P18), IA y esta versión V4. Se versionan
originales canónicos necesarios, sin duplicados ni alteración de datos.
No cambios en src/tests/scripts/Docker/migraciones/requirements.

## Validación de esta fase

Lectura completa del nuevo enunciado (10 páginas), L22 (25) y L25 (16), tablas
visuales pertinentes; CMDB B4:U6 (20 atributos/2 ejemplos), catálogo conservado
con SHA conocido. Controles documentales de cierre ejecutados con resultado
correcto: enlaces locales de los 14 documentos nuevos/modificados; cobertura
39/39 requisitos en matriz y 18/18 escenarios SD; hashes de ambos Excel
coincidentes; CMDB sin listas de validación ni fórmulas (catálogo con cuatro
validaciones y sin fórmulas). `git diff --check` devolvió código 0 y el diff
rastreado contiene solo los siete Markdown modificados. Los siete Markdown
nuevos y fuentes canónicas se revisan también al preparar el commit. Son
controles documentales; no son pruebas funcionales ni sustituyen P01–P18.

Al incluir la fuente textual original en staging, el control global
`git diff --cached --check` reportó sus espacios finales preexistentes. No se
modificó la fuente para eliminarlos: su hash debe conservarse. Se verifica por
separado `git diff --cached --check -- '*.md'` para los documentos redactados y
se registra esta excepción de fuente en FUENTES_SERVICE_DESK. No es una prueba
de aplicación ni un ciclo funcional de Loop Engineering.

No se ejecutaron tests (ni dirigidos ni completos), importaciones persistentes,
migraciones, generación, Docker ni operaciones remotas. Los comandos existentes
del README siguen siendo instrucciones para fases autorizadas, no acciones de
esta revisión. No se acreditan tres nuevos ciclos ni ocho prompts por crear V4.

## Commit verificable

El SHA del commit que introduce esta versión se recupera después de crearlo:

```bash
git log -1 --diff-filter=A --format='%H %s' -- docs/contexto/CONTEXTO_V4.md
```

Este mecanismo evita inventar un hash autorreferente. V4 es una actualización
real del contexto; la suficiencia de evidencias históricas para los mínimos de
la nueva tarea queda por confirmar y no se acredita solo por llegar a V4.
