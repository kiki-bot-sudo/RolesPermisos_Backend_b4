# Unidad II - Actividad 4

## Configuración de permisos para diferentes roles

**Autor: Enrique Zavala. Entrega individual.**

La entrega continúa el Sistema General de Ingresos de esta carpeta. Integra roles y permisos en la API financiera existente.

## Contenido

- Código de empresas, usuarios, autenticación y finanzas con autorización por roles.
- Cuatro roles por empresa, diez permisos y tablas `role_permissions` y `company_user_roles`.
- Consultas y mutaciones GraphQL del documento, con validación de actor contra JWT.
- MySQL 8.4, Dockerfile y Compose.
- Carga de Ana, Luis, María, José y Pedro y demostración de las cuatro partes.
- Capturas reales de GraphiQL con su regla y reporte PDF.
- SELECT final, parejas inactivas conservadas y reinicio sin duplicados.
- Pruebas en SQLite y en una base MySQL independiente, con informes de ejecución.

## Revisión

Sigue `README.md` para generar las claves propias, iniciar Docker y ejecutar `scripts/demo_roles.py --docker`. Abre `http://127.0.0.1:8008/graphql`. La guía manual está en `docs/roles-operaciones.md`; los resultados y la correspondencia con los requisitos están en `docs/roles-evidencias.md`.

El ZIP no incluye contraseñas locales, tokens, `.env`, bases de datos ni entornos virtuales. El docente puede generar sus datos al ejecutar la carga. Los IDs de las evidencias corresponden a la ejecución documentada y pueden variar en otra instalación.

El envío al docente corresponde al autor. Esta entrega no se ha enviado ni publicado.
