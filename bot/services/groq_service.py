"""
Serviço de integração com a API da Groq.
Fornece chat contextual, análise de imagens, resumo, tradução, geração de código e posts do LinkedIn.
Usa o sistema modular de prompts (persona + skills).
"""

import re
import logging
from groq import AsyncGroq

from bot.prompts import build_prompt

logger = logging.getLogger(__name__)


class GroqService:
    """Serviço de integração com a API da Groq."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3.6-27b",
        vision_model: str = "qwen/qwen3.6-27b",
    ):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        self.vision_model = vision_model
        logger.info(f"Groq inicializado com modelo: {model} e visão: {vision_model}")

    async def chat(self, message: str, history: list[dict]) -> str:
        """
        Envia uma mensagem de chat com histórico de conversa.
        Usa: persona + skill "chat"
        """
        try:
            from datetime import datetime, timezone, timedelta
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("America/Sao_Paulo")
                agora_dt = datetime.now(tz)
            except Exception:
                tz = timezone(timedelta(hours=-3))
                agora_dt = datetime.now(tz)
            dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
            dia_semana_str = dias_semana[agora_dt.weekday()]
            agora = f"{dia_semana_str}, {agora_dt.strftime('%d/%m/%Y %H:%M:%S')}"
            prompt = build_prompt("chat")
            prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual: {agora}. Use esta referência caso precise responder sobre tempo ou datas."
            messages = [{"role": "system", "content": prompt}]
            
            # Adiciona o histórico
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})
                
            # Adiciona a mensagem atual
            messages.append({"role": "user", "content": message})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui gerar uma resposta. Tente novamente."

        except Exception as e:
            logger.error(f"Erro no Groq chat: {e}", exc_info=True)
            return self._format_error(e)

    async def search_answer(self, query: str, search_context: str) -> str:
        """
        Gera uma resposta inteligente com base nos resultados de pesquisa da internet.
        Usa: persona + skill "search"
        """
        try:
            prompt = build_prompt("search")
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Pesquisa: {query}\n\n"
                        f"Resultados da internet:\n{search_context}\n\n"
                        "Com base nesses resultados, dê uma resposta completa e organizada. "
                        "Cite as fontes relevantes no final."
                    )
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=2048,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui elaborar uma resposta."

        except Exception as e:
            logger.error(f"Erro no Groq search_answer: {e}", exc_info=True)
            return self._format_error(e)

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        caption: str | None,
        history: list[dict],
    ) -> str:
        """
        Analisa uma imagem usando modelo de visão da Groq.
        Usa: persona + skill "image"
        """
        try:
            user_prompt = caption or "Analise esta imagem em detalhes. O que você vê?"
            vision_model = self.vision_model

            import base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            image_url = f"data:{mime_type};base64,{base64_image}"

            prompt = build_prompt("image")
            messages = [{"role": "system", "content": prompt}]

            # Injeta histórico recente de mensagens (se houver)
            if history:
                for msg in history:
                    role = "assistant" if msg["role"] == "model" else msg["role"]
                    messages.append({"role": role, "content": msg["content"]})

            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            })

            import asyncio
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self.client.chat.completions.create(
                        model=vision_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui analisar a imagem."
                except Exception as ex:
                    if ("503" in str(ex) or "over capacity" in str(ex).lower()) and attempt < max_retries - 1:
                        logger.warning(f"Groq Vision instável (503/capacity), tentando novamente ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    raise ex

        except Exception as e:
            logger.error(f"Erro no Groq Vision: {e}", exc_info=True)
            return self._format_error(e)

    async def summarize(self, text: str) -> str:
        """
        Resume um texto de forma clara e concisa.
        Usa: persona + skill "summarize"
        """
        try:
            prompt = build_prompt("summarize")
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Resuma o seguinte texto de forma clara e concisa, mantendo os pontos principais:\n\n{text}"
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui resumir o texto."

        except Exception as e:
            logger.error(f"Erro no Groq resumo: {e}", exc_info=True)
            return self._format_error(e)

    async def translate(self, text: str, target_lang: str = "inglês") -> str:
        """
        Traduz um texto para o idioma especificado.
        Usa: persona + skill "translate"
        """
        try:
            prompt = build_prompt("translate")
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Traduza fielmente o seguinte texto para o idioma {target_lang}. Retorne APENAS o texto traduzido final, sem aspas extras, sem preâmbulos e sem explicações adicionais:\n\n{text}"
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui traduzir o texto."

        except Exception as e:
            logger.error(f"Erro no Groq tradução: {e}", exc_info=True)
            return self._format_error(e)

    async def generate_code(self, description: str) -> str:
        """
        Gera código com base em uma descrição.
        Usa: persona + skill "code"
        """
        try:
            prompt = build_prompt("code")
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Gere o código para: {description}\n\nInclua comentários explicativos e um exemplo de uso."
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
                max_tokens=3000,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui gerar o código."

        except Exception as e:
            logger.error(f"Erro no Groq código: {e}", exc_info=True)
            return self._format_error(e)

    async def generate_linkedin_post(self, topic: str) -> str:
        """
        Gera um post viral para o LinkedIn.
        Usa: persona + skill "linkedin"
        """
        try:
            prompt = build_prompt("linkedin")
            user_prompt = (
                f"Crie um post viral para o LinkedIn sobre o seguinte tema:\n\n{topic}\n\n"
                "Siga à risca o estilo de escrita: frases curtas, impacto emocional, gancho inicial forte, "
                "valor informativo/estatística e uma chamada para ação (pergunta de engajamento no final). "
                "Adicione as hashtags mais adequadas de TI e IA."
            )

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=1024,
            )
            return self._clean_response(response.choices[0].message.content) or "🤔 Não consegui criar o post para o LinkedIn."

        except Exception as e:
            logger.error(f"Erro no Groq LinkedIn Post: {e}", exc_info=True)
            return self._format_error(e)

    @staticmethod
    def _clean_response(content: str | None) -> str:
        """Remove blocos de raciocínio interno (<think>...</think>) e formata a resposta."""
        if not content:
            return ""
        # Remove tags <think>...</think> completas
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        # Remove caso tenha tag <think> aberta sem fechamento (em caso de truncamento)
        cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @staticmethod
    def _format_error(error: Exception) -> str:
        """Formata mensagem de erro amigável para o usuário."""
        error_str = str(error).lower()

        if "rate" in error_str or "limit" in error_str:
            return (
                "⚠️ Limite de requisições atingido na API Groq. "
                "Aguarde alguns segundos e tente novamente."
            )
        elif "api_key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
            return "🔑 Erro de autenticação com a API Groq. Verifique a chave."
        else:
            return f"❌ Erro ao processar: {str(error)[:200]}"
