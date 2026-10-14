"""Contrato de roles de Unidad II, Actividad 4. JWT conserva la autenticación previa."""
import strawberry
from strawberry.types import Info
from .schema import Time, execute


@strawberry.type
class Role:
    id: strawberry.ID
    company_id: strawberry.ID
    code: str
    name: str
    is_active: bool


@strawberry.type
class Permission:
    id: strawberry.ID
    code: str
    name: str


@strawberry.type
class RolePermission:
    id: strawberry.ID
    role_id: strawberry.ID
    permission_id: strawberry.ID
    is_active: bool
    created_at: Time
    role: Role
    permission: Permission


@strawberry.type
class CompanyUserRole:
    id: strawberry.ID
    company_user_id: strawberry.ID
    role_id: strawberry.ID
    is_active: bool
    created_at: Time
    role: Role


@strawberry.input
class AssignPermissionToRoleInput:
    role_id: strawberry.ID
    permission_id: strawberry.ID


@strawberry.input
class AssignRoleInput:
    company_user_id: strawberry.ID
    role_id: strawberry.ID


def role_value(kind, obj):
    values = {}
    for key in kind.__dataclass_fields__:
        value = getattr(obj, key)
        if key in ('role', 'permission'):
            value = role_value(Role if key == 'role' else Permission, value)
        elif key == 'id' or key.endswith('_id'):
            value = strawberry.ID(str(value))
        values[key] = value
    return kind(**values)


@strawberry.type
class RoleQuery:
    @strawberry.field
    def roles(self, info: Info, company_id: strawberry.ID | None = None,
              actor_company_user_id: strawberry.ID | None = None) -> list[Role]:
        return execute(info, lambda s: [role_value(Role, r) for r in s.roles(company_id)], actor_company_user_id)

    @strawberry.field
    def permissions(self, info: Info, company_id: strawberry.ID | None = None,
                    actor_company_user_id: strawberry.ID | None = None) -> list[Permission]:
        return execute(info, lambda s: [role_value(Permission, p) for p in s.permissions(company_id)], actor_company_user_id)

    @strawberry.field
    def role_permissions(self, info: Info, role_id: strawberry.ID, active_only: bool = True,
                         actor_company_user_id: strawberry.ID | None = None) -> list[RolePermission]:
        return execute(info, lambda s: [role_value(RolePermission, p) for p in s.role_permissions(role_id, active_only)],
                       actor_company_user_id)

    @strawberry.field
    def company_user_roles(self, info: Info, company_user_id: strawberry.ID, active_only: bool = True,
                           actor_company_user_id: strawberry.ID | None = None) -> list[CompanyUserRole]:
        return execute(info, lambda s: [role_value(CompanyUserRole, p) for p in s.company_user_roles(company_user_id, active_only)],
                       actor_company_user_id)


@strawberry.type
class RoleMutation:
    @strawberry.mutation
    def assign_permission_to_role(self, info: Info, input: AssignPermissionToRoleInput,
                                  actor_company_user_id: strawberry.ID | None = None) -> RolePermission:
        return execute(info, lambda s: role_value(RolePermission, s.assign_permission(input.role_id, input.permission_id)),
                       actor_company_user_id)

    @strawberry.mutation
    def remove_permission_from_role(self, info: Info, input: AssignPermissionToRoleInput,
                                    actor_company_user_id: strawberry.ID | None = None) -> RolePermission:
        return execute(info, lambda s: role_value(RolePermission, s.assign_permission(input.role_id, input.permission_id, True)),
                       actor_company_user_id)

    @strawberry.mutation
    def assign_role(self, info: Info, input: AssignRoleInput,
                    actor_company_user_id: strawberry.ID | None = None) -> CompanyUserRole:
        return execute(info, lambda s: role_value(CompanyUserRole, s.assign_role(input.company_user_id, input.role_id)),
                       actor_company_user_id)
