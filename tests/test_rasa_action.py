"""
Testes de validação para a Custom Action do Rasa (actions/actions.py).
Mocka o Rasa Tracker, CollectingDispatcher e a execução da skill.
"""

import pytest
from unittest.mock import MagicMock, patch
from actions.actions import (
    ActionBuscarOlharDigitalAI,
    ActionExtractTopics,
    ActionGenerateComments,
    ActionGenerateLinkedinPost,
)


class TestActionBuscarOlharDigitalAI:
    """Testes de unidade para a ActionBuscarOlharDigitalAI do Rasa."""

    def test_action_name(self):
        """Verifica se o nome da action retornado está correto."""
        action = ActionBuscarOlharDigitalAI()
        assert action.name() == "action_buscar_olhardigital_ai"

    @patch("actions.actions.AlfredoSkillOlharDigitalAI")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "chave_mock"})
    def test_run_sucesso_com_artigos(self, mock_skill_class):
        """Testa o run da action quando artigos são retornados com sucesso."""
        # Configura o mock da skill
        mock_skill_instance = MagicMock()
        mock_skill_instance.executar.return_value = [
            {"titulo": "Notícia Rasa 1", "link": "https://olhardigital.com.br/1", "resumo": "Resumo 1"},
            {"titulo": "Notícia Rasa 2", "link": "https://olhardigital.com.br/2", "resumo": "Resumo 2"},
        ]
        mock_skill_class.return_value = mock_skill_instance

        # Mocks do Rasa
        dispatcher = MagicMock()
        tracker = MagicMock()
        tracker.get_slot.return_value = "chatgpt"  # preferências
        domain = {}

        action = ActionBuscarOlharDigitalAI()
        events = action.run(dispatcher, tracker, domain)

        # Asserts
        assert events == []
        mock_skill_class.assert_called_once_with(tavily_api_key="chave_mock")
        mock_skill_instance.executar.assert_called_once_with(preferencias=["chatgpt"])
        
        # Verifica as mensagens enviadas ao dispatcher
        assert dispatcher.utter_message.call_count == 2
        dispatcher.utter_message.assert_any_call(text="Notícia Rasa 1 - https://olhardigital.com.br/1")
        dispatcher.utter_message.assert_any_call(text="Notícia Rasa 2 - https://olhardigital.com.br/2")

    @patch("actions.actions.AlfredoSkillOlharDigitalAI")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "chave_mock"})
    def test_run_sem_artigos(self, mock_skill_class):
        """Testa o run da action quando nenhum artigo é retornado."""
        mock_skill_instance = MagicMock()
        mock_skill_instance.executar.return_value = []
        mock_skill_class.return_value = mock_skill_instance

        dispatcher = MagicMock()
        tracker = MagicMock()
        tracker.get_slot.return_value = None
        domain = {}

        action = ActionBuscarOlharDigitalAI()
        action.run(dispatcher, tracker, domain)

        dispatcher.utter_message.assert_called_once_with(
            text="Não encontrei artigos relevantes no Olhar Digital."
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_run_sem_api_key(self):
        """Testa o erro retornado quando a chave do Tavily não está configurada no ambiente."""
        dispatcher = MagicMock()
        tracker = MagicMock()
        domain = {}

        action = ActionBuscarOlharDigitalAI()
        action.run(dispatcher, tracker, domain)

        dispatcher.utter_message.assert_called_once_with(
            text="Erro: Chave de API TAVILY_API_KEY não configurada no ambiente."
        )


class TestActionExtractTopics:
    def test_action_name(self):
        action = ActionExtractTopics()
        assert action.name() == "action_extract_topics"

    def test_run(self):
        dispatcher = MagicMock()
        tracker = MagicMock()
        tracker.latest_message = {'text': 'Artigo de teste sobre Inteligência Artificial'}
        domain = {}

        action = ActionExtractTopics()
        events = action.run(dispatcher, tracker, domain)

        assert events == []
        dispatcher.utter_message.assert_called_once_with(
            text="Tópicos identificados: Inteligência Artificial, Tecnologia, Inovação"
        )


class TestActionGenerateComments:
    def test_action_name(self):
        action = ActionGenerateComments()
        assert action.name() == "action_generate_comments"

    def test_run(self):
        dispatcher = MagicMock()
        tracker = MagicMock()
        domain = {}

        action = ActionGenerateComments()
        events = action.run(dispatcher, tracker, domain)

        assert events == []
        dispatcher.utter_message.assert_called_once_with(
            text="Comentários: \n- Ponto forte: inovação\n- Ponto fraco: riscos éticos\n- Relevância: impacto no mercado de trabalho"
        )


class TestActionGenerateLinkedinPost:
    def test_action_name(self):
        action = ActionGenerateLinkedinPost()
        assert action.name() == "action_generate_linkedin_post"

    def test_run(self):
        dispatcher = MagicMock()
        tracker = MagicMock()
        domain = {}

        action = ActionGenerateLinkedinPost()
        events = action.run(dispatcher, tracker, domain)

        assert events == []
        assert dispatcher.utter_message.call_count == 1
        msg = dispatcher.utter_message.call_args[1].get("text")
        assert "A IA não vai roubar seu emprego" in msg
        assert "#InteligênciaArtificial" in msg

