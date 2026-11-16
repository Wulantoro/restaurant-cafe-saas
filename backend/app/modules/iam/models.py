import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    password_hash = Column(Text, nullable=False)
    is_central_admin = Column(Boolean, nullable=False, default=False)
    is_owner = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="users_tenant_id_email_key"),
        UniqueConstraint("tenant_id", "id", name="users_tenant_id_id_key"),
    )

    tenant = relationship("Tenant", back_populates="users")
    outlet_roles = relationship(
        "UserOutletRole",
        back_populates="user",
        cascade="all, delete-orphan",
        overlaps="outlet,user_roles",
    )


class UserOutletRole(Base):
    __tablename__ = "user_outlet_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    outlet_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            ondelete="CASCADE",
            name="user_outlet_roles_tenant_id_user_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "outlet_id"],
            ["outlets.tenant_id", "outlets.id"],
            ondelete="CASCADE",
            name="user_outlet_roles_tenant_id_outlet_id_fkey",
        ),
        UniqueConstraint("tenant_id", "user_id", "outlet_id", "role", name="user_outlet_roles_tenant_id_user_id_outlet_id_role_key"),
    )

    user = relationship("User", back_populates="outlet_roles")
    outlet = relationship("Outlet", back_populates="user_roles", overlaps="outlet_roles,user")
