"""ORM models — Package, Analysis, Alert."""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    JSON, String, Text, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class RegistryType(str, enum.Enum):
    NPM = "npm"
    PYPI = "pypi"


class ThreatLevel(str, enum.Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Package(Base):
    __tablename__ = "packages"

    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    registry = Column(SQLEnum(RegistryType), nullable=False)
    description = Column(Text)
    author = Column(String(255))
    license = Column(String(100))
    repository_url = Column(String(500))
    homepage_url = Column(String(500))
    risk_score = Column(Float, default=0.0)
    threat_level = Column(SQLEnum(ThreatLevel))
    is_malicious = Column(Boolean, default=False)
    weekly_downloads = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True))
    analyzed_at = Column(DateTime(timezone=True), default=_utcnow)

    analyses = relationship("Analysis", back_populates="package", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="package", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Package {self.name}@{self.version}>"


class Analysis(Base):
    __tablename__ = "analyses"

    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False, index=True)

    typosquatting_score = Column(Float, default=0.0)
    code_analysis_score = Column(Float, default=0.0)
    behavior_score = Column(Float, default=0.0)
    maintainer_score = Column(Float, default=0.0)
    dependency_score = Column(Float, default=0.0)

    typosquatting_evidence = Column(JSON)
    code_patterns = Column(JSON)
    behaviors = Column(JSON)
    dependencies = Column(JSON)
    maintainer_flags = Column(JSON)

    confidence = Column(Float, default=0.0)

    package = relationship("Package", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis package_id={self.package_id}>"


class Alert(Base):
    __tablename__ = "alerts"

    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    threat_level = Column(SQLEnum(ThreatLevel))
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    registry_reported = Column(Boolean, default=False)
    blocked_in_ci = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    package = relationship("Package", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert {self.title!r}>"

