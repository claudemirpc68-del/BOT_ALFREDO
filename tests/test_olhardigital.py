"""
Testes de validação para a skill Olhar Digital AI (bot/services/olhardigital_service.py).
Testa a integração simulada (mocking) com a API do Tavily e filtragem de preferências.
"""

import pytest
from unittest.mock import MagicMock, patch
from bot.services.olhardigital_service import AlfredoSkillOlharDigitalAI


class TestAlfredoSkillOlharDigitalAI:
    """Testes de unidade para a classe AlfredoSkillOlharDigitalAI."""

    def test_inicializacao(self):
        """Verifica se a classe inicializa corretamente com a chave da API."""
        skill = AlfredoSkillOlharDigitalAI(tavily_api_key="minha_chave_mock")
        assert skill.api_key == "minha_chave_mock"
        assert skill.endpoint == "https://api.tavily.com/search"

    @patch("requests.post")
    def test_executar_sucesso_sem_preferencias(self, mock_post):
        """Testa a execução bem-sucedida trazendo todos os resultados sem filtros."""
        # Configuração do mock de resposta do requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Nova IA revolucionária no mercado",
                    "url": "https://olhardigital.com.br/noticia1",
                    "content": "Uma nova inteligência artificial promete mudar o mercado de tecnologia de ponta a ponta.",
                },
                {
                    "title": "Google lança novidades",
                    "url": "https://olhardigital.com.br/noticia2",
                    "content": "Google apresenta novidades para desenvolvedores no seu evento anual.",
                }
            ]
        }
        mock_post.return_value = mock_response

        skill = AlfredoSkillOlharDigitalAI(tavily_api_key="minha_chave_mock")
        resultados = skill.executar()

        assert len(resultados) == 2
        assert resultados[0]["titulo"] == "Nova IA revolucionária no mercado"
        assert resultados[0]["link"] == "https://olhardigital.com.br/noticia1"
        assert resultados[0]["resumo"] == "Uma nova inteligência artificial promete mudar o mercado de tecnologia de ponta a ponta...."
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_executar_sucesso_com_preferencias(self, mock_post):
        """Testa a execução com filtros de preferências."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "OpenAI lança nova ferramenta GPT",
                    "url": "https://olhardigital.com.br/noticia1",
                    "content": "A OpenAI atualizou o seu principal modelo GPT com novos recursos de voz.",
                },
                {
                    "title": "Apple e IA no iOS",
                    "url": "https://olhardigital.com.br/noticia2",
                    "content": "Apple planeja integrar novos modelos locais aos iPhones mais recentes.",
                }
            ]
        }
        mock_post.return_value = mock_response

        skill = AlfredoSkillOlharDigitalAI(tavily_api_key="minha_chave_mock")
        
        # Filtrando por "GPT"
        resultados = skill.executar(preferencias=["gpt"])

        assert len(resultados) == 1
        assert resultados[0]["titulo"] == "OpenAI lança nova ferramenta GPT"
        
        # Filtrando por termo não existente
        resultados_vazios = skill.executar(preferencias=["android"])
        assert len(resultados_vazios) == 0

    @patch("requests.post")
    def test_executar_falha_requisicao(self, mock_post):
        """Testa o comportamento quando a API retorna um erro HTTP."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        skill = AlfredoSkillOlharDigitalAI(tavily_api_key="chave_invalida")
        resultados = skill.executar()

        assert "erro" in resultados
        assert "Falha na requisição" in resultados["erro"]
        assert "401" in resultados["erro"]
