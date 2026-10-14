# Unidad II - Actividad 4: configuración de permisos por roles

**Enrique Zavala. Entrega individual.** Actividad basada en `unidad2_actividad_4.pdf` (8 páginas), integrada en el Sistema General de Ingresos existente. Conserva FastAPI, Strawberry, JWT, Argon2id, empresas, usuarios y finanzas. La actividad financiera anterior se conserva en [su README histórico](docs/README-finanzas.md).

## Ejecutar con MySQL y Docker

Desde PowerShell en `codigo`, con Docker Desktop abierto y el entorno `env` creado:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env.docker)) { .\env\Scripts\python.exe -m app.init_docker }
docker compose --env-file .env.docker up -d --build
.\env\Scripts\python.exe scripts/demo_roles.py --docker
```

Abre **http://127.0.0.1:8008/graphql**. MySQL escucha en `127.0.0.1:3307`. Docker usa su propia base, independiente de los datos SQLite existentes. El puerto 8008 evita interferir con el servidor local del puerto 8000.

Las credenciales de las cinco personas están en `.roles-credentials.json`; los IDs de MySQL, en `.roles-demo.mysql.json`. Son privados y no se empaquetan. La demostración puede repetirse: prepara a Pedro como CONSULTA y termina con él como CAPTURISTA. La matriz final de los cuatro roles vuelve a la inicial.

Para detener conservando la base:

```powershell
docker compose --env-file .env.docker down
```

Conserva `.env.docker` y el volumen `mysql_data`; no agregues `-v` al comando. En cada instalación nueva se generan secretos propios.

## Ejecutar con Python local y SQLite

Si aún no existe el entorno, créalo con `python -m venv env`. No es necesario activarlo para usar su ejecutable:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { .\env\Scripts\python.exe -m app.init_config }
.\env\Scripts\python.exe -m app.init_db
.\env\Scripts\python.exe -m app.seed_roles
.\env\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abre **http://127.0.0.1:8000/graphql**. Los IDs locales están en `.roles-demo.json`. La carga `app.seed_roles` conserva puestos y permisos ya configurados. `app.seed` sigue disponible para la demostración financiera anterior. Ejecuta siempre desde `codigo`, pues SQLite usa `./app.db`.

## Probar en Strawberry / GraphiQL

1. Abre localmente `.roles-credentials.json` y usa los datos de Ana en `login`.
2. Copia el token a **Headers**: `{"Authorization":"Bearer TU_TOKEN"}`.
3. Consulta `roles` y `permissions` y usa sus IDs en las mutaciones.
4. Cambia el token para probar como otra persona. `actorCompanyUserId` debe corresponder al usuario autenticado y la empresa elegida; no permite suplantar a Ana.

[Guía completa de operaciones, variables y resultados esperados](docs/roles-operaciones.md). [Contrato GraphQL](schema.graphql). Los tokens expiran a los 30 minutos.

## Matriz inicial y final

| Permiso | ADMINISTRADOR | CONTADOR | CAPTURISTA | CONSULTA |
|---|:---:|:---:|:---:|:---:|
| company.users.read | Sí | Sí | No | Sí |
| company.users.write | Sí | No | No | No |
| accounts.read | Sí | Sí | Sí | Sí |
| accounts.write | Sí | Sí | No | No |
| concepts.read | Sí | Sí | Sí | Sí |
| concepts.write | Sí | Sí | No | No |
| transactions.read | Sí | Sí | Sí | Sí |
| transactions.write | Sí | Sí | Sí | No |
| roles.read | Sí | Sí | No | No |
| roles.write | Sí | No | No | No |

Ana es ADMINISTRADOR con `isAdmin=true`; Luis es CONTADOR; María y José son CAPTURISTA. Pedro empieza como CONSULTA y cambia a CAPTURISTA durante el ejercicio. Las membresías normales nuevas empiezan como CAPTURISTA; `assignRole` cambia su puesto. Esa misma asignación inicial se incorpora a las membresías existentes que no tenían roles.

## Implementación

- `roles`: cuatro puestos por empresa. `permissions`: diez acciones globales. `role_permissions`: lista de cada rol. `company_user_roles`: historial de puestos. No hay permisos individuales en `User`.
- `exigir_permiso` consulta membresía, empresa, rol y permiso activos antes de escribir. `isAdmin` no omite esta comprobación. Los cambios se aplican incluso con el mismo JWT: el token identifica a la persona y no copia sus permisos.
- Agregar una pareja activa produce `CONFLICT`. Reactivar una inactiva conserva su ID. Quitar conserva la fila con `isActive=false`; repetir la eliminación de una pareja existente devuelve la misma fila inactiva.
- `assignRole` desactiva el anterior antes de activar el destino. Una restricción única con columna calculada impide dos roles activos incluso fuera de GraphQL. El administrador principal conserva ADMINISTRADOR.
- No se permiten roles ni membresías de otra empresa. Si una persona tiene varias empresas, debe seleccionar una al consultar los catálogos de roles.
- SQLite serializa con `BEGIN IMMEDIATE`; MySQL usa InnoDB, aislamiento READ COMMITTED y bloqueo de la empresa antes de comprobar permisos. Cada resolver usa una transacción; un rechazo revierte sus escrituras.
- El arranque completa catálogos ausentes sin restaurar permisos quitados. Las restricciones únicas y un candado de inicialización en MySQL evitan duplicados durante reinicios.
- Se conservan las tablas y los datos existentes. Los tamaños explícitos de texto permiten crear el modelo en MySQL. Los montos siguen siendo decimales exactos almacenados como texto.
- Se preservan los campos y argumentos anteriores. Se agregan operaciones de roles y el argumento opcional `actorCompanyUserId` en operaciones protegidas. JWT sigue siendo obligatorio; bootstrap solo aprovisiona la empresa y el primer administrador.

## Pruebas y entrega

```powershell
.\env\Scripts\python.exe -m pytest -v
.\env\Scripts\python.exe scripts/test_mysql.py
.\env\Scripts\python.exe scripts/demo_roles.py --docker
.\env\Scripts\python.exe scripts/package_delivery.py
```

Las pruebas habituales usan bases temporales SQLite. `test_mysql.py` crea una base MySQL aislada `test_roles_*`, ejecuta los casos de roles y elimina solamente esa base de pruebas.

[Evidencias y correspondencia con el PDF](docs/roles-evidencias.md): capturas reales, regla junto a cada captura, respuestas HTTP, SELECT final y reinicio. Las evidencias financieras anteriores permanecen como registros históricos.

Para repetir capturas instala Playwright (`npm install playwright`, `npx playwright install chromium`), ejecuta `node scripts/capture_roles.cjs` y, en otra terminal, `python scripts/demo_roles.py --docker --capture-url http://127.0.0.1:8019/capture`. No hace falta Playwright para usar la API. El capturador ejecuta las operaciones en GraphiQL y captura sus respuestas reales sin mostrar los tokens. Ctrl+C lo detiene.
