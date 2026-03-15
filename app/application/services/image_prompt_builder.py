"""Prompt builder for image generation."""

from __future__ import annotations

from app.domain.entities import GeneratedRecipePayload, RecipeGenerationParameters


class ImagePromptBuilder:
    """Build a high-quality image prompt from the generated recipe."""

    def build(
        self,
        *,
        generated_recipe: GeneratedRecipePayload,
        generation_parameters: RecipeGenerationParameters,
    ) -> str:
        """Create a detailed prompt for the final plated dish image."""

        style_tags = ", ".join(generated_recipe.style_tags)
        plating_tips = "; ".join(generated_recipe.plating_tips)
        return (
            f"Editorial food photography of the finished dish '{generated_recipe.title}'. "
            f"Subtitle context: {generated_recipe.subtitle}. "
            f"Visual brief: {generated_recipe.image_generation_brief}. "
            f"Style tags: {style_tags}. "
            f"Plating guidance: {plating_tips}. "
            f"Image style: {generation_parameters.image_style}. "
            "Single plated serving, realistic texture, appetizing lighting, "
            "shallow depth of field, high detail, clean table styling, "
            "no hands, no packaging, no visible text, no watermark."
        )
