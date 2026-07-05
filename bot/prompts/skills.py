"""
Habilidades do ALFREDO — Carregadas da pasta 'SKILLS ALFREDO/' na raiz do projeto.
Cada habilidade é um arquivo .py individual nessa pasta.
"""

import importlib.util
import logging
from pathlib import Path

from bot.prompts.persona import PERSONA

logger = logging.getLogger(__name__)

# Caminho da pasta de skills na raiz do projeto
_SKILLS_DIR = Path(__file__).parent.parent.parent / "SKILLS ALFREDO"


def _load_skills() -> dict[str, str]:
    """
    Carrega dinamicamente todas as skills da pasta 'SKILLS ALFREDO/'.
    Cada arquivo .py deve ter uma constante SKILL com o prompt da habilidade.
    """
    skills = {}

    if not _SKILLS_DIR.exists():
        logger.warning(f"Pasta de skills não encontrada: {_SKILLS_DIR}")
        return skills

    for skill_file in _SKILLS_DIR.glob("*.py"):
        if skill_file.name.startswith("_"):
            continue  # Ignora __init__.py e afins

        skill_name = skill_file.stem  # Nome do arquivo sem extensão

        try:
            spec = importlib.util.spec_from_file_location(skill_name, skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "SKILL"):
                skills[skill_name] = module.SKILL
                logger.debug(f"Skill carregada: {skill_name}")
            else:
                logger.warning(f"Skill '{skill_name}' não tem constante SKILL")

        except Exception as e:
            logger.error(f"Erro ao carregar skill '{skill_name}': {e}")

    logger.info(f"Skills carregadas: {list(skills.keys())}")
    return skills


# Carrega todas as skills ao importar o módulo
SKILLS = _load_skills()


def build_prompt(*skill_names: str) -> str:
    """
    Constrói um prompt completo combinando a persona com uma ou mais habilidades.

    Args:
        *skill_names: Nomes das habilidades a incluir.
                      Exemplo: "chat", "search", "linkedin"

    Returns:
        Prompt completo (persona + habilidades selecionadas).

    Exemplo:
        >>> prompt = build_prompt("chat")
        >>> prompt = build_prompt("chat", "search")
    """
    parts = [PERSONA]

    for name in skill_names:
        skill = SKILLS.get(name)
        if skill:
            parts.append(skill)

    return "\n\n".join(parts)
