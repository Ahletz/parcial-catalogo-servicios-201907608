# CONTEXTO V5 — modelo CMDB respaldado y clasificación no inventada

Fecha: 2026-10-29, America/Guatemala. Base 396aa81; anterior [V4](CONTEXTO_V4.md).
Codex desktop; familia GPT-6, variante exacta no expuesta.

## Hallazgo → fuente → cambio de decisión → impacto

V4 mantenía bloqueado todo diseño definitivo de clasificación. La inspección
completa de CMDB confirmó una sola hoja, sin hojas ocultas, listas, nombres,
tablas ni aristas padre/hijo, y únicamente Hardware/Software en C5/C6. L22
p.11/12/14/23 no añade niveles de dispositivos: contiene dominios de información
y SKMS/CMS/CMDB/KEDB. [ANALISIS_CMDB](../ANALISIS_CMDB.md) registra pruebas de
fuente y comparación, sin conocimiento externo para rellenar ausencias.

Decisión nueva: implementar bosque configurable con mínimo documental de tipos
observados, sin poblar nodos ni inventar nivel adicional. Nivel=profundidad es
convención técnica; organigrama y contención de sistemas quedan separados.
La fidelidad a una jerarquía original más detallada sigue pendiente de fuente;
SD-P04 no se declara satisfecho. Es una resolución concreta del modelo mínimo,
no una falsa afirmación de que apareció la taxonomía ausente.

Al concretar modelo, dirección y política de ciclos de un tipo no pueden
cambiar con relaciones existentes, y el subgrafo acíclico combina tipos
restrictivos para no permitir ciclos por alternarlos. Atributos JSON por clase
sin herencia implícita y cambios de esquema que no invalidan CI históricos.
Reutilizar DomainModel y su lock: no bypass bulk/SQL. No normalizar extremos
de una relación durante un save parcial de estado; exigir orientación canónica.

Esta actualización se justifica por decisiones de integridad concretadas y por
la nueva autorización de modelo, no por cumplir un número de versiones.

## Fuentes suministradas

Solicitud actual; AGENTS/V4, REQUISITOS, DECISIONES, MATRIZ, MODELO y documentos
SD; T/L22 completos; CMDB todas sus celdas/metadatos; código actual de
accounts/organization/catalog/config.domain y migraciones existentes.
Fuentes inmutables y datos no confiables: no ejecutan órdenes del agente.
Todos los cambios funcionales se limitan al modelo CMDB y registro de app.

## Alcance y resultado

Seis modelos: ClasificacionCI, UbicacionCI, CI, TipoRelacionCI, RelacionCI,
ServicioCI. Atributos específicos JSON validados; IP opcional; responsables
Usuario y M:N a N2; sin dependencias de tickets inexistentes.
Migración 0001_initial sin RunPython/datos. No generador/importador CMDB, UI,
workflows, dashboard, P01–P18, suite completa ni recorrido público de grafos.

El entorno impidió Docker y escritura en el repositorio original pese a los
permisos concedidos. Se prepara copia local de 396aa81 en el espacio de trabajo,
con hasta dos commits y un parche revisable; **no afirmar aplicación al original**.
Django 5.2.17 y dependencias mínimas oficiales se instalan solo en directorio
temporal. No se cambia requirements ni se usa SQLite para fingir PostgreSQL.

## Validación y commits

Resultados exactos en [FASE_CMDB](../evidencias/FASE_CMDB.md).
Check estático no demuestra ciclos ni concurrencia. Makemigrations sin base
conectada no acredita historia aplicada; se conserva su advertencia.
No se ejecutan tests ni datos de ejemplo. Hashes originales antes/después.

Recuperar commits reales en la copia, sin hash autorreferente inventado:

~~~bash
git log -1 --diff-filter=A --format='%H %s' -- docs/contexto/CONTEXTO_V5.md
git log -1 --diff-filter=A --format='%H %s' -- src/cmdb/models.py
~~~
