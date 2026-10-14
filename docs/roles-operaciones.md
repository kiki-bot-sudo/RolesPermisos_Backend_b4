# Guía de GraphiQL - Unidad II, Actividad 4

La demostración registrada usa MySQL en http://127.0.0.1:8008/graphql. Los IDs de los ejemplos corresponden a esa ejecución. Consulta `.roles-demo.mysql.json`, `roles` y `permissions` para obtener los tuyos.

## Iniciar sesión

Usa los valores privados de `.roles-credentials.json` en Variables:

```graphql
mutation Login($input: LoginInput!) {
  login(input: $input) { token tokenType user { id name email } }
}
```

```json
{"input":{"email":"ana.roles@example.com","password":"COPIA_LA_CONTRASEÑA_LOCAL"}}
```

Copia el token retornado a Headers:

```json
{"Authorization":"Bearer TU_TOKEN"}
```

Para ejecutar como otra persona, vuelve a iniciar sesión con sus credenciales y cambia el token. `actorCompanyUserId` debe ser su propia membresía. Los ejemplos de abajo indican el actor y la regla.

Los cambios de permisos y de puesto se aplican con el mismo token, sin volver a iniciar sesión. Las operaciones que rechazan devuelven HTTP 200 con `errors[].extensions.code=FORBIDDEN`; comprueba el JSON.

## 00 Preparar el puesto inicial de Pedro

**Actor: Ana.** La demostración comienza con Pedro como CONSULTA.

```graphql
mutation ($u: ID!, $r: ID!) {
  assignRole(input: {companyUserId: $u, roleId: $r}) {
    id
    isActive
    role {
      code
    }
  }
}
```

```json
{
  "u": "5",
  "r": "4"
}
```

Resultado esperado: **OK**.

## 01 Catálogos

**Actor: Ana.** La empresa tiene cuatro roles y diez permisos.

```graphql
query ($c: ID!) {
  roles(companyId: $c) {
    id
    code
  }
  permissions(companyId: $c) {
    id
    code
  }
}
```

```json
{
  "c": "1"
}
```

Resultado esperado: **OK**.

## 02 Configuración inicial ADMINISTRADOR

**Actor: Ana.** Lista vigente del rol ADMINISTRADOR.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "1"
}
```

Resultado esperado: **OK**.

## 02 Configuración inicial CONTADOR

**Actor: Ana.** Lista vigente del rol CONTADOR.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "2"
}
```

Resultado esperado: **OK**.

## 02 Configuración inicial CAPTURISTA

**Actor: Ana.** Lista vigente del rol CAPTURISTA.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "3"
}
```

Resultado esperado: **OK**.

## 02 Configuración inicial CONSULTA

**Actor: Ana.** Lista vigente del rol CONSULTA.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4"
}
```

Resultado esperado: **OK**.

## 03 Antes de conceder Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "María 03 Antes de conceder 33333e04",
  "actor": "3"
}
```

Resultado esperado: **FORBIDDEN**.

## 03 Antes de conceder Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "José 03 Antes de conceder 33333e04",
  "actor": "4"
}
```

Resultado esperado: **FORBIDDEN**.

## 04 Ana concede accounts.write

**Actor: Ana.** Un cambio en CAPTURISTA beneficia a sus dos integrantes.

```graphql
mutation ($r: ID!, $p: ID!, $actor: ID!) {
  assignPermissionToRole(
    input: {roleId: $r, permissionId: $p}
    actorCompanyUserId: $actor
  ) {
    id
    isActive
    role {
      code
    }
    permission {
      code
    }
  }
}
```

```json
{
  "r": "3",
  "p": "4",
  "actor": "1"
}
```

Resultado esperado: **OK**.

## 05 Con permiso Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "María 05 Con permiso 33333e04",
  "actor": "3"
}
```

Resultado esperado: **OK**.

## 05 Con permiso Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "José 05 Con permiso 33333e04",
  "actor": "4"
}
```

Resultado esperado: **OK**.

## 06 Ana quita accounts.write

**Actor: Ana.** Quitar un permiso desactiva la pareja y conserva el ID.

```graphql
mutation ($r: ID!, $p: ID!, $actor: ID!) {
  removePermissionFromRole(
    input: {roleId: $r, permissionId: $p}
    actorCompanyUserId: $actor
  ) {
    id
    isActive
    role {
      code
    }
    permission {
      code
    }
  }
}
```

```json
{
  "r": "3",
  "p": "4",
  "actor": "1"
}
```

Resultado esperado: **OK**.

## 07 Tras quitar permiso Cuenta de María

**Actor: María.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "María 07 Tras quitar permiso 33333e04",
  "actor": "3"
}
```

Resultado esperado: **FORBIDDEN**.

## 07 Tras quitar permiso Cuenta de José

**Actor: José.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "José 07 Tras quitar permiso 33333e04",
  "actor": "4"
}
```

Resultado esperado: **FORBIDDEN**.

## 08 Pedro como CONSULTA

**Actor: Pedro.** CONSULTA no tiene transactions.write; el rechazo no crea movimientos.

```graphql
mutation ($a: ID!, $c: ID!, $actor: ID!) {
  createTransaction(
    input: {accountId: $a, conceptId: $c, transactionType: INCOME, amount: "125.50"}
    actorCompanyUserId: $actor
  ) {
    id
    amount
    capturedBy
  }
}
```

```json
{
  "a": "1",
  "c": "1",
  "actor": "5"
}
```

Resultado esperado: **FORBIDDEN**.

## 09 Ana cambia el puesto de Pedro

**Actor: Ana.** assignRole deja un solo rol activo y conserva el anterior inactivo.

```graphql
mutation ($u: ID!, $r: ID!, $actor: ID!) {
  assignRole(input: {companyUserId: $u, roleId: $r}, actorCompanyUserId: $actor) {
    id
    isActive
    role {
      code
    }
  }
}
```

```json
{
  "u": "5",
  "r": "3",
  "actor": "1"
}
```

Resultado esperado: **OK**.

## 10 Pedro como CAPTURISTA

**Actor: Pedro.** El mismo token recibe los permisos del nuevo rol.

```graphql
mutation ($a: ID!, $c: ID!, $actor: ID!) {
  createTransaction(
    input: {accountId: $a, conceptId: $c, transactionType: INCOME, amount: "125.50"}
    actorCompanyUserId: $actor
  ) {
    id
    amount
    capturedBy
  }
}
```

```json
{
  "a": "1",
  "c": "1",
  "actor": "5"
}
```

Resultado esperado: **OK**.

## 11 Historial de Pedro

**Actor: Ana.** Pedro tiene CAPTURISTA activo y CONSULTA inactivo.

```graphql
query ($u: ID!) {
  companyUserRoles(companyUserId: $u, activeOnly: false) {
    id
    isActive
    role {
      code
    }
  }
}
```

```json
{
  "u": "5"
}
```

Resultado esperado: **OK**.

## 12 Contador sin cambios

**Actor: Ana.** Lista vigente del rol CONTADOR.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "2"
}
```

Resultado esperado: **OK**.

## 13 Consulta sin cambios

**Actor: Ana.** Lista vigente del rol CONSULTA.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4"
}
```

Resultado esperado: **OK**.

## 14 Contador conserva escritura Cuenta de Luis

**Actor: Luis.** El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.

```graphql
mutation ($c: ID!, $n: String!, $actor: ID!) {
  createAccount(
    input: {companyId: $c, name: $n, accountType: CASH}
    actorCompanyUserId: $actor
  ) {
    id
    name
    companyId
  }
}
```

```json
{
  "c": "1",
  "n": "Luis 14 Contador conserva escritura 33333e04",
  "actor": "2"
}
```

Resultado esperado: **OK**.

## 15 José intenta configurar permisos

**Actor: José.** Sin roles.write no se cambia la lista ni se inserta la pareja.

```graphql
mutation ($r: ID!, $p: ID!, $actor: ID!) {
  assignPermissionToRole(
    input: {roleId: $r, permissionId: $p}
    actorCompanyUserId: $actor
  ) {
    id
    isActive
    role {
      code
    }
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4",
  "p": "6",
  "actor": "1"
}
```

Resultado esperado: **FORBIDDEN**.

## 16 Ana agrega concepts.write a CONSULTA

**Actor: Ana.** Con roles.write la misma operación sí se permite.

```graphql
mutation ($r: ID!, $p: ID!, $actor: ID!) {
  assignPermissionToRole(
    input: {roleId: $r, permissionId: $p}
    actorCompanyUserId: $actor
  ) {
    id
    isActive
    role {
      code
    }
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4",
  "p": "6",
  "actor": "1"
}
```

Resultado esperado: **OK**.

## 17 Ana restaura CONSULTA

**Actor: Ana.** La pareja queda inactiva y CONSULTA vuelve a ser de lectura.

```graphql
mutation ($r: ID!, $p: ID!, $actor: ID!) {
  removePermissionFromRole(
    input: {roleId: $r, permissionId: $p}
    actorCompanyUserId: $actor
  ) {
    id
    isActive
    role {
      code
    }
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4",
  "p": "6",
  "actor": "1"
}
```

Resultado esperado: **OK**.

## 18 Matriz final ADMINISTRADOR

**Actor: Ana.** Lista vigente del rol ADMINISTRADOR.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "1"
}
```

Resultado esperado: **OK**.

## 18 Matriz final CONTADOR

**Actor: Ana.** Lista vigente del rol CONTADOR.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "2"
}
```

Resultado esperado: **OK**.

## 18 Matriz final CAPTURISTA

**Actor: Ana.** Lista vigente del rol CAPTURISTA.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "3"
}
```

Resultado esperado: **OK**.

## 18 Matriz final CONSULTA

**Actor: Ana.** Lista vigente del rol CONSULTA.

```graphql
query ($r: ID!) {
  rolePermissions(roleId: $r) {
    id
    isActive
    permission {
      code
    }
  }
}
```

```json
{
  "r": "4"
}
```

Resultado esperado: **OK**.
