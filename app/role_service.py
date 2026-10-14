"""Autorización por membresía autenticada y lista vigente del rol en la empresa."""
from sqlalchemy import select
from . import models as m
from .service import Service, fail, identifier


class RoleService(Service):
    def membership(self, company_id):
        user = self.actor()
        # Orden común para escrituras y cambios de configuración. El candado dura hasta commit.
        company = self.db.scalar(select(m.Company).where(m.Company.id == company_id).with_for_update())
        member = self.db.scalar(select(m.CompanyUser).where(
            m.CompanyUser.company_id == company_id, m.CompanyUser.user_id == user.id,
            m.CompanyUser.is_active.is_(True)))
        if not company or not company.is_active or not member:
            fail('No tienes autorización en esta empresa.', 'FORBIDDEN')
        if self.actor_company_user_id is not None and member.id != identifier(self.actor_company_user_id):
            fail('actorCompanyUserId no corresponde al usuario autenticado en esta empresa.', 'FORBIDDEN')
        return member

    def has_permission(self, member, code):
        return self.db.scalar(select(m.RolePermission.id).join(m.Permission).join(m.Role).join(
            m.CompanyUserRole, m.CompanyUserRole.role_id == m.Role.id).where(
            m.CompanyUserRole.company_user_id == member.id, m.CompanyUserRole.is_active.is_(True),
            m.Role.company_id == member.company_id, m.Role.is_active.is_(True),
            m.RolePermission.is_active.is_(True), m.Permission.code == code)) is not None

    def exigir_permiso(self, company_id, code):
        member = self.membership(company_id)
        if not self.has_permission(member, code):
            fail(f'El rol no tiene el permiso {code}.', 'FORBIDDEN')
        return member

    def role_company(self, company_id=None):
        if company_id is not None:
            return identifier(company_id)
        user = self.actor()
        stmt = select(m.CompanyUser).join(m.Company).where(
            m.CompanyUser.user_id == user.id, m.CompanyUser.is_active.is_(True), m.Company.is_active.is_(True))
        if self.actor_company_user_id is not None:
            stmt = stmt.where(m.CompanyUser.id == identifier(self.actor_company_user_id))
        members = list(self.db.scalars(stmt))
        if not members:
            fail('Membresía no disponible.', 'FORBIDDEN')
        if len(members) != 1:
            fail('Indica companyId o actorCompanyUserId para seleccionar la empresa.')
        return members[0].company_id

    def roles(self, company_id=None):
        cid = self.role_company(company_id)
        self.exigir_permiso(cid, 'roles.read')
        return list(self.db.scalars(select(m.Role).where(m.Role.company_id == cid).order_by(m.Role.code)))

    def permissions(self, company_id=None):
        self.exigir_permiso(self.role_company(company_id), 'roles.read')
        return list(self.db.scalars(select(m.Permission).order_by(m.Permission.code)))

    def role(self, role_id, permission):
        self.actor()
        role = self.db.get(m.Role, identifier(role_id))
        if not role:
            fail('Rol inexistente.', 'NOT_FOUND')
        self.exigir_permiso(role.company_id, permission)
        if not role.is_active:
            fail('El rol está inactivo.', 'FORBIDDEN')
        return role

    def role_permissions(self, role_id, active_only=True):
        role = self.role(role_id, 'roles.read')
        stmt = select(m.RolePermission).where(m.RolePermission.role_id == role.id).order_by(m.RolePermission.id)
        if active_only:
            stmt = stmt.where(m.RolePermission.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def assign_permission(self, role_id, permission_id, remove=False):
        role = self.role(role_id, 'roles.write')
        permission = self.db.get(m.Permission, identifier(permission_id))
        if not permission:
            fail('Permiso inexistente.', 'NOT_FOUND')
        link = self.db.scalar(select(m.RolePermission).where(
            m.RolePermission.role_id == role.id, m.RolePermission.permission_id == permission.id))
        if remove:
            if not link:
                fail('La pareja rol-permiso no existe.', 'NOT_FOUND')
            link.is_active = False
        elif link:
            if link.is_active:
                fail('El permiso ya está activo en este rol.', 'CONFLICT')
            link.is_active = True
        else:
            link = m.RolePermission(role_id=role.id, permission_id=permission.id)
            self.db.add(link)
        self.db.flush()
        return link

    def assign_role(self, company_user_id, role_id):
        role = self.role(role_id, 'roles.write')
        member = self.db.get(m.CompanyUser, identifier(company_user_id))
        if not member or not member.is_active or not member.user.is_active:
            fail('Membresía inactiva o inexistente.', 'FORBIDDEN')
        if member.company_id != role.company_id:
            fail('El rol y la membresía deben pertenecer a la misma empresa.', 'FORBIDDEN')
        if member.is_admin and role.code != 'ADMINISTRADOR':
            fail('El administrador principal conserva el rol ADMINISTRADOR.', 'CONFLICT')
        links = list(self.db.scalars(select(m.CompanyUserRole).where(
            m.CompanyUserRole.company_user_id == member.id).with_for_update()))
        target = next((x for x in links if x.role_id == role.id), None)
        for link in links:
            link.is_active = False
        self.db.flush()  # Libera la posición única antes de activar el destino.
        if target is None:
            target = m.CompanyUserRole(company_user_id=member.id, role_id=role.id)
            self.db.add(target)
        target.is_active = True
        self.db.flush()
        return target

    def company_user_roles(self, company_user_id, active_only=True):
        self.actor()
        member = self.db.get(m.CompanyUser, identifier(company_user_id))
        if not member:
            fail('Membresía no disponible.', 'FORBIDDEN')
        self.exigir_permiso(member.company_id, 'roles.read')
        stmt = select(m.CompanyUserRole).where(m.CompanyUserRole.company_user_id == member.id)
        if active_only:
            stmt = stmt.where(m.CompanyUserRole.is_active.is_(True))
        return list(self.db.scalars(stmt.order_by(m.CompanyUserRole.id)))
