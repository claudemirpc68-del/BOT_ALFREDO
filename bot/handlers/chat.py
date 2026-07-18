import logging
import json
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import MAX_MESSAGE_LENGTH
from bot.database.db import Database
from bot.services.groq_service import GroqService

logger = logging.getLogger(__name__)


async def _detect_geo_intent(groq: GroqService, text: str) -> dict:
    """Detecta se o usuário quer informações geográficas e extrai os parâmetros."""
    prompt = """Você é um assistente de extração de dados e intenção geográfica.
Analise a mensagem do usuário e extraia a intenção geográfica, se houver.
Identifique se ele está pedindo por:
- Rota/Direções: caminhos entre dois pontos (tipo: "rota").
- Busca de locais próximos: encontrar estabelecimentos, comércio ou serviços (tipo: "busca_local").
- Distância/Tempo: tempo de viagem ou distância física entre locais (tipo: "distancia").
- Nenhuma intenção de localização (tipo: "nenhum").

Responda EXCLUSIVAMENTE com um objeto JSON válido, sem tags markdown (como ```json ...) ou texto adicional.
O JSON deve ter exatamente estas chaves:
{
  "tipo": "rota" | "busca_local" | "distancia" | "nenhum",
  "origem": "endereço de origem de uma rota se mencionado. Se for busca_local, coloque aqui o ponto de referência, cidade ou região mencionado para a busca (ex: 'Suzano, SP'), senão null",
  "destino": "endereço de destino ou rota de destino, senão null",
  "busca": "termo do local que o usuário quer achar, se busca_local, senão null"
}
"""
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.1,  # Baixa temperatura para classificação estável
            max_tokens=256,
            response_format={"type": "json_object"}  # Força retorno JSON no Groq
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"Erro ao detectar intenção geográfica: {e}")
        return {"tipo": "nenhum", "origem": None, "destino": None, "busca": None}


async def _detect_adesao_intent(groq: GroqService, text: str) -> dict:
    """Detecta se o usuário quer registrar uma adesão de plano de saúde na planilha e extrai os dados."""
    prompt = """Você é um assistente especializado em extrair dados de adesão de plano de saúde.
Analise a mensagem do usuário e determine se ele quer registrar ou cadastrar uma nova adesão/plano na planilha.
Extraia os seguintes campos se mencionados:
- nome (nome completo do aderente)
- cpf (apenas os números ou formatado)
- plano (ex: Básico, Intermediário, Premium, Gold)
- email (e-mail de contato)
- data_adesao (data mencionada no formato AAAA-MM-DD. Se não mencionada, use null)

Responda EXCLUSIVAMENTE com um objeto JSON válido, sem tags markdown (como ```json ...) ou texto adicional.
O JSON deve ter exatamente estas chaves:
{
  "quer_registrar": true | false,
  "nome": string | null,
  "cpf": string | null,
  "plano": string | null,
  "email": string | null,
  "data_adesao": string | null
}
"""
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"Erro ao detectar intenção de adesão: {e}")
        return {"quer_registrar": False, "nome": None, "cpf": None, "plano": None, "email": None, "data_adesao": None}


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa localizações enviadas fisicamente pelo usuário via Telegram.
    Salva as coordenadas no banco de dados para referência geográfica futura.
    """
    db: Database = context.bot_data["db"]
    user = update.effective_user
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude

    # Registra/atualiza o usuário e salva suas coordenadas
    await db.save_user(user.id, user.username, user.first_name, user.last_name)
    await db.save_user_location(user.id, latitude, longitude)

    logger.info(f"Localização recebida e salva para o usuário {user.id}: {latitude}, {longitude}")

    await update.message.reply_text(
        "📍 *Localização registrada!*\n\n"
        "Agora, quando você me perguntar onde fica algum estabelecimento ou pedir rotas, "
        "usarei esta localização como ponto de partida ou referência geográfica. 😊",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de texto e envia para o Groq com contexto.
    Mantém o histórico de conversa no banco de dados.
    """
    db: Database = context.bot_data["db"]
    groq: GroqService = context.bot_data["groq"]
    user = update.effective_user
    message_text = update.message.text

    # 0. Detecção de intenção de adesão à planilha
    adesao_data = await _detect_adesao_intent(groq, message_text)
    if adesao_data.get("quer_registrar"):
        nome = adesao_data.get("nome")
        cpf = adesao_data.get("cpf")
        plano = adesao_data.get("plano")
        email = adesao_data.get("email")
        
        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)
        data_adesao = agora_dt.strftime("%Y-%m-%d") if not adesao_data.get("data_adesao") else adesao_data.get("data_adesao")

        campos_faltantes = []
        if not nome: campos_faltantes.append("Nome Completo")
        if not cpf: campos_faltantes.append("CPF")
        if not plano: campos_faltantes.append("Plano (Básico, Intermediário, Premium ou Gold)")
        if not email: campos_faltantes.append("E-mail")

        if campos_faltantes:
            await update.message.reply_text(
                f"📝 <b>Quase lá!</b> Para registrar a adesão na planilha, preciso que você me informe estes dados:\n\n"
                + "\n".join([f"• {c}" for c in campos_faltantes]) + "\n\n"
                "Por favor, envie uma mensagem informando os dados que faltaram.",
                parse_mode="HTML"
            )
            return

        await update.message.chat.send_action("typing")
        import httpx
        try:
            # verify=False ignora erros de certificado SSL autoassinado
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                webhook_url = "https://adesao.docescakemanias.cloud/adesao"
                payload = {
                    "nome": nome,
                    "cpf": cpf,
                    "plano": plano,
                    "data_adesao": data_adesao,
                    "email": email
                }
                res = await client.post(webhook_url, json=payload)
                if res.status_code == 200:
                    resposta_msg = (
                        f"✅ <b>Adesão registrada com sucesso na planilha!</b>\n\n"
                        f"👤 <b>Aderente:</b> {nome}\n"
                        f"💳 <b>Plano:</b> {plano}\n"
                        f"📧 <b>E-mail:</b> {email}\n"
                        f"📅 <b>Data:</b> {data_adesao}"
                    )
                    await update.message.reply_text(resposta_msg, parse_mode="HTML")
                    await db.save_message(user.id, "user", message_text)
                    await db.save_message(user.id, "model", resposta_msg)
                else:
                    resposta_msg = f"❌ <b>Erro ao registrar adesão:</b> {res.text}"
                    await update.message.reply_text(resposta_msg, parse_mode="HTML")
                    await db.save_message(user.id, "user", message_text)
                    await db.save_message(user.id, "model", resposta_msg)
        except Exception as ex:
            logger.error(f"Erro ao disparar webhook de adesão: {ex}")
            await update.message.reply_text(
                f"❌ <b>Erro ao se conectar ao servidor da planilha:</b> {str(ex)}",
                parse_mode="HTML"
            )
        return

    # Registra/atualiza o usuário
    await db.save_user(user.id, user.username, user.first_name, user.last_name)

    # 0. Detecção de intenção de salvar localização/CEP ou link do Maps por texto
    menciona_salvar = any(w in message_text.lower() for w in ["salve", "salvar", "registre", "registrar", "registrado", "gravar", "grave", "meu cep", "minha residência", "minha residencia", "minha casa", "estabelecimento", "localização", "localizacao"])
    cep_match = re.search(r'\b\d{5}-?\d{3}\b', message_text)
    maps_url_match = re.search(r'https?://(?:maps\.app\.goo\.gl|goo\.gl/maps|www\.google\.com/maps)\S+', message_text)
    
    if menciona_salvar and maps_url_match:
        url = maps_url_match.group(0)
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                url_str = str(response.url)
                
                lat, lng = None, None
                
                # 1. Tenta extrair maps/search/lat,+lng ou maps/place/lat,+lng
                match_search = re.search(r'/maps/(?:search|place)/(-?\d+\.\d+),\s*\+?(-?\d+\.\d+)', url_str)
                if match_search:
                    lat, lng = float(match_search.group(1)), float(match_search.group(2))
                else:
                    # 2. Tenta extrair o padrão @lat,lng
                    match_at = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url_str)
                    if match_at:
                        lat, lng = float(match_at.group(1)), float(match_at.group(2))
                    else:
                        # 3. Tenta extrair de parâmetros query
                        match_query = re.search(r'[?&](?:q|query|ll)=(-?\d+\.\d+),(-?\d+\.\d+)', url_str)
                        if match_query:
                            lat, lng = float(match_query.group(1)), float(match_query.group(2))
                        else:
                            # 4. Tenta no HTML (staticmap)
                            match_static = re.search(r'staticmap\?center=(-?\d+\.\d+)%2C(-?\d+\.\d+)', response.text)
                            if match_static:
                                lat, lng = float(match_static.group(1)), float(match_static.group(2))
                                
                if lat is not None and lng is not None:
                    await db.save_user_location(user.id, lat, lng)
                    logger.info(f"Localização por Link do Maps registrada para o usuário {user.id}: {lat}, {lng}")
                    
                    # Tenta obter endereço em formato de texto para confirmação
                    endereco_amigavel = "Seu estabelecimento"
                    maps = context.bot_data.get("google_maps")
                    if maps:
                        geo_coord = await maps.geocode(f"{lat},{lng}")
                        if geo_coord:
                            endereco_amigavel = geo_coord["formatted_address"]
                            
                    await update.message.reply_text(
                        f"📍 *Localização registrada com sucesso!*\n\n"
                        f"O link do seu estabelecimento ({endereco_amigavel}) foi gravado como sua localização de referência. "
                        f"Sempre que você me pedir locais próximos ou rotas, usarei este ponto de partida! 😊",
                        parse_mode="Markdown"
                    )
                    await db.save_message(user.id, "user", message_text)
                    await db.save_message(user.id, "model", f"Localização registrada com sucesso via Link do Maps: {lat},{lng}")
                    return
        except Exception as e:
            logger.error(f"Erro ao resolver link do Maps no chat: {e}", exc_info=True)

    elif menciona_salvar and cep_match:
        cep = cep_match.group(0)
        maps = context.bot_data.get("google_maps")
        if maps:
            # Geocodifica o CEP para obter as coordenadas reais
            geo_coord = await maps.geocode(f"{cep}, Brasil")
            if geo_coord:
                await db.save_user_location(user.id, geo_coord["lat"], geo_coord["lng"])
                logger.info(f"Localização textual (CEP {cep}) registrada para o usuário {user.id}: {geo_coord['lat']}, {geo_coord['lng']}")
                await update.message.reply_text(
                    f"📍 *Localização registrada com sucesso!*\n\n"
                    f"O CEP `{cep}` ({geo_coord['formatted_address']}) foi gravado como sua residência/localização de referência. "
                    f"Sempre que você me pedir locais próximos ou rotas, usarei este ponto de partida! 😊",
                    parse_mode="Markdown"
                )
                # Salva no histórico da conversa e encerra
                await db.save_message(user.id, "user", message_text)
                await db.save_message(user.id, "model", f"Localização registrada com sucesso: CEP {cep}")
                return

    # Mostra indicador de "digitando..."
    await update.message.chat.send_action("typing")

    # 1. Detecção de câmbio / cotação
    menciona_cambio = any(w in message_text.lower() for w in ["dólar", "dolar", "euro", "cotação", "cotacao", "cambio", "câmbio", "taxa de câmbio", "moedas"])
    moeda_context = ""
    if menciona_cambio:
        finexly = context.bot_data.get("finexly")
        if finexly:
            rates = await finexly.get_rates(base="USD", symbols="BRL,EUR")
            if rates:
                moeda_context = (
                    f"\n[DADOS FINANCEIROS - COTAÇÃO REAL DO FINEXLY (Base USD)]\n"
                    f"Dólar Comercial (USD/BRL): R$ {rates.get('BRL')}\n"
                    f"Euro (USD/EUR): {rates.get('EUR')}\n"
                )

    # 2. Detecção de intenção geográfica
    geo = await _detect_geo_intent(groq, message_text)
    geo_context = ""
    
    if geo["tipo"] != "none" and geo["tipo"] != "nenhum":
        maps = context.bot_data.get("google_maps")
        if maps:
            user_lat, user_lng = await db.get_user_location(user.id)
            user_loc_str = f"{user_lat},{user_lng}" if (user_lat is not None and user_lng is not None) else None
            
            if geo["tipo"] == "rota":
                origem = geo.get("origem") or user_loc_str
                destino = geo.get("destino")
                
                if not destino:
                    geo_context = "\n[SISTEMA: O usuário quer uma rota, mas não especificou o destino.]"
                elif not origem:
                    geo_context = (
                        "\n[SISTEMA: A localização de origem do usuário é desconhecida. "
                        "Peça para ele enviar a localização física no Telegram ou informar de onde está partindo.]"
                    )
                else:
                    direcoes = await maps.get_directions(origem, destino)
                    if direcoes:
                        geo_context = (
                            f"\n[DADOS DO GOOGLE MAPS - ROTAS]\n"
                            f"Origem: {direcoes['origin_address']}\n"
                            f"Destino: {direcoes['destination_address']}\n"
                            f"Distância: {direcoes['distance']}\n"
                            f"Tempo estimado de percurso: {direcoes['duration']}\n"
                            f"Instruções passo a passo:\n" + "\n".join([f"- {s}" for s in direcoes["steps"]])
                        )
                    else:
                        geo_context = "\n[SISTEMA: Não foi possível encontrar rotas ou direções válidas do Google Maps para os locais fornecidos.]"

            elif geo["tipo"] == "busca_local":
                busca = geo.get("busca")
                origem = geo.get("origem")
                search_lat, search_lng = user_lat, user_lng
                
                if origem:
                    geo_coord = await maps.geocode(origem)
                    if geo_coord:
                        search_lat, search_lng = geo_coord["lat"], geo_coord["lng"]
                        
                if search_lat is None or search_lng is None:
                    geo_context = (
                        "\n[SISTEMA: Você possui integração com a API do Google Maps, mas a localização do usuário é desconhecida no momento. "
                        "Explique de forma amigável que você tem integração com o Google Maps, mas precisa que ele envie a localização física "
                        "pelo Telegram ou especifique o local/cidade (ex: 'em Suzano, SP' ou 'perto do CEP 08625-572') para que você possa buscar.]"
                    )
                elif busca:
                    locais = await maps.search_places(busca, search_lat, search_lng)
                    if locais:
                        linhas = []
                        for l in locais:
                            linhas.append(f"- {l['name']} | Endereço: {l['address']} | Nota: {l['rating']} ({l['user_ratings_total']} avaliações)")
                        geo_context = f"\n[DADOS DO GOOGLE MAPS - ESTABELECIMENTOS PROXIMOS ENCONTRADOS]\n" + "\n".join(linhas)
                    else:
                        geo_context = f"\n[SISTEMA: Nenhum local do tipo '{busca}' foi encontrado próximo.]"

            elif geo["tipo"] == "distancia":
                origem = geo.get("origem") or user_loc_str
                destino = geo.get("destino")
                
                if not destino:
                    geo_context = "\n[SISTEMA: O usuário quer saber a distância/tempo, mas não especificou o destino.]"
                elif not origem:
                    geo_context = (
                        "\n[SISTEMA: A localização do usuário é desconhecida. "
                        "Peça para ele enviar a localização física pelo Telegram ou fornecer o local de partida.]"
                    )
                else:
                    matriz = await maps.get_distance_matrix(origem, destino)
                    if matriz:
                        geo_context = (
                            f"\n[DADOS DO GOOGLE MAPS - DISTÂNCIA E TRÂNSITO]\n"
                            f"Distância: {matriz['distance']}\n"
                            f"Tempo de percurso padrão: {matriz['duration']}\n"
                            f"Tempo de percurso no trânsito atual: {matriz['duration_in_traffic']}"
                        )
                    else:
                        geo_context = "\n[SISTEMA: Erro ao calcular distância e tempo no Google Maps.]"

    # Injeta contextos adicionais se houverem
    if moeda_context:
        message_text += moeda_context
    if geo_context:
        logger.info(f"Contexto geográfico injetado: {geo_context}")
        message_text += geo_context

    # Busca histórico de conversa
    history = await db.get_history(user.id)

    # Obtém resposta da IA
    response = await groq.chat(message_text, history)

    # Salva ambas as mensagens no histórico
    await db.save_message(user.id, "user", message_text)
    await db.save_message(user.id, "model", response)

    # Envia resposta (dividindo se necessário)
    await send_long_message(update, response)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa fotos enviadas pelo usuário.
    Baixa a imagem e envia para análise pelo Groq Vision.
    """
    db: Database = context.bot_data["db"]
    groq: GroqService = context.bot_data["groq"]
    user = update.effective_user

    # Registra/atualiza o usuário
    await db.save_user(user.id, user.username, user.first_name, user.last_name)

    # Mostra indicador de "digitando..."
    await update.message.chat.send_action("typing")

    # Pega a foto na maior resolução disponível
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    caption = update.message.caption
    history = await db.get_history(user.id)

    # Analisa a imagem com o Groq
    response = await groq.analyze_image(
        bytes(image_bytes), "image/jpeg", caption, history
    )

    # Salva no histórico (representação textual da imagem)
    user_msg = f"[📷 Imagem enviada]{f': {caption}' if caption else ''}"
    await db.save_message(user.id, "user", user_msg)
    await db.save_message(user.id, "model", response)

    await send_long_message(update, response)


async def send_long_message(update: Update, text: str) -> None:
    """
    Envia uma mensagem, dividindo em chunks se exceder o limite do Telegram.
    Tenta enviar com Markdown; se falhar, envia como texto puro.
    """
    if not text:
        text = "🤔 Resposta vazia recebida."

    if len(text) <= MAX_MESSAGE_LENGTH:
        await _safe_reply(update, text)
        return

    # Divide em chunks respeitando quebras de linha/espaços
    chunks = _split_text(text, MAX_MESSAGE_LENGTH)

    for chunk in chunks:
        await _safe_reply(update, chunk)


async def _safe_reply(update: Update, text: str) -> None:
    """Envia resposta com Markdown, fallback para texto puro se der erro."""
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        # Markdown inválido — tenta sem formatação
        try:
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")


def _split_text(text: str, max_length: int) -> list[str]:
    """Divide texto em chunks inteligentes, respeitando quebras naturais."""
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Tenta dividir em quebra de linha
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1 or split_at < max_length // 2:
            # Tenta dividir em espaço
            split_at = text.rfind(" ", 0, max_length)
        if split_at == -1:
            # Último recurso: corta no limite
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks
