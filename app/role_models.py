"""Roles por empresa, catálogo de permisos e historial de asignaciones."""
from datetime import datetime
from sqlalchemy import Boolean, Computed, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
from .models import now, Company, CompanyUser


class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = (UniqueConstraint('company_id', 'code', name='uq_role_company_code'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'))
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    company: Mapped[Company] = relationship()


class Permission(Base):
    __tablename__ = 'permissions'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(200))


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))
    permission_id: Mapped[int] = mapped_column(ForeignKey('permissions.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    role: Mapped[Role] = relationship()
    permission: Mapped[Permission] = relationship()


class CompanyUserRole(Base):
    __tablename__ = 'company_user_roles'
    __table_args__ = (
        UniqueConstraint('company_user_id', 'role_id', name='uq_member_role'),
        UniqueConstraint('company_user_id', 'active_slot', name='uq_member_active_role'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_user_id: Mapped[int] = mapped_column(ForeignKey('company_users.id'))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # NULL permite varias asignaciones históricas; 1 solo una activa.
    active_slot: Mapped[int | None] = mapped_column(
        Integer, Computed('CASE WHEN is_active THEN 1 ELSE NULL END'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    company_user: Mapped[CompanyUser] = relationship()
    role: Mapped[Role] = relationship()
