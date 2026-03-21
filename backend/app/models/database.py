from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    API_ONLY = "api_only"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    api_keys = relationship("ApiKey", back_populates="user")
    instances = relationship("Instance", back_populates="owner")
    accounts = relationship("MT5Account", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    permissions = Column(Text)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")


class Instance(Base):
    __tablename__ = "instances"

    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    docker_container_id = Column(String(100))
    status = Column(String(20))
    rpyc_port = Column(Integer)
    vnc_port = Column(Integer)
    config = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="instances")
    account = relationship("MT5Account", back_populates="instance", uselist=False)


class MT5Account(Base):
    __tablename__ = "mt5_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    instance_id = Column(String(50), ForeignKey("instances.id"))
    login = Column(String(50))
    server = Column(String(100))
    broker = Column(String(100))
    account_name = Column(String(255))
    is_demo = Column(Boolean, default=True)
    encrypted_password = Column(Text)
    last_connected = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="accounts")
    instance = relationship("Instance", back_populates="account")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    instance_id = Column(String(50))
    alert_type = Column(String(50))
    condition = Column(Text)
    channel = Column(String(50))
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String(100))
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    api_key_id = Column(Integer)
    endpoint = Column(String(200))
    method = Column(String(10))
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
