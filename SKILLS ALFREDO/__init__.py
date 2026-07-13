"""
Skills do ALFREDO — Cada habilidade é um módulo individual.
Para adicionar uma nova skill, crie um arquivo .py nesta pasta e
registre-a no dicionário REGISTRY abaixo.
"""

import sys
from pathlib import Path

# Garante que a pasta raiz do projeto está no path para importação
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from chat import SKILL as chat_skill
from image import SKILL as image_skill
from summarize import SKILL as summarize_skill
from translate import SKILL as translate_skill
from code import SKILL as code_skill
from linkedin import SKILL as linkedin_skill
from search import SKILL as search_skill
from olhardigital import SKILL as olhardigital_skill
from news_digest import SKILL as news_digest_skill

# ── Registro central de skills ───────────────────────────────
# Para adicionar uma nova skill:
# 1. Crie um arquivo .py nesta pasta com a constante SKILL
# 2. Importe aqui e adicione ao REGISTRY

REGISTRY: dict[str, str] = {
    "chat": chat_skill,
    "image": image_skill,
    "summarize": summarize_skill,
    "translate": translate_skill,
    "code": code_skill,
    "linkedin": linkedin_skill,
    "search": search_skill,
    "olhardigital": olhardigital_skill,
    "news_digest": news_digest_skill,
}


def list_skills() -> list[str]:
    """Retorna a lista de skills disponíveis."""
    return list(REGISTRY.keys())
