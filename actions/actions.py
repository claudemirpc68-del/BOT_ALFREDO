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


class ActionExtractTopics(Action):
    def name(self) -> str:
        return "action_extract_topics"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        article = tracker.latest_message.get('text')
        topics = ["Inteligência Artificial", "Tecnologia", "Inovação"]
        dispatcher.utter_message(text=f"Tópicos identificados: {', '.join(topics)}")
        return []


class ActionGenerateComments(Action):
    def name(self) -> str:
        return "action_generate_comments"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        dispatcher.utter_message(text="Comentários: \n- Ponto forte: inovação\n- Ponto fraco: riscos éticos\n- Relevância: impacto no mercado de trabalho")
        return []


class ActionGenerateLinkedinPost(Action):
    def name(self) -> str:
        return "action_generate_linkedin_post"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        post = (
            "🚀 A IA não vai roubar seu emprego. "
            "Mas quem souber usá-la, sim.\n\n"
            "O artigo mostra como ferramentas de IA estão transformando tarefas repetitivas "
            "em processos automáticos. Isso abre espaço para que profissionais foquem em criatividade e estratégia.\n\n"
            "O desafio? Requalificação. Quem não se adaptar às novas habilidades digitais pode ficar para trás.\n\n"
            "👉 Você já está se preparando para essa mudança?\n\n"
            "#InteligênciaArtificial #Tecnologia #Inovação #Carreira"
        )
        dispatcher.utter_message(text=post)
        return []

