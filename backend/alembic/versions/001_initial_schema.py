"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("token", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("instrument_type", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])
    op.create_index("ix_instruments_token", "instruments", ["token"])

    op.create_table(
        "candles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candles_symbol", "candles", ["symbol"])
    op.create_index("ix_candles_timeframe", "candles", ["timeframe"])
    op.create_index("ix_candles_ts", "candles", ["ts"])

    op.create_table(
        "option_chain_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("pcr", sa.Float(), nullable=True),
        sa.Column("max_pain", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=32), nullable=False),
        sa.Column("symbols", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    op.create_table(
        "sector_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sector", sa.String(length=32), nullable=False),
        sa.Column("momentum", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal", sa.String(length=8), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("instrument", sa.String(length=64), nullable=True),
        sa.Column("entry", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("target_1", sa.Float(), nullable=True),
        sa.Column("target_2", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("market_condition", sa.String(length=16), nullable=False),
        sa.Column("holding_time", sa.String(length=32), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("data_stale", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signal_outcomes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("exit_reason", sa.String(length=64), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "confidence_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bucket", sa.String(length=64), nullable=False),
        sa.Column("weight_multiplier", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "risk_state",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trading_date", sa.String(length=10), nullable=False),
        sa.Column("daily_pnl_pct", sa.Float(), nullable=False),
        sa.Column("consecutive_losses", sa.Integer(), nullable=False),
        sa.Column("halted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trading_date"),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table in [
        "webhook_events",
        "risk_state",
        "confidence_history",
        "signal_outcomes",
        "signals",
        "sector_scores",
        "news_items",
        "option_chain_snapshots",
        "candles",
        "instruments",
    ]:
        op.drop_table(table)
