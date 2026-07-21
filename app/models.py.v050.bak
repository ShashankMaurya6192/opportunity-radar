from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserProfile(Base):
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(120), default="Shashank")
    headline: Mapped[str] = mapped_column(String(300), default="Python Backend Developer")
    years_experience: Mapped[float] = mapped_column(Float, default=5.5)
    skills: Mapped[str] = mapped_column(Text, default="Python,Django,FastAPI,REST APIs,Selenium,Automation,AI integrations,AWS,Docker")
    preferred_roles: Mapped[str] = mapped_column(Text, default="Python Developer,Backend Engineer,Django Developer,FastAPI Developer,AI Automation Engineer")
    preferred_countries: Mapped[str] = mapped_column(Text, default="United States,United Kingdom,Canada,Australia,Europe,Remote")
    preferred_work_mode: Mapped[str] = mapped_column(String(80), default="Remote")
    availability: Mapped[str] = mapped_column(String(120), default="Immediate")
    minimum_match_score: Mapped[int] = mapped_column(Integer, default=60)
    email_signature: Mapped[str] = mapped_column(Text, default="Best regards,\nShashank")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), default="Unknown company")
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(120), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    employee_size: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    services: Mapped[str] = mapped_column(Text, default="")
    github_url: Mapped[str] = mapped_column(String(500), default="")
    careers_url: Mapped[str] = mapped_column(String(500), default="")
    contact_url: Mapped[str] = mapped_column(String(500), default="")
    public_emails: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")

    opportunity_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    combined_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    score_delta: Mapped[int] = mapped_column(Integer, default=0)
    technical_score: Mapped[int] = mapped_column(Integer, default=0)
    hiring_score: Mapped[int] = mapped_column(Integer, default=0)
    contract_score: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    contact_score: Mapped[int] = mapped_column(Integer, default=0)
    score_reasons: Mapped[str] = mapped_column(Text, default="")
    match_reasons: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[str] = mapped_column(String(40), default="NEW", index=True)
    priority: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    source_query: Mapped[str] = mapped_column(String(500), default="")
    first_discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    histories: Mapped[list["ScoreHistory"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    events: Mapped[list["ChangeEvent"]] = relationship(back_populates="company", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(700))
    location: Mapped[str] = mapped_column(String(180), default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="jobs")

class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), default="")
    role: Mapped[str] = mapped_column(String(180), default="")
    email: Mapped[str] = mapped_column(String(300), default="")
    profile_url: Mapped[str] = mapped_column(String(700), default="")
    source: Mapped[str] = mapped_column(String(120), default="Manual")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="contacts")

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(60), default="NOTE")
    title: Mapped[str] = mapped_column(String(250))
    details: Mapped[str] = mapped_column(Text, default="")
    happened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="activities")

class ScoreHistory(Base):
    __tablename__ = "score_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    opportunity_score: Mapped[int] = mapped_column(Integer)
    match_score: Mapped[int] = mapped_column(Integer)
    combined_score: Mapped[int] = mapped_column(Integer)
    technical_score: Mapped[int] = mapped_column(Integer)
    hiring_score: Mapped[int] = mapped_column(Integer)
    contract_score: Mapped[int] = mapped_column(Integer)
    quality_score: Mapped[int] = mapped_column(Integer)
    contact_score: Mapped[int] = mapped_column(Integer)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="histories")

class ChangeEvent(Base):
    __tablename__ = "change_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    details: Mapped[str] = mapped_column(Text, default="")
    importance: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="events")

class DiscoveryCampaign(Base):
    __tablename__ = "discovery_campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    query: Mapped[str] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(180), default="")
    result_limit: Mapped[int] = mapped_column(Integer, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
