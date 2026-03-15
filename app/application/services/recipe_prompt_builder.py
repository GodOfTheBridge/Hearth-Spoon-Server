"""Prompt builder for the structured recipe generation call."""

from __future__ import annotations

from datetime import datetime

from app.domain.entities import RecipeGenerationParameters


class RecipePromptBuilder:
    """Generate stable prompts for structured recipe generation."""

    def build_system_prompt(self) -> str:
        """Return a strict system prompt focused on reliable structured output."""

        return (
            "You are an expert culinary creator for the mobile app 'ПечьДаЛожка'. "
            "Generate one original, realistic, cookable home recipe. "
            "The recipe must be safe, family-friendly, achievable with common kitchen tools, "
            "and written in Russian. Do not include markdown, explanations, or extra keys. "
            "Respect the provided constraints exactly and produce content that "
            "matches the JSON schema."
        )

    def build_user_prompt(
        self,
        *,
        slot_time_utc: datetime,
        parameters: RecipeGenerationParameters,
    ) -> str:
        """Return the user prompt containing generation constraints."""

        excluded_ingredients = (
            ", ".join(parameters.excluded_ingredients)
            if parameters.excluded_ingredients
            else "none"
        )
        return (
            f"Generation slot UTC: {slot_time_utc.isoformat()}.\n"
            f"Language code: {parameters.language_code}.\n"
            f"Cuisine context: {parameters.cuisine_context}.\n"
            f"Dietary context: {parameters.dietary_context}.\n"
            f"Excluded ingredients: {excluded_ingredients}.\n"
            f"Maximum ingredients: {parameters.maximum_ingredients}.\n"
            f"Maximum steps: {parameters.maximum_steps}.\n"
            "The recipe should feel editorial, appetizing, practical and slightly surprising, "
            "but it must remain believable for real home cooking."
        )
