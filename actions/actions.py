import os
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from skills.alfredo_olhardigital import AlfredoSkillOlharDigitalAI
from skills.alfredo_planilha import AlfredoSkillAutomacaoPlanilha
from groq import Groq

# Garante o carregamento das variáveis de ambiente a partir do arquivo .env
load_dotenv()


def _obter_ultimo_artigo(tracker: Tracker) -> str | None:
    """Recupera do tracker o último texto fornecido de um artigo."""
    for event in reversed(tracker.events):
        if event.get("event") == "user":
            parse_data = event.get("parse_data", {})
            intent = parse_data.get("intent", {}).get("name")
            if intent == "provide_article":
                return event.get("text")
    
    # Fallback: último texto de usuário que não seja um comando
    for event in reversed(tracker.events):
        if event.get("event") == "user":
            text = event.get("text", "")
            if text and not text.startswith("/") and len(text) > 20:
                return text
    return None


def _obter_cliente_groq() -> tuple[Groq | None, str]:
    """Instancia o cliente Groq e recupera o modelo a ser utilizado."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, ""
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return Groq(api_key=api_key), model


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
        if not article:
            dispatcher.utter_message(text="Não encontrei o artigo para extrair tópicos.")
            return []

        client, model = _obter_cliente_groq()
        if not client:
            # Fallback estático caso falte a chave
            topics = ["Inteligência Artificial", "Tecnologia", "Inovação"]
            dispatcher.utter_message(text=f"Tópicos identificados (modo offline): {', '.join(topics)}")
            return []

        try:
            prompt = (
                "Extraia os tópicos principais (máximo 5) do seguinte artigo sobre tecnologia/IA, separados por vírgula. "
                "Responda apenas com os tópicos identificados e absolutamente nada mais.\n\n"
                f"Artigo: {article}"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai tópicos chaves em formato CSV."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            topics = response.choices[0].message.content.strip()
            dispatcher.utter_message(text=f"Tópicos identificados: {topics}")
        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao extrair tópicos: {e}")
        return []


class ActionGenerateComments(Action):
    def name(self) -> str:
        return "action_generate_comments"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        article = _obter_ultimo_artigo(tracker)
        if not article:
            dispatcher.utter_message(text="Não encontrei o texto do artigo para avaliar.")
            return []

        client, model = _obter_cliente_groq()
        if not client:
            # Fallback estático
            dispatcher.utter_message(text="Comentários (modo offline): \n- Ponto forte: inovação\n- Ponto fraco: riscos éticos\n- Relevância: impacto no mercado de trabalho")
            return []

        try:
            prompt = (
                "Analise o seguinte artigo de tecnologia e gere uma avaliação crítica contendo exatamente esta estrutura:\n"
                "- Ponto forte: [descrição do ponto forte]\n"
                "- Ponto fraco: [descrição do ponto fraco]\n"
                "- Relevância: [descrição da relevância no mercado/sociedade]\n\n"
                f"Artigo: {article}"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um analista de tecnologia crítico e objetivo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1024
            )
            comentarios = response.choices[0].message.content.strip()
            dispatcher.utter_message(text=comentarios)
        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao gerar comentários: {e}")
        return []


class ActionGenerateLinkedinPost(Action):
    def name(self) -> str:
        return "action_generate_linkedin_post"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        article = _obter_ultimo_artigo(tracker)
        if not article:
            dispatcher.utter_message(text="Não encontrei o artigo para gerar o post.")
            return []

        client, model = _obter_cliente_groq()
        if not client:
            # Fallback estático
            post = (
                "🚀 A IA não vai roubar seu emprego. "
                "Mas quem souber usá-la, sim.\n\n"
                "O artigo mostra como ferramentas de IA estão transformando tarefas repetitivas "
                "em processos automáticos. Isso abre espaço para que profissionais foquem em criatividade e estratégia.\n\n"
                "👉 Você já está se preparando para essa mudança?\n\n"
                "#InteligênciaArtificial #Tecnologia #Inovação #Carreira"
            )
            dispatcher.utter_message(text=post)
            return []

        try:
            prompt = (
                "Escreva um post viral para o LinkedIn com base no seguinte artigo de tecnologia. "
                "Siga à risca estas diretrizes:\n"
                "- Estilo: envolvente, direto, com frases curtas e impacto emocional.\n"
                "- Estrutura: gancho inicial forte, valor informativo do artigo, e uma pergunta de engajamento no final.\n"
                "- Inclua hashtags relevantes no final (ex: #InteligenciaArtificial #Tecnologia #Inovacao).\n\n"
                f"Artigo: {article}"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é o ALFREDO, assistente pessoal especialista em criar posts virais no LinkedIn."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1024
            )
            post = response.choices[0].message.content.strip()
            dispatcher.utter_message(text=post)
        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao gerar post do LinkedIn: {e}")
        return []


class ActionRegistrarAdesao(Action):
    def name(self) -> str:
        return "action_registrar_adesao"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        
        nome = tracker.get_slot("nome")
        cpf = tracker.get_slot("cpf")
        plano = tracker.get_slot("plano")
        data_adesao = tracker.get_slot("data_adesao")
        email = tracker.get_slot("email")

        if not all([nome, cpf, plano, data_adesao, email]):
            dispatcher.utter_message(text="Erro: Faltam dados necessários para concluir o registro.")
            return []

        skill = AlfredoSkillAutomacaoPlanilha()
        resultado = skill.executar(
            nome=nome,
            cpf=cpf,
            plano=plano,
            data_adesao=data_adesao,
            email=email
        )

        if resultado.get("sucesso"):
            dispatcher.utter_message(text=f"Adesão registrada com sucesso para {nome} no plano {plano}!")
        else:
            msg_erro = resultado.get("mensagem", "Erro desconhecido")
            dispatcher.utter_message(text=f"Não foi possível registrar a adesão: {msg_erro}")

        return [
            SlotSet("nome", None),
            SlotSet("cpf", None),
            SlotSet("plano", None),
            SlotSet("data_adesao", None),
            SlotSet("email", None)
        ]
