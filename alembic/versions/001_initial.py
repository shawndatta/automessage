"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-09-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("llm", sa.JSON(), nullable=True),
        sa.Column("onboarded", sa.Boolean(), nullable=False),
        sa.Column("encryption_check", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "channel_account",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("credentials", sa.JSON(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "flow",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("trigger", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "kb_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "processed_event",
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("dedupe_key"),
    )
    op.create_table(
        "contact",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("channel_account_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("subscribed", sa.Boolean(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["channel_account_id"], ["channel_account.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_account_id", "external_id", name="uq_contact_channel_external"),
    )
    op.create_index("ix_contact_channel_account_id", "contact", ["channel_account_id"])
    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["kb_document.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kb_chunk_document_id", "kb_chunk", ["document_id"])
    op.create_table(
        "contact_tag",
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contact.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("contact_id", "tag_id"),
    )
    op.create_table(
        "conversation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contact.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_contact_id", "conversation", ["contact_id"])
    op.create_table(
        "flow_run",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flow_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("current_node_id", sa.String(length=128), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("wake_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("awaiting_field", sa.String(length=128), nullable=True),
        sa.Column("exec_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contact.id"]),
        sa.ForeignKeyConstraint(["flow_id"], ["flow.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flow_run_contact_id", "flow_run", ["contact_id"])
    op.create_index("ix_flow_run_flow_id", "flow_run", ["flow_id"])
    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_conversation_id", "message", ["conversation_id"])
    op.create_table(
        "agent_trace",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("flow_run_id", sa.Integer(), nullable=True),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("input", sa.JSON(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"]),
        sa.ForeignKeyConstraint(["flow_run_id"], ["flow_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_trace_conversation_id", "agent_trace", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_trace_conversation_id", table_name="agent_trace")
    op.drop_table("agent_trace")
    op.drop_index("ix_message_conversation_id", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_flow_run_flow_id", table_name="flow_run")
    op.drop_index("ix_flow_run_contact_id", table_name="flow_run")
    op.drop_table("flow_run")
    op.drop_index("ix_conversation_contact_id", table_name="conversation")
    op.drop_table("conversation")
    op.drop_table("contact_tag")
    op.drop_index("ix_kb_chunk_document_id", table_name="kb_chunk")
    op.drop_table("kb_chunk")
    op.drop_index("ix_contact_channel_account_id", table_name="contact")
    op.drop_table("contact")
    op.drop_table("processed_event")
    op.drop_table("kb_document")
    op.drop_table("flow")
    op.drop_table("tag")
    op.drop_table("channel_account")
    op.drop_table("app_settings")
