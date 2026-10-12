"""The model catalogue moves from code to the database: one row per model a game can be played
on (its menu entry, rescue, thinking levels and structured-output mode) and its dated prices.

A model can now be added, listed, re-priced or retuned without a deploy (scripts/model_catalog.py);
the server re-reads the tables every few seconds. The rows below are the catalogue as it stood in
code on 2026-10-12 (server/game/model_catalog.py, Agents/llm_factory/pricing.py, and the per-model
levels and modes in accessors.py and backends.py), written out here so this migration always
inserts the same rows.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-12
"""

from datetime import date
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (model, display_name, listed, menu_order, house_funded, rescue_model, turn_thinking,
#  summary_thinking, structured_mode, notes)
MODELS = [
    ('gemini-3.5-flash-lite', 'Gemini 3.5 Flash-Lite', True, 1, True, 'gemini-3.1-flash-lite', 'medium', None, None, "The fallback default, the first house-funded row (owner preference 2026-09-10). With structured output it reasons 0 tokens at minimal and low; at medium the hallucination bench's bad samples fell from 31% to 10% (discussion_evidence.md §6.7)."),
    ('gemini-3.1-flash-lite', 'Gemini 3.1 Flash-Lite', True, 2, True, 'gemini-3.5-flash-lite', 'low', None, None, 'Reasons at low; bench bad samples 15% (discussion_evidence.md §6.7).'),
    ('gemini-3.6-flash', 'Gemini 3.6 Flash', True, 3, True, 'gemini-3.5-flash-lite', None, None, None, ''),
    ('gemini-2.5-pro', 'Gemini 2.5 Pro', True, 4, False, 'gemini-3.5-flash-lite', None, None, None, ''),
    ('deepseek/deepseek-v4-pro', 'DeepSeek V4 Pro', True, 5, False, 'deepseek/deepseek-v4-flash', None, None, None, ''),
    ('deepseek/deepseek-v4-flash', 'DeepSeek V4 Flash', True, 6, False, 'deepseek/deepseek-v4-pro', None, None, None, ''),
    ('deepseek/deepseek-flash', 'DeepSeek V4.1 Flash', True, 7, False, 'deepseek/deepseek-v4-flash', None, None, None, "Probed 2026-09-10 (tests/live): drops required fields on roughly one wolf vote in three; the seat's retry plus the rescue absorb it."),
    ('openai/gpt-6-luna', 'GPT-6 Luna', True, 8, False, None, 'low', None, 'json_schema', "Admitted 2026-10-04 (eval-model-admission + the hallucination bench). Both refuse a forced tool call with reasoning on, so json_schema. 2026-10-11 Phase 3 bench (phase3_luna_haiku): low 7% bad against medium's 4%, a tie case by case, ~390 reasoning tokens against ~1,260 and 8 s a turn against 16. An OpenAI key; no rescue."),
    ('anthropic/claude-haiku-5-5', 'Claude Haiku 5.5', True, 9, True, None, 'low', None, 'json_schema', "Admitted 2026-10-11 (eval-model-admission; the Phase 3 hallucination bench): effort low, 10-16% bad samples against 3.5 flash-lite's 34-39%, ~9.5 s a turn. A forced tool call turns its thinking off; json_schema kept it (51/51 against 45/51). Paid from the owner's Anthropic credits. No rescue (owner 2026-10-12)."),
    ('openrouter/z-ai/glm-5.3-flash', 'GLM-5.3 Flash', True, 10, False, None, 'minimal', 'minimal', 'json_mode', "Without thinking (its endpoint cannot turn reasoning fully off; effort low), json_mode: 32% bad samples, a cheap option rather than a recommended one. With thinking it took 34-55 s a call, against the summary's 90 s budget. An OpenRouter key, pinned to Z.AI's servers; no rescue."),
    ('anthropic/claude-sonnet-5-5', 'Claude Sonnet 5.5', False, 100, False, None, None, None, 'json_schema', 'Refuses tool_choice "tool" and "any" (2026-10-12); with thinking off it needs "between_tools" and takes no temperature (backends._CLAUDE_THINKING_OFF).'),
]

# (model as billed, since, input, cached, output, peak, source), USD per million tokens
PRICES = [
    ('gemini-3.1-flash-lite', '2026-01-01', 0.25, 0.025, 1.5, False, 'Langfuse models/prices table, entered 2026-07-26'),
    ('gemini-3.5-flash-lite', '2026-07-21', 0.3, 0.03, 2.5, False, 'Langfuse models/prices table, entered 2026-07-26'),
    ('gemini-3.6-flash', '2026-07-21', 1.5, 0.15, 7.5, False, 'Langfuse models/prices table, entered 2026-07-26'),
    ('gemini-3.5-flash', '2026-05-19', 1.5, 0.15, 9.0, False, 'Vertex AI pricing page, global endpoint, read 2026-10-12'),
    ('gemini-2.5-pro', '2025-06-01', 1.25, 0.3125, 10.0, False, 'list rates (not in the Langfuse table); cached rate unverified'),
    ('deepseek-v4-pro', '2026-07-01', 0.435, 0.003625, 0.87, False, 'Langfuse models/prices table, entered 2026-07-26'),
    ('deepseek-v4-pro', '2026-08-13', 0.66, 0.022, 1.98, True, 'DeepSeek pricing page, read 2026-10-04 (peak hours from 2026-08-13)'),
    ('deepseek-v4-flash', '2026-07-01', 0.14, 0.0028, 0.28, False, 'Langfuse models/prices table, entered 2026-07-26'),
    ('deepseek-v4-flash', '2026-08-13', 0.22, 0.007, 0.66, True, 'a third-party listing of the August rates, dated from when DeepSeek added peak hours; the exact day of the change is not known'),
    ('deepseek-v4-flash', '2026-09-10', 0.15, 0.003, 0.6, True, 'the name routes to V4.1 Flash from 2026-09-10 and bills at its rates'),
    ('deepseek-flash', '2026-09-10', 0.15, 0.003, 0.6, True, 'DeepSeek pricing page, read 2026-10-04'),
    ('gpt-6-luna', '2026-09-01', 0.1, 0.01, 0.5, False, 'OpenAI list rates; cache writes bill $0.125, which usage does not separate out, so an uncached input token is priced $0.025 short'),
    ('z-ai/glm-5.3-flash', '2026-09-10', 0.15, 0.03, 0.5, False, 'Z.AI list rates after its launch promotion ended 2026-09-09 (OpenRouter, pinned to Z.AI)'),
    ('claude-haiku-5-5', '2026-10-07', 0.1, 0.01, 0.5, False, 'Anthropic pricing page, read 2026-10-11; a cache write bills 1.25x input, counted as plain input; rates for prompts under 100,000 tokens'),
    ('claude-sonnet-5-5', '2026-09-28', 2.0, 0.1, 10.0, False, 'Anthropic pricing page, read 2026-10-11; a cache write bills 1.25x input, counted as plain input'),
]


def upgrade() -> None:
    models = op.create_table(
        "models",
        sa.Column("model", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("listed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("menu_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("house_funded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rescue_model", sa.Text(), nullable=True),
        sa.Column("turn_thinking", sa.Text(), nullable=True),
        sa.Column("summary_thinking", sa.Text(), nullable=True),
        sa.Column("structured_mode", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    prices = op.create_table(
        "model_prices",
        sa.Column("model", sa.Text(), primary_key=True),
        sa.Column("since", sa.Date(), primary_key=True),
        sa.Column("input", sa.Float(), nullable=False),
        sa.Column("cached", sa.Float(), nullable=False),
        sa.Column("output", sa.Float(), nullable=False),
        sa.Column("peak", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source", sa.Text(), nullable=False, server_default=""),
    )
    keys = ("model", "display_name", "listed", "menu_order", "house_funded", "rescue_model",
            "turn_thinking", "summary_thinking", "structured_mode", "notes")
    op.bulk_insert(models, [dict(zip(keys, row)) for row in MODELS])
    keys = ("model", "since", "input", "cached", "output", "peak", "source")
    op.bulk_insert(prices, [{**dict(zip(keys, row)), "since": date.fromisoformat(row[1])}
                            for row in PRICES])


def downgrade() -> None:
    op.drop_table("model_prices")
    op.drop_table("models")
