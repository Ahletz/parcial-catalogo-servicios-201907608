# Auditoría de rúbrica

Fuente: ENUNCIADO §9. Fecha: 2026-10-04. Los puntos son pesos del enunciado,
no una nota autoasignada. Resultados finales en [FASE_CIERRE](evidencias/FASE_CIERRE.md).
El estado técnico se cierra únicamente después del harness satisfactorio.

| CRITERIO | PUNTOS | ESTADO | EVIDENCIA | PENDIENTE |
|---|---:|---|---|---|
| Modelo/importación | 15 | Implementado y probado | MODELO_DATOS; FASE_IMPORTACION; tests modelo/parser/persistencia/P06–P08; probe final 12/46 y reimportación. | Ninguno técnico. |
| Funcionalidad | 20 | Implementada y probada | FASE_FUNCIONAL; tests HTTP/CRUD/P04/P05/P09/P10/P11 y probe Gunicorn final. | Revisión humana de UI en evaluación. |
| Autenticación | 10 | Implementada y probada | P01–P03; Argon2id; CSRF/roles/cookies/inactivos; test_web_security. | Ninguno técnico. |
| Context engineering | 10 | Documentado y comprobable | AGENTS, V1/V2/V3; RESOLUCION §7; commits f5f39e3/d513d94/628efa5. | Ninguno técnico. |
| Prompt engineering | 10 | Cinco temas y dos mejoras reales | P01–P05 y revisiones P03/P04 con pruebas comprobadas; RESOLUCION §8. | Versión exacta IA no expuesta: registrar manualmente, sin inventarla. |
| Harness engineering | 10 | Rutina final y ciclos reales | verify.sh/helpers; fallos→correcciones en cuatro evidencias; códigos de salida y datos aislados. | Cerrar con salida final real del harness. |
| Pruebas | 10 | P01–P11 probadas; P12 dirigido probado | 165 tests Django; script operativo P12; matriz individual. | Cerrar ejecución completa final una vez. |
| Docker | 10 | Final construido y P12 dirigido válido | Dockerfile/compose.yaml/.env.example/.dockerignore; healthy/init/web; probe final con DEBUG=false. | Ensayo desde clon limpio y salida final. |
| GitHub/documentación | 5 | Preparación local; entrega remota pendiente | README/RESOLUCION/matriz/evidencias; main/origin verificadas localmente. | Nombre completo; push, acceso/invitación maldanap-usac, tag/SHA y entrega. |
| TOTAL | 100 | No se afirma 100% de cumplimiento ni calificación | Evidencia local separada de entrega remota. | Acciones externas/metadatos mencionados y controles finales por registrar. |

GitHub no se califica completo por mencionar al colaborador. origin/main [gone]
no demuestra ausencia del remoto: falta la referencia de seguimiento local.
La UI no tiene navegador automatizado; sí peticiones Django y HTTP real en
Gunicorn con ambos roles. No se inventan métricas visuales ni verificación remota.
