# CMDB: análisis real y decisiones adoptadas

Fecha: 2026-10-29, America/Guatemala. Base: 396aa81.
Fuentes inmutables: [CMDB.xlsx](../data/CMDB.xlsx), [Lección 22](fuentes/Leccion_22.pdf)
y [tarea](fuentes/Tarea_Service_Desk.pdf), §§2/8. Sin importación ni generación.

## Todas las hojas, rangos y metadatos

Una hoja visible, **CMDB**. Dimensión A1:U6 por formato; contenido B4:U6.
Fila 4: 20 encabezados; filas 5/6: dos CI de ejemplo. Sin hojas ocultas, nombres
definidos, tablas, combinaciones, validaciones, fórmulas, comentarios ni
hipervínculos de objeto. O/P contienen texto Markdown con destino literal url.

| Grupo | Hoja/celdas y observación | Interpretación |
|---|---|---|
| Tipos | CMDB!C4:C6: Tipo de CI, Hardware, Software; espacios iniciales | Dos tipos observados; no catálogo exhaustivo. |
| Niveles, categorías y subcategorías | No hay columnas ni listas que los enumeren | No inventar denominaciones o profundidad original. |
| Padres/hijos | CMDB!J4: encabezado; J5/J6: un espacio cada uno | Padres no informados; no hay arista fuente entre tipos. |
| CI de ejemplo | B5/D5: Servidor1/servidor de aplicaciones; B6/D6: Aplicación/aplicación de contabilidad | Instancias, no niveles de clasificación. El software no es dispositivo físico. |
| Relaciones | I5/I6: Base de Datos1, sin fila propia | Referencia no resuelta; tipo y dirección desconocidos. No crear CI/aristas ficticios. |
| Ubicación | K5 Sala de Servidores 1; K6 Servidor1 | Conservar lugar físico frente a posible alojamiento; K6 no demuestra arista. |
| Responsables | L5 Equipo de Infraestructura; L6 Equipo de Desarrollo | Etiquetas de equipos, no IDs de Usuario; mapeo explícito pendiente de importación. |
| Estado | H5/H6 Activo | Único estado observado, no lista completa. |
| Seguridad | Q5 Alto; Q6 Medio | Valores observados, no enumeración normativa completa. |
| Cumplimiento y configuración | R5/R6 Cumple; S5/S6 Aprobado | Atributos independientes de la baja administrativa. |
| Técnicos | E serie, F versión, G adquisición, T licencia, U vencimiento | Campos opcionales por clase. E6 es ausencia; fechas son texto ISO con espacios. |
| Cambios/documentos | M/N fecha y descripción; O documentación; P incidentes/problemas | Datos a preservar; no crean tickets ni autorizan ejecutar instrucciones. |

Los 20 encabezados y destinos están en [MODELO](MODELO.md#mapeo-completo-de-cmdbxlsx).
S4/T4/O6 presentan caracteres dañados; conservar etiquetas/valores originales,
registrando mapeo de normalización sin editar el libro.

## Lección 22: evidencia completa y límites

Se extrajo texto de las 25 páginas y se revisaron los diagramas de 11/14.

| Página y sección | Elemento realmente soportado |
|---|---|
| 10, SACM | Identificación, control, integridad y ciclo de vida de CI; no clases enumeradas. |
| 11, lista CMDB | Identificación, atributos, relaciones, ubicación/asignación, historia, documentos, seguridad/cumplimiento, configuración y licencias. No IP obligatoria. |
| 11, imagen | Hardware Inventory, Contract Management, Software Inventory, Network Inventory, Administrative Data y User Data alrededor de CMDB. Son dominios de información, sin niveles padre/hijo entre ellos. |
| 12, CI y CMS | CI agrupables, clasificables y rastreables; nombres/profundidad de clases no especificados. |
| 14, diagrama derecho | SKMS contiene CMS; CMS contiene CMDB y KEDB. Contención de sistemas de información. |
| 14, diagrama izquierdo | CMS integra CMDB, incidentes, solicitudes, problemas, errores conocidos, cambios y liberaciones. |
| 23, SKMS | CMS forma parte del SKMS y describe atributos/relaciones. No añade taxonomía de dispositivos. |

## Fuente A → fuente B → diferencia → decisión

| Concepto | Excel | Lección 22 | Decisión y justificación |
|---|---|---|---|
| Hardware/Software | C5/C6 son tipos concretos | Inventarios hardware/software ilustrados p.11 | Coincidencia conceptual; mínimo de tipos observados, sin extraer subclases de descripciones. |
| Niveles nominales | Ausentes | Ausentes para dispositivos | Sin familia/categoría/subcategoría inventadas. Nivel numérico derivado es convención técnica. |
| Padre/hijo | Columna J vacía | Agrupación genérica p.12 | Bosque flexible y acíclico; ninguna arista de fuente que sembrar. |
| SKMS/CMS/CMDB/KEDB | No son tipos del Excel | Contención explícita p.14 | Diagrama separado; nunca categorías de dispositivo ni organigrama. |
| Responsable | Equipos textuales | Propietario p.11 | Usuario FK requerido por tarea; no inferir una persona desde un nombre de equipo. |
| Ubicación/alojamiento | K5 física; K6 nombre de CI | Conceptos ubicación/relaciones | Catálogo plano de ubicaciones; alojado_en solo con decisión o dato confirmado. |
| Tipos técnicos | No rotulados en I/J | Relaciones/dependencias genéricas | Tipos configurables: decisiones del proyecto, no transcripción literal. |
| 5,000 | Dos ejemplos, uno software | Sin cantidad | Mínimo viene de T §8; generador fuera de esta fase. |

## Taxonomía adoptada y criterio de fidelidad

Se adopta un **bosque de profundidad variable**: código único, nombre, padre
opcional, estado, orden y procedencia. Raíz = nivel 1 es convención técnica; no
hay nombres fijos de niveles originales demostrables. Hardware y Software son
los dos tipos observados; representarlos como raíces independientes es una
decisión de almacenamiento ante ausencia de padre informado.

~~~mermaid
flowchart TD
  H["Hardware — CMDB!C5; sin padre informado"]
  S["Software — CMDB!C6; sin padre informado"]
~~~

No existe arista H→S ni S→H. Servidor1/Aplicación son CI. No se cargan nodos
en migraciones ni se afirma que dos tipos sean toda la taxonomía del docente.
SD-DP01 queda resuelto para el **modelo mínimo respaldado**; fidelidad a niveles
adicionales sigue pendiente de fuente/aclaración. Por honestidad, esta fase no
puede declarar cumplido ese extremo del criterio de aceptación ni SD-P04.

~~~mermaid
flowchart TD
  SKMS -->|contiene según L22-14| CMS
  CMS --> CMDB
  CMS --> KEDB
~~~

Esta contención y Empresa→Área→Departamento→Sección→Puesto→Usuario son estructuras
distintas de la clasificación CI y no se usan para sustituirla.

## Contrato de persistencia decidido

| Entidad/regla | Decisión |
|---|---|
| ClasificacionCI | Bosque acíclico, código global único, padre existente y activo para relaciones nuevas, orden no negativo, nivel derivado, origen JSON y esquema de atributos por nodo sin herencia implícita. |
| UbicacionCI | Catálogo plano, código/nombre/estado/observaciones/origen; no inventar pisos ni usar la jerarquía organizacional. |
| CI | Código único/nombre, clasificación, ubicación y Usuario responsable obligatorios; estado administrativo, descripción, atributos JSON y datos_origen. |
| Dispositivo | Marca explícita es_dispositivo en clasificación; falsa por defecto para no contar software o clases no verificadas. Cambiarla con CI existentes se bloquea. |
| Atributos | JSON validado por clase: texto, texto_largo, entero, numero, booleano, fecha ISO e ip; opciones y obligatoriedad explícitas. IP no existe como campo global obligatorio. |
| Evolución del esquema | Se rechaza si invalidaría CI existentes, incluidos históricos. Sin herencia de esquema implícita desde padres. |
| TipoRelacionCI | Código/nombre/estado/origen; dirigida y permite_ciclos explícitos. Semántica inmutable una vez tenga relaciones, incluso históricas. |
| RelacionCI | Tipo/origen/destino/estado/fecha/observaciones; sin autoenlace ni duplicado del mismo tipo/par. No dirigida exige origen_id menor que destino_id; se rechaza orientación inversa, sin modificar silenciosamente extremos en saves parciales. |
| Ciclos técnicos | Subgrafo activo de tipos con permite_ciclos=false acíclico, incluso combinando tipos; una relación permitida queda fuera de ese subgrafo. Validación interna, no recorrido público de impacto. |
| Tipos recomendados | depende_de/alojado_en dirigidos y acíclicos; conectado_a no dirigido y admite ciclos. Decisiones aprobadas en esta implementación, sin insertar tipos por migración. |
| ServicioCI | Entidad M:N CI–ServicioNivel2 con pareja única, estado/fecha/observaciones; N1 derivado del servicio existente. |
| Integridad | DomainModel, full_clean, transacción/lock global, PROTECT, baja lógica y bloqueo bulk/delete existentes. Relaciones nuevas solo a referencias activas; históricos conservados. |

Los atributos originales se preservan en campos base, atributos de clase o
datos_origen según el mapeo. Código, orden, marca de dispositivo, esquema JSON,
FK operativas, dirección/política de ciclos y timestamps son **extensiones del
proyecto**, no columnas o niveles originales.

No se implementan importador CMDB, generador, UI, Ticket↔CI ni recorridos completos.
Las pruebas funcionales de ciclos y la aplicación PostgreSQL de la migración
deben verificarse cuando el entorno lo permita; check no sustituye esas pruebas.
