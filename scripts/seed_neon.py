#!/usr/bin/env python
"""
Seed Neon/Postgres with realistic fake data for smoke testing.

Usage:
  APP_ENV=production DATABASE_URL=postgresql://...sslmode=require \\
    python scripts/seed_neon.py
"""

import datetime as dt
import os
import sys
import uuid

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.database import models as m
from src.database.database import Base


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    sys.exit("DATABASE_URL env var is required (point to Neon/Postgres).")


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_tables():
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def upsert_contact(db, name, phone=None, email=None, tags=None):
    """Create or update a contact keyed by email/phone/name."""
    query = db.query(m.Contact)
    if email:
        query = query.filter(m.Contact.email == email)
    elif phone:
        query = query.filter(m.Contact.phone_number == phone)
    else:
        query = query.filter(m.Contact.name == name)

    contact = query.first()
    if contact:
        if phone:
            contact.phone_number = phone
        if email:
            contact.email = email
        contact.tags = tags or contact.tags
        return contact

    contact = m.Contact(
        name=name,
        phone_number=phone,
        email=email,
        tags=tags or [],
    )
    db.add(contact)
    db.flush()
    return contact


def upsert_channel_identity(db, contact_id, channel, address, verified=False):
    """Ensure a channel identity exists for a contact."""
    existing = (
        db.query(m.ChannelIdentity)
        .filter(
            m.ChannelIdentity.contact_id == contact_id,
            m.ChannelIdentity.channel == channel,
            m.ChannelIdentity.address == address,
        )
        .first()
    )
    if existing:
        existing.verified = existing.verified or verified
        return existing

    identity = m.ChannelIdentity(
        contact_id=contact_id,
        channel=channel,
        address=address,
        verified=verified,
    )
    db.add(identity)
    return identity


def upsert_goal(db, title):
    goal = db.query(m.Goal).filter(m.Goal.title == title).first()
    if goal:
        return goal
    goal = m.Goal(title=title, goal_type="short_term", priority=8)
    db.add(goal)
    db.flush()
    return goal


def upsert_project(db, title, goal):
    project = db.query(m.Project).filter(m.Project.title == title).first()
    if project:
        return project
    project = m.Project(
        title=title,
        description="Seeded demo project for Neon validation.",
        goal_id=goal.id,
        priority=7,
        milestones=[{"name": "MVP", "status": "open"}],
        constraints={"bandwidth": "medium"},
    )
    db.add(project)
    db.flush()
    return project


def upsert_task(db, project):
    task_id = "seed-task-1"
    task = db.query(m.Task).filter(m.Task.task_id == task_id).first()
    if task:
        return task
    task = m.Task(
        task_id=task_id,
        status="planning",
        task="Call Bob about pricing",
        context={"project_id": project.id},
    )
    db.add(task)
    return task


def upsert_project_task(db, project):
    existing = (
        db.query(m.ProjectTask)
        .filter(
            m.ProjectTask.project_id == project.id,
            m.ProjectTask.title == "Prepare demo script",
        )
        .first()
    )
    if existing:
        return existing

    task = m.ProjectTask(
        project_id=project.id,
        title="Prepare demo script",
        status="todo",
        priority=6,
        estimated_minutes=90,
        deadline_type="FLEX",
    )
    db.add(task)
    db.flush()
    return task


def upsert_calendar_block(db, task):
    existing = (
        db.query(m.CalendarBlock)
        .filter(m.CalendarBlock.task_id == task.id)
        .first()
    )
    if existing:
        return existing

    now = dt.datetime.utcnow()
    block = m.CalendarBlock(
        task_id=task.id,
        start_at=now,
        end_at=now + dt.timedelta(hours=1),
        locked=False,
    )
    db.add(block)
    return block


def upsert_pricing_rule(db):
    rule = (
        db.query(m.PricingRule)
        .filter(
            m.PricingRule.provider == "openai",
            m.PricingRule.service == "chat",
        )
        .first()
    )
    if rule:
        return rule

    rule = m.PricingRule(
        provider="openai",
        service="chat",
        service_type="LLM",
        pricing_model="PER_TOKEN",
        unit_costs={"input_token": 0.0000025, "output_token": 0.00001},
        currency="USD",
        effective_date=dt.datetime.utcnow(),
        documentation_url="https://platform.openai.com/pricing",
    )
    db.add(rule)
    return rule


def upsert_cost_event(db, project_id=None, task_id=None):
    event = db.query(m.CostEvent).filter(m.CostEvent.event_id == "seed-cost-1").first()
    if event:
        return event

    event = m.CostEvent(
        event_id="seed-cost-1",
        provider="openai",
        service="chat",
        metric_type="tokens",
        units=1000,
        unit_cost=0.00001,
        total_cost=0.01,
        task_id=task_id,
        project_id=project_id,
        agent_id="seed-agent",
        is_priced=True,
        meta_data={"phase": "planning"},
    )
    db.add(event)
    return event


def upsert_budget(db):
    budget = (
        db.query(m.Budget)
        .filter(m.Budget.scope == "overall", m.Budget.period == "monthly")
        .first()
    )
    if budget:
        return budget

    budget = m.Budget(
        scope="overall",
        period="monthly",
        limit=50.0,
        currency="USD",
        enforcement_mode="warn",
        is_active=True,
    )
    db.add(budget)
    return budget


def upsert_message(db, contact):
    msg = (
        db.query(m.Message)
        .filter(m.Message.twilio_message_sid == "seed-msg-1")
        .first()
    )
    if msg:
        return msg

    msg = m.Message(
        contact_id=contact.id,
        channel="sms",
        direction="outbound",
        timestamp=dt.datetime.utcnow(),
        raw_payload={"seed": True},
        text_content="Test SMS from seed script",
        conversation_id="seed-conv-1",
        twilio_message_sid="seed-msg-1",
        status="sent",
        is_read=True,
    )
    db.add(msg)
    db.flush()
    return msg


def upsert_outbound_approval(db, message):
    approval = (
        db.query(m.OutboundApproval)
        .filter(m.OutboundApproval.message_id == message.id)
        .first()
    )
    if approval:
        return approval

    approval = m.OutboundApproval(
        message_id=message.id,
        approved_by="seed-user",
        approved_at=dt.datetime.utcnow(),
        sent_at=dt.datetime.utcnow(),
        status="approved",
    )
    db.add(approval)
    return approval


def seed():
    ensure_tables()
    db = Session()
    try:
        alice = upsert_contact(
            db,
            name="Alice Johnson",
            phone="+15550000001",
            email="alice@example.com",
            tags=["vip", "partner"],
        )
        bob = upsert_contact(
            db,
            name="Bob Lee",
            phone="+15550000002",
            email="bob@example.com",
            tags=["lead"],
        )

        upsert_channel_identity(db, alice.id, "sms", "+15550000001", verified=True)
        upsert_channel_identity(db, bob.id, "sms", "+15550000002", verified=False)

        goal = upsert_goal(db, title="Launch Pilot")
        project = upsert_project(db, title="AI Caller Rollout", goal=goal)
        project_task = upsert_project_task(db, project)
        upsert_calendar_block(db, project_task)
        upsert_task(db, project)

        msg = upsert_message(db, contact=alice)
        upsert_outbound_approval(db, msg)

        upsert_pricing_rule(db)
        upsert_cost_event(db, project_id=project.id, task_id=project_task.id)
        upsert_budget(db)

        db.commit()
        print("✓ Seed complete against Neon/Postgres.")
    except SQLAlchemyError as err:
        db.rollback()
        print(f"✗ Seed failed: {err}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

