"""Data model:
Target 1..N Scan 1..N Finding ; Scan 1..1 Analysis ; Scan 1..N Action
Designed so the agent can diff current vs previous scan per target.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean, Index
)
from sqlalchemy.orm import relationship

from app.database.db import Base


class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True)
    url = Column(String(512), unique=True, nullable=False)
    label = Column(String(128), default="")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan",
                         order_by="desc(Scan.created_at)")


class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status = Column(String(32), default="pending")  # pending|running|done|error
    raw = Column(JSON, default=dict)                # union of all checker outputs
    severity = Column(String(16), default="LOW")    # LOW|MEDIUM|HIGH|CRITICAL
    summary = Column(Text, default="")              # short AI summary
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    target = relationship("Target", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="scan", uselist=False,
                            cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    check = Column(String(64), nullable=False)      # http|ssl|git|headers
    severity = Column(String(16), default="LOW")
    title = Column(String(256), nullable=False)
    detail = Column(Text, default="")
    data = Column(JSON, default=dict)

    scan = relationship("Scan", back_populates="findings")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), unique=True, nullable=False)
    severity = Column(String(16), default="LOW")
    reasoning = Column(Text, default="")
    risk = Column(Text, default="")
    mitigation = Column(Text, default="")
    model = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="analysis")


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    kind = Column(String(32), nullable=False)       # telegram|report|solana_proof
    status = Column(String(32), default="ok")       # ok|skipped|error
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="actions")


Index("ix_scans_target_created", Scan.target_id, Scan.created_at.desc())
