#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validação consolidado de habilidades para o BOT ALFREDO.
Valida:
1. Variáveis de ambiente
2. Conexão com Telegram API
3. Banco de dados local SQLite (aiosqlite)
4. Groq Service (Habilidades de chat, resumo, tradução, código, linkedin e vision)
5. Tavily Service (Pesquisa)
6. Skill Olhar Digital
7. Finexly Service (Moedas)
8. Google Maps Service (Geocoding, rotas, locais)
"""

import os
import sys
import io
import asyncio
import logging
from dotenv import load_dotenv

# Garante saída em UTF-8 no Windows para evitar UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configuração de cores para o terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    NEGRITO = '\033[1m'
    RESET = '\033[0m'

# Bytes de uma imagem PNG válida de 1x1 pixel para teste do Groq Vision
FAKE_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

# Desativa logging verboso
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("validador")

async def testar_env():
    print(f"{Cores.NEGRITO}1. Verificando Variáveis de Ambiente (.env)...{Cores.RESET}")
    vars_obrigatorias = [
        "TELEGRAM_BOT_TOKEN",
        "GROQ_API_KEY",
        "TAVILY_API_KEY",
        "GROQ_MODEL",
        "BOT_NAME",
        "FINEXLY_API_KEY",
        "GOOGLE_MAPS_API_KEY"
    ]
    
    erros = []
    for var in vars_obrigatorias:
        valor = os.getenv(var)
        if not valor:
            erros.append(var)
            print(f"  ❌ {Cores.VERMELHO}{var}{Cores.RESET} está ausente ou vazio.")
        else:
            # Oculta segredos para exibição
            exibicao = valor[:6] + "..." + valor[-6:] if len(valor) > 12 else "***"
            if "TOKEN" in var or "KEY" in var:
                print(f"  ✅ {var}: {Cores.VERDE}{exibicao}{Cores.RESET}")
            else:
                print(f"  ✅ {var}: {Cores.VERDE}{valor}{Cores.RESET}")
                
    if erros:
        print(f"  🔴 {Cores.VERMELHO}Falha na validação do .env.{Cores.RESET}\n")
        return False
    print(f"  🟢 {Cores.VERDE}Variáveis de ambiente validadas com sucesso!{Cores.RESET}\n")
    return True

async def testar_telegram():
    print(f"{Cores.NEGRITO}2. Testando API do Telegram...{Cores.RESET}")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("ok"):
                    result = dados.get("result", {})
                    nome = result.get("first_name")
                    username = result.get("username")
                    print(f"  ✅ Conectado com sucesso à API do Telegram!")
                    print(f"  ✅ Nome do Bot: {Cores.VERDE}{nome}{Cores.RESET}")
                    print(f"  ✅ Username: {Cores.VERDE}@{username}{Cores.RESET}")
                    return True
            print(f"  ❌ {Cores.VERMELHO}Erro na API do Telegram: {resp.status_code} - {resp.text}{Cores.RESET}\n")
            return False
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Falha ao conectar na API do Telegram: {e}{Cores.RESET}\n")
        return False

async def testar_sqlite():
    print(f"{Cores.NEGRITO}3. Testando Banco de Dados Local (SQLite/aiosqlite)...{Cores.RESET}")
    TEST_DB_PATH = "data/alfredo_valida_tmp.db"
    
    # Remove arquivo anterior caso exista
    if os.path.exists(TEST_DB_PATH):
        try: os.remove(TEST_DB_PATH)
        except Exception: pass
        
    try:
        from bot.database.db import Database
        db = Database(TEST_DB_PATH)
        await db.initialize()
        
        # Teste de persistência de usuário
        chat_id = 999111
        await db.save_user(chat_id, "user_validacao", "Teste", "Habilidades")
        
        # Teste de persistência de mensagem
        await db.save_message(chat_id, "user", "Mensagem de Teste")
        await db.save_message(chat_id, "model", "Resposta de Teste")
        
        # Recupera histórico
        historico = await db.get_history(chat_id, limit=5)
        if len(historico) != 2:
            raise Exception("Falha ao persistir e recuperar histórico de mensagens.")
            
        # Teste de Lembrete
        reminder_id = await db.save_reminder(chat_id, chat_id, "once", "2026-07-13T20:00:00", "Lembrete Teste")
        reminders = await db.get_user_reminders(chat_id)
        if len(reminders) != 1:
            raise Exception("Falha ao criar lembrete no banco.")
            
        await db.delete_reminder(reminder_id)
        reminders_pos_delete = await db.get_user_reminders(chat_id)
        if len(reminders_pos_delete) != 0:
            raise Exception("Falha ao deletar lembrete do banco.")
            
        await db.close()
        print(f"  ✅ Banco de dados SQLite testado com sucesso (Usuários, Histórico e Lembretes).")
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro ao testar o Banco de Dados: {e}{Cores.RESET}\n")
        return False
    finally:
        # Limpa o banco temporário
        if os.path.exists(TEST_DB_PATH):
            try: os.remove(TEST_DB_PATH)
            except Exception: pass

async def testar_groq_service():
    print(f"{Cores.NEGRITO}4. Testando Habilidades do GroqService (IA)...{Cores.RESET}")
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")
    
    try:
        from bot.services.groq_service import GroqService
        groq = GroqService(api_key=api_key, model=model)
        
        # A. Chat Inteligente
        resp_chat = await groq.chat("Diga 'OK' e nada mais.", [])
        print(f"  ✅ [Habilidade Chat] IA respondeu: \"{resp_chat.strip()}\"")
        
        # B. Resumo
        texto_longo = "A inteligência artificial é a capacidade de dispositivos eletrônicos de funcionar de maneira que se assemelha aos aspectos da inteligência humana, como raciocínio, aprendizado e adaptação."
        resp_resumo = await groq.summarize(texto_longo)
        print(f"  ✅ [Habilidade Resumo] Resumo: \"{resp_resumo.strip()}\"")
        
        # C. Tradução
        resp_traducao = await groq.translate("Good morning, how are you?", "português")
        print(f"  ✅ [Habilidade Tradução] Traduzido: \"{resp_traducao.strip()}\"")
        
        # D. Código
        resp_codigo = await groq.generate_code("função fibonacci recursiva em Python")
        print(f"  ✅ [Habilidade Código] Código gerado com sucesso ({len(resp_codigo)} caracteres).")
        
        # E. Ghostwriter LinkedIn
        resp_linkedin = await groq.generate_linkedin_post("Lançamento do novo modelo Llama 3.3")
        print(f"  ✅ [Habilidade LinkedIn] Post gerado com sucesso ({len(resp_linkedin)} caracteres).")
        
        # F. Groq Vision (Análise de Imagem)
        resp_vision = await groq.analyze_image(
            image_bytes=FAKE_PNG_BYTES,
            mime_type="image/png",
            caption="Descreva a imagem",
            history=[]
        )
        print(f"  ✅ [Habilidade Vision] Análise enviada/respondida com sucesso.")
        
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro no teste do GroqService: {e}{Cores.RESET}\n")
        return False

async def testar_tavily_service():
    print(f"{Cores.NEGRITO}5. Testando Habilidade de Pesquisa (Tavily)...{Cores.RESET}")
    api_key = os.getenv("TAVILY_API_KEY")
    
    try:
        from bot.services.tavily_service import TavilyService
        tavily = TavilyService(api_key=api_key)
        resultados = await tavily.search("Últimas novidades de Inteligência Artificial 2026")
        contexto = tavily.extract_context(resultados)
        if not contexto or len(contexto) < 20:
            raise Exception("Nenhum resultado de busca retornado ou extraído.")
            
        print(f"  ✅ Conectado ao Tavily. Resultados de pesquisa extraídos com sucesso ({len(contexto)} caracteres).")
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro no teste do Tavily: {e}{Cores.RESET}\n")
        return False

async def testar_skill_olhar_digital():
    print(f"{Cores.NEGRITO}6. Testando Habilidade Olhar Digital AI...{Cores.RESET}")
    api_key = os.getenv("TAVILY_API_KEY")
    
    try:
        from bot.services.olhardigital_service import AlfredoSkillOlharDigitalAI
        skill = AlfredoSkillOlharDigitalAI(api_key)
        resultados = skill.executar(preferencias=["Inteligência Artificial"], max_results=3)
        if isinstance(resultados, dict) and "erro" in resultados:
            raise Exception(resultados["erro"])
            
        print(f"  ✅ Habilidade Olhar Digital executada. Encontradas {len(resultados)} notícias de IA.")
        for idx, art in enumerate(resultados[:2], 1):
            print(f"    [{idx}] {art['titulo']} (Link: {art['link']})")
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro na Habilidade Olhar Digital: {e}{Cores.RESET}\n")
        return False

async def testar_finexly_service():
    print(f"{Cores.NEGRITO}7. Testando Habilidade de Cotações (Finexly)...{Cores.RESET}")
    api_key = os.getenv("FINEXLY_API_KEY")
    
    try:
        from bot.services.finexly_service import FinexlyService
        finexly = FinexlyService(api_key=api_key)
        rates = await finexly.get_rates()
        if not rates or "BRL" not in rates or "EUR" not in rates:
            raise Exception("Não foi possível obter as taxas USD/BRL ou USD/EUR.")
            
        print(f"  ✅ Conectado à API do Finexly. USD/BRL: {rates['BRL']} | USD/EUR: {rates['EUR']}")
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro na Habilidade de Cotações: {e}{Cores.RESET}\n")
        return False

async def testar_google_maps_service():
    print(f"{Cores.NEGRITO}8. Testando Habilidade de Localização e Rotas (Google Maps)...{Cores.RESET}")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    try:
        from bot.services.google_maps_service import GoogleMapsService
        maps = GoogleMapsService(api_key=api_key)
        
        # A. Geocoding
        geo_result = await maps.geocode("Av. Paulista, 1000, São Paulo")
        if not geo_result or "lat" not in geo_result:
            raise Exception("Geocoding falhou para Av. Paulista.")
        lat, lng = geo_result["lat"], geo_result["lng"]
        print(f"  ✅ [Geocoding] Av. Paulista, 1000 resolvida para Lat: {lat}, Lng: {lng}")
        
        # B. Directions
        directions = await maps.get_directions("Av. Paulista, 1000, São Paulo", "Aeroporto de Congonhas, São Paulo")
        if not directions or "steps" not in directions:
            raise Exception("Falha ao calcular direções da rota.")
        print(f"  ✅ [Directions] Distância: {directions['distance']} | Tempo: {directions['duration']}")
        
        # C. Places
        places = await maps.search_places("banco", lat, lng, radius=2000)
        print(f"  ✅ [Places] Encontrados {len(places)} locais do tipo 'banco' em um raio de 2km.")
        
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Erro na Habilidade do Google Maps: {e}{Cores.RESET}\n")
        return False

async def rodar_validacao_completa():
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}      SISTEMA DE VALIDAÇÃO COMPLETA DE HABILIDADES      {Cores.RESET}")
    print(f"{Cores.NEGRITO}                    BOT ALFREDO                     {Cores.RESET}")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}\n")
    
    load_dotenv()
    
    if not await testar_env():
        print(f"🔴 {Cores.VERMELHO}Validação abortada por falta de variáveis essenciais.{Cores.RESET}")
        sys.exit(1)
        
    testes = {
        "Variáveis de Ambiente (.env)": testar_env(),
        "Conexão Telegram API": testar_telegram(),
        "Banco de Dados SQLite": testar_sqlite(),
        "Habilidades Groq (IA)": testar_groq_service(),
        "Habilidade Pesquisa Tavily": testar_tavily_service(),
        "Habilidade Olhar Digital AI": testar_skill_olhar_digital(),
        "Habilidade Cotações Finexly": testar_finexly_service(),
        "Habilidade Google Maps (Rotas)": testar_google_maps_service(),
    }
    
    resultados = {}
    for nome_teste, coroutine in testes.items():
        if nome_teste == "Variáveis de Ambiente (.env)":
            # Já testamos
            resultados[nome_teste] = True
            continue
        try:
            res = await coroutine
            resultados[nome_teste] = res
        except Exception as e:
            print(f"Erro inesperado no teste '{nome_teste}': {e}")
            resultados[nome_teste] = False
        print("")
            
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}                  RESUMO DOS TESTES                  {Cores.RESET}")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    
    sucesso = True
    for nome, status in resultados.items():
        status_str = f"{Cores.VERDE}PASSOUS{Cores.RESET}" if status else f"{Cores.VERMELHO}FALHOU{Cores.RESET}"
        print(f"  - {nome:<35}: {status_str}")
        if not status:
            sucesso = False
            
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    if sucesso:
        print(f"🎉 {Cores.VERDE}{Cores.NEGRITO}TODOS OS TESTES PASSARAM COM SUCESSO!{Cores.RESET}")
        print(f"🤖 O bot ALFREDO está com todas as habilidades 100% validadas e funcionais.")
    else:
        print(f"⚠️ {Cores.AMARELO}{Cores.NEGRITO}ALGUMAS HABILIDADES APRESENTARAM FALHAS.{Cores.RESET}")
        print(f"Corrija os serviços que falharam listados acima.")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}\n")
    
    if not sucesso:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(rodar_validacao_completa())
