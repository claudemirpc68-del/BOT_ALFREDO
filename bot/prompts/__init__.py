"""
Módulo de prompts do ALFREDO.
Separa a persona (quem ele é) das habilidades (o que ele faz).
"""

from bot.prompts.persona import PERSONA
from bot.prompts.skills import SKILLS, build_prompt

__all__ = ["PERSONA", "SKILLS", "build_prompt"]
