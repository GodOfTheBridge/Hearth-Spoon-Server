"""Initial schema for the ПечьДаЛожка backend.

Revision ID: 20260315_0001
Revises:
Create Date: 2026-03-15 16:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260315_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    difficulty_level_enum = sa.Enum(
        "easy",
        "medium",
        "hard",
        name="difficultylevel",
        native_enum=False,
    )
    moderation_status_enum = sa.Enum(
        "pending",
        "approved",
        "rejected",
        name="moderationstatus",
        native_enum=False,
    )
    publication_status_enum = sa.Enum(
        "draft",
        "published",
        "unpublished",
        name="publicationstatus",
        native_enum=False,
    )
    generation_slot_status_enum = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        name="generationslotstatus",
        native_enum=False,
    )
    generation_job_status_enum = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        name="generationjobstatus",
        native_enum=False,
    )
    generation_type_enum = sa.Enum(
        "hourly_recipe",
        name="generationtype",
        native_enum=False,
    )
    generation_job_type_enum = sa.Enum(
        "hourly_recipe_generation",
        name="generationjobtype",
        native_enum=False,
    )

    json_type = postgresql.JSONB(astext_type=sa.Text())

    op.create_table(
        "recipes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=False),
        sa.Column("story_or_intro", sa.Text(), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("cooking_time_minutes", sa.Integer(), nullable=False),
        sa.Column("preparation_time_minutes", sa.Integer(), nullable=False),
        sa.Column("difficulty_level", difficulty_level_enum, nullable=False),
        sa.Column("ingredients", json_type, nullable=False),
        sa.Column("tools", json_type, nullable=False),
        sa.Column("steps", json_type, nullable=False),
        sa.Column("cooking_tips", json_type, nullable=False),
        sa.Column("plating_tips", json_type, nullable=False),
        sa.Column("style_tags", json_type, nullable=False),
        sa.Column("source_generation_parameters", json_type, nullable=False),
        sa.Column("image_prompt", sa.Text(), nullable=False),
        sa.Column("moderation_status", moderation_status_enum, nullable=False),
        sa.Column("publication_status", publication_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipes_publication_status", "recipes", ["publication_status"])
    op.create_index("ix_recipes_published_at", "recipes", ["published_at"])

    op.create_table(
        "generation_schedule_slots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slot_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generation_type", generation_type_enum, nullable=False),
        sa.Column("status", generation_slot_status_enum, nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "slot_time_utc",
            "generation_type",
            name="uq_generation_schedule_slot",
        ),
    )
    op.create_index(
        "ix_generation_schedule_slots_slot_time_utc",
        "generation_schedule_slots",
        ["slot_time_utc"],
    )

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_type", generation_job_type_enum, nullable=False),
        sa.Column("schedule_slot_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", generation_job_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_request_metadata", json_type, nullable=False),
        sa.Column("provider_response_metadata", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["schedule_slot_id"],
            ["generation_schedule_slots.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_generation_jobs_idempotency_key"),
    )
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"])
    op.create_index(
        "ix_generation_jobs_schedule_slot_id",
        "generation_jobs",
        ["schedule_slot_id"],
    )

    op.create_table(
        "recipe_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipe_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("public_url", sa.String(length=1024), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("provider_model", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", name="uq_recipe_images_recipe_id"),
    )
    op.create_index("ix_recipe_images_storage_key", "recipe_images", ["storage_key"])


def downgrade() -> None:
    op.drop_index("ix_recipe_images_storage_key", table_name="recipe_images")
    op.drop_table("recipe_images")

    op.drop_index("ix_generation_jobs_schedule_slot_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_status", table_name="generation_jobs")
    op.drop_table("generation_jobs")

    op.drop_index(
        "ix_generation_schedule_slots_slot_time_utc",
        table_name="generation_schedule_slots",
    )
    op.drop_table("generation_schedule_slots")

    op.drop_index("ix_recipes_published_at", table_name="recipes")
    op.drop_index("ix_recipes_publication_status", table_name="recipes")
    op.drop_table("recipes")
