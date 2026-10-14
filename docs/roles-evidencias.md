# Evidencias - Unidad II, Actividad 4

**Enrique Zavala. 14 de octubre de 2026.**

Fuente: `unidad2_actividad_4.pdf`, ocho páginas, suministrado por el autor. Se continuó la API existente y se completó primero la base de roles que aún no tenía.

## Ejecuciones reales

- Regresión y autorización en bases temporales SQLite: **57 pruebas aprobadas** ([registro](evidencias/roles/sqlite-pytest.txt)).
- Autorización contra MySQL aislado: **15 pruebas aprobadas** ([registro](evidencias/roles/mysql-pytest.txt)).
- **28 operaciones ejecutadas en GraphiQL**, con sus respuestas HTTP y comprobaciones SQL ([JSON](evidencias/roles/demostracion.json)).
- MySQL **8.4.11**. Reinicio real de la API: **4 roles y 10 permisos**, sin duplicados ([registro](evidencias/roles/reinicio-mysql.json)).
- `pip check`: sin dependencias rotas. Existe un aviso de deprecación de Starlette/AnyIO; no hubo fallos de pruebas.
- [SELECT final](roles-select.sql) y [resultado TSV](evidencias/roles/role_permissions-final.tsv).
- [Reporte PDF con capturas](../output/pdf/Unidad2_Actividad4_Evidencias.pdf).

Las capturas muestran respuestas reales de la API en GraphiQL. El capturador no simula ni sustituye las respuestas. Los tokens quedan ocultos en la pestaña Headers. Las verificaciones SQL usan conexiones independientes después de cada operación.

## Correspondencia con los requisitos

| Requisito | Implementación y evidencia |
|---|---|
| Cuatro roles y diez permisos | role_models.py, role_catalog.py, catálogos y matriz inicial |
| Permisos de puesto, no de usuario | role_permissions y exigir_permiso en role_service.py |
| Dos capturistas reciben el mismo cambio | María y José rechazados, aceptados y rechazados después de revocar |
| Quitar conserva la fila | Mismo ID y isActive=false; SELECT final incluye las parejas inactivas |
| Pedro cambia de puesto | assignRole, movimiento antes/después e historial con un único rol activo |
| Contador y Consulta conservan sus listas | Comparación de conjuntos antes/después; Luis crea cuenta |
| Solo roles.write cambia listas | Intento de José rechazado; misma operación de Ana aceptada |
| Rechazo no guarda filas | Conteos antes/después en el JSON y pruebas HTTP con verificación SQL |
| Separación por empresa y actor | Pruebas de roles de otra empresa y suplantación del actor contra JWT |
| Reinicio sin duplicar ni reactivar permisos | Reinicio real y prueba de configuración revocada persistente |
| Matriz final igual al documento | 26 parejas activas originales y dos parejas de demostración inactivas |

## Capturas y regla demostrada

### 00 Preparar el puesto inicial de Pedro

**Actor: Ana.** La demostración comienza con Pedro como CONSULTA.

Esperado y obtenido: **OK**.

![00 Preparar el puesto inicial de Pedro](evidencias/roles/capturas/01-00-preparar-el-puesto-inicial-de-pedro.png)

### 01 Catálogos

**Actor: Ana.** La empresa tiene cuatro roles y diez permisos.

Esperado y obtenido: **OK**.

![01 Catálogos](evidencias/roles/capturas/02-01-catalogos.png)

### 02 Configuración inicial ADMINISTRADOR

**Actor: Ana.** Lista vigente del rol ADMINISTRADOR.

Esperado y obtenido: **OK**.

![02 Configuración inicial ADMINISTRADOR](evidencias/roles/capturas/03-02-configuracion-inicial-administrador.png)

### 02 Configuración inicial CONTADOR

**Actor: Ana.** Lista vigente del rol CONTADOR.

Esperado y obtenido: **OK**.

![02 Configuración inicial CONTADOR](evidencias/roles/capturas/04-02-configuracion-inicial-contador.png)

### 02 Configuración inicial CAPTURISTA

**Actor: Ana.** Lista vigente del rol CAPTURISTA.

Esperado y obtenido: **OK**.

![02 Configuración inicial CAPTURISTA](evidencias/roles/capturas/05-02-configuracion-inicial-capturista.png)

### 02 Configuración inicial CONSULTA

**Actor: Ana.** Lista vigente del rol CONSULTA.

Esperado y obtenido: **OK**.

![02 Configuración inicial CONSULTA](evidencias/roles/capturas/06-02-configuracion-inicial-consulta.png)

### 03 Antes de conceder Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"accounts_before": 7, "accounts_after": 7}`.

![03 Antes de conceder Cuenta de María](evidencias/roles/capturas/07-03-antes-de-conceder-cuenta-de-maria.png)

### 03 Antes de conceder Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"accounts_before": 7, "accounts_after": 7}`.

![03 Antes de conceder Cuenta de José](evidencias/roles/capturas/08-03-antes-de-conceder-cuenta-de-jose.png)

### 04 Ana concede accounts.write

**Actor: Ana.** Un cambio en CAPTURISTA beneficia a sus dos integrantes.

Esperado y obtenido: **OK**.

![04 Ana concede accounts.write](evidencias/roles/capturas/09-04-ana-concede-accounts-write.png)

### 05 Con permiso Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **OK**.

Comprobación independiente de almacenamiento: `{"accounts_before": 7, "accounts_after": 8}`.

![05 Con permiso Cuenta de María](evidencias/roles/capturas/10-05-con-permiso-cuenta-de-maria.png)

### 05 Con permiso Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **OK**.

Comprobación independiente de almacenamiento: `{"accounts_before": 8, "accounts_after": 9}`.

![05 Con permiso Cuenta de José](evidencias/roles/capturas/11-05-con-permiso-cuenta-de-jose.png)

### 06 Ana quita accounts.write

**Actor: Ana.** Quitar un permiso desactiva la pareja y conserva el ID.

Esperado y obtenido: **OK**.

Comprobación independiente de almacenamiento: `{"role_permission_id": 27, "is_active": false, "row_preserved": true}`.

![06 Ana quita accounts.write](evidencias/roles/capturas/12-06-ana-quita-accounts-write.png)

### 07 Tras quitar permiso Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"accounts_before": 9, "accounts_after": 9}`.

![07 Tras quitar permiso Cuenta de María](evidencias/roles/capturas/13-07-tras-quitar-permiso-cuenta-de-maria.png)

### 07 Tras quitar permiso Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"accounts_before": 9, "accounts_after": 9}`.

![07 Tras quitar permiso Cuenta de José](evidencias/roles/capturas/14-07-tras-quitar-permiso-cuenta-de-jose.png)

### 08 Pedro como CONSULTA

**Actor: Pedro.** CONSULTA no tiene transactions.write; el rechazo no crea movimientos.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"transactions_before": 2, "transactions_after": 2}`.

![08 Pedro como CONSULTA](evidencias/roles/capturas/15-08-pedro-como-consulta.png)

### 09 Ana cambia el puesto de Pedro

**Actor: Ana.** assignRole deja un solo rol activo y conserva el anterior inactivo.

Esperado y obtenido: **OK**.

![09 Ana cambia el puesto de Pedro](evidencias/roles/capturas/16-09-ana-cambia-el-puesto-de-pedro.png)

### 10 Pedro como CAPTURISTA

**Actor: Pedro.** El mismo token recibe los permisos del nuevo rol.

Esperado y obtenido: **OK**.

![10 Pedro como CAPTURISTA](evidencias/roles/capturas/17-10-pedro-como-capturista.png)

### 11 Historial de Pedro

**Actor: Ana.** Pedro tiene CAPTURISTA activo y CONSULTA inactivo.

Esperado y obtenido: **OK**.

![11 Historial de Pedro](evidencias/roles/capturas/18-11-historial-de-pedro.png)

### 12 Contador sin cambios

**Actor: Ana.** Lista vigente del rol CONTADOR.

Esperado y obtenido: **OK**.

![12 Contador sin cambios](evidencias/roles/capturas/19-12-contador-sin-cambios.png)

### 13 Consulta sin cambios

**Actor: Ana.** Lista vigente del rol CONSULTA.

Esperado y obtenido: **OK**.

![13 Consulta sin cambios](evidencias/roles/capturas/20-13-consulta-sin-cambios.png)

### 14 Contador conserva escritura Cuenta de Luis

**Actor: Luis.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

Esperado y obtenido: **OK**.

Comprobación independiente de almacenamiento: `{"accounts_before": 9, "accounts_after": 10}`.

![14 Contador conserva escritura Cuenta de Luis](evidencias/roles/capturas/21-14-contador-conserva-escritura-cuenta-de-luis.png)

### 15 José intenta configurar permisos

**Actor: José.** Sin roles.write no se cambia la lista ni se inserta la pareja.

Esperado y obtenido: **FORBIDDEN**.

Comprobación independiente de almacenamiento: `{"role_permissions_before": 28, "role_permissions_after": 28}`.

![15 José intenta configurar permisos](evidencias/roles/capturas/22-15-jose-intenta-configurar-permisos.png)

### 16 Ana agrega concepts.write a CONSULTA

**Actor: Ana.** Con roles.write la misma operación sí se permite.

Esperado y obtenido: **OK**.

![16 Ana agrega concepts.write a CONSULTA](evidencias/roles/capturas/23-16-ana-agrega-concepts-write-a-consulta.png)

### 17 Ana restaura CONSULTA

**Actor: Ana.** La pareja queda inactiva y CONSULTA vuelve a ser de lectura.

Esperado y obtenido: **OK**.

![17 Ana restaura CONSULTA](evidencias/roles/capturas/24-17-ana-restaura-consulta.png)

### 18 Matriz final ADMINISTRADOR

**Actor: Ana.** Lista vigente del rol ADMINISTRADOR.

Esperado y obtenido: **OK**.

![18 Matriz final ADMINISTRADOR](evidencias/roles/capturas/25-18-matriz-final-administrador.png)

### 18 Matriz final CONTADOR

**Actor: Ana.** Lista vigente del rol CONTADOR.

Esperado y obtenido: **OK**.

![18 Matriz final CONTADOR](evidencias/roles/capturas/26-18-matriz-final-contador.png)

### 18 Matriz final CAPTURISTA

**Actor: Ana.** Lista vigente del rol CAPTURISTA.

Esperado y obtenido: **OK**.

![18 Matriz final CAPTURISTA](evidencias/roles/capturas/27-18-matriz-final-capturista.png)

### 18 Matriz final CONSULTA

**Actor: Ana.** Lista vigente del rol CONSULTA.

Esperado y obtenido: **OK**.

![18 Matriz final CONSULTA](evidencias/roles/capturas/28-18-matriz-final-consulta.png)
