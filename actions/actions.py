import os
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from skills.alfredo_olhardigital import AlfredoSkillOlharDigitalAI

# Garante o carregamento das variáveis de ambiente a partir do arquivo .env
load_dotenv()

class ActionBuscarOlharDigitalAI(Action):
    def name(self) -> str:
        return "action_buscar_olhardigital_ai"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        # Obtém a chave de API de forma segura a partir do ambiente (.env)
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            dispatcher.utter_message(text="Erro: Chave de API TAVILY_API_KEY não configurada no ambiente.")
            return []

        skill = AlfredoSkillOlharDigitalAI(tavily_api_key=tavily_key)

        preferencias = tracker.get_slot("preferencias")
        artigos = skill.executar(preferencias=[preferencias] if preferencias else None)

        if isinstance(artigos, dict) and "erro" in artigos:
            dispatcher.utter_message(text=f"Erro ao buscar no Olhar Digital: {artigos['erro']}")
            return []

        if artigos:
            for artigo in artigos:
                dispatcher.utter_message(text=f"{artigo['titulo']} - {artigo['link']}")
        else:
            dispatcher.utter_message(text="Não encontrei artigos relevantes no Olhar Digital.")

        return []
