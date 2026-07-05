"""
Serviço de pesquisa na internet via Tavily API.
Permite que o ALFREDO busque informações atualizadas da web.
"""

import logging
from tavily import TavilyClient

logger = logging.getLogger(__name__)


class TavilyService:
    """Serviço de pesquisa na internet usando a API do Tavily."""

    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)
        logger.info("Tavily Search inicializado com sucesso")

    async def search(self, query: str, max_results: int = 5) -> dict:
        """
        Realiza uma pesquisa na internet.

        Args:
            query: Termo de busca.
            max_results: Número máximo de resultados (padrão: 5).

        Returns:
            Dicionário com os resultados da pesquisa.
        """
        try:
            # A API do Tavily é síncrona, mas o overhead é mínimo
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True,
            )
            return response

        except Exception as e:
            logger.error(f"Erro na pesquisa Tavily: {e}", exc_info=True)
            raise

    def format_results(self, response: dict) -> str:
        """
        Formata os resultados da pesquisa para exibição no Telegram.

        Args:
            response: Resposta da API do Tavily.

        Returns:
            Texto formatado em Markdown para o Telegram.
        """
        results = response.get("results", [])

        if not results:
            return "🔍 Nenhum resultado encontrado para sua pesquisa."

        formatted = []
        for i, result in enumerate(results[:5], 1):
            title = result.get("title", "Sem título")
            url = result.get("url", "")
            content = result.get("content", "")

            # Trunca o conteúdo se muito longo
            if len(content) > 200:
                content = content[:200] + "..."

            formatted.append(f"{i}. *{title}*\n{content}\n🔗 {url}")

        return "\n\n".join(formatted)

    def extract_context(self, response: dict) -> str:
        """
        Extrai o conteúdo dos resultados para usar como contexto na IA.

        Args:
            response: Resposta da API do Tavily.

        Returns:
            Texto com o contexto extraído dos resultados.
        """
        results = response.get("results", [])
        answer = response.get("answer", "")

        context_parts = []

        if answer:
            context_parts.append(f"Resposta direta: {answer}")

        for result in results[:5]:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            context_parts.append(f"[{title}]({url}): {content}")

        return "\n\n".join(context_parts)
