import uuid
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0.00)
    service_charge_rate = Column(Numeric(5, 2), nullable=False, default=0.00)
    allow_negative_inventory = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    outlets = relationship("Outlet", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class Outlet(Base):
    __tablename__ = "outlets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(150), nullable=False)
    address = Column(Text, nullable=True)
    payment_timing = Column(
        Enum("PAY_BEFORE_SERVING", "PAY_AFTER_SERVING", name="payment_timing_enum"),
        nullable=False,
        default="PAY_AFTER_SERVING",
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="outlets_tenant_id_id_key"),
    )

    tenant = relationship("Tenant", back_populates="outlets")
    user_roles = relationship(
        "UserOutletRole",
        back_populates="outlet",
        cascade="all, delete-orphan",
        overlaps="outlet_roles,user",
    )
