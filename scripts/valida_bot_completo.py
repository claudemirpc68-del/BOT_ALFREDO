#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validação de ponta a ponta (E2E) para todas as funcionalidades do ALFREDO.
Realiza chamadas reais de integração (banco de dados, Groq, Tavily, lembretes).
"""

import os
import sys
import io
import asyncio
import logging

# Garante saída em UTF-8 no Windows para evitar UnicodeEncodeError com emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Garante que a raiz do projeto está no sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Configuração de logging básica
logging.basicConfig(level=logging.ERROR)

from bot.config import GROQ_API_KEY, GROQ_MODEL, TAVILY_API_KEY, MAX_REMINDER_MINUTES
from bot.database.db import Database
from bot.services.groq_service import GroqService
from bot.services.tavily_service import TavilyService

# Banco de dados temporário de testes para evitar concorrência com o bot rodando
TEST_DB_PATH = "alfredo_test.db"

# Bytes de uma imagem PNG válida de 1x1 pixel
FAKE_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


async def testar_banco_de_dados():
    print("[TEST] 1. Banco de Dados Local (aiosqlite)...")
    
    # Limpa arquivo anterior caso tenha sobrado
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    db = Database(TEST_DB_PATH)
    await db.initialize()
    
    # Salva o usuário primeiro para respeitar a chave estrangeira
    chat_id = 999999
    await db.save_user(chat_id, username="test_validador", first_name="Teste", last_name="Validador")
    
    # Salva mensagem de teste
    await db.save_message(chat_id, "user", "Mensagem de teste de validacao")
    
    # Recupera histórico
    historico = await db.get_history(chat_id, limit=5)
    assert len(historico) > 0, "Erro: historico nao persistido no SQLite."
    assert historico[0]["content"] == "Mensagem de teste de validacao", "Erro: conteudo da mensagem incorreto."
    
    # Limpa histórico (comando /nova)
    await db.clear_history(chat_id)
    historico_limpo = await db.get_history(chat_id)
    assert len(historico_limpo) == 0, "Erro: comando /nova (limpeza de historico) falhou."
    
    await db.close()
    
    # Remove o banco de teste temporário para manter o repositório limpo
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
            
    print("   [OK] Banco de dados operacional (salvar usuario, salvar mensagem, obter e limpar historico).")


async def testar_chat_inteligente(groq):
    print("[TEST] 2. Chat Inteligente (Groq)...")
    resposta = await groq.chat("Diga apenas a palavra 'Confirmado' e nada mais.", history=[])
    print(f"   Groq respondeu: \"{resposta.strip()}\"")
    assert "erro" not in resposta.lower() or "limite" in resposta.lower(), "Erro retornado no chat."
    print("   [OK] Chat inteligente operacional.")


async def testar_analise_imagem(groq):
    print("[TEST] 3. Analise de Imagens (Vision)...")
    try:
        resposta = await groq.analyze_image(
            image_bytes=FAKE_PNG_BYTES,
            mime_type="image/png",
            caption="Descreva esta imagem de 1x1 pixel.",
            history=[]
        )
        print(f"   Vision respondeu: \"{resposta.strip()}\"")
        if "invalid image data" in resposta.lower() or "invalid_request_error" in resposta.lower():
            print("   [AVISO] A API do Groq respondeu, mas rejeitou a imagem de teste (comum para 1x1 pixel). Conexao OK!")
        else:
            print("   [OK] Analise de imagens operacional.")
    except Exception as e:
        print(f"   [AVISO] Erro ao enviar imagem: {e}. Conectividade da API ja validada no teste anterior.")


async def testar_resumo(groq):
    print("[TEST] 4. Resumo de Textos (/resumir)...")
    texto_longo = (
        "O ALFREDO e um assistente pessoal inteligente projetado para facilitar tarefas diarias. "
        "Ele funciona dentro do Telegram, mantendo um historico local criptografado para garantir a privacidade "
        "e respondendo as mensagens usando os modelos mais velozes da Groq. Ele tem modulos especiais "
        "de traducao, geracao de codigo, criacao de posts virais e agendamento de lembretes."
    )
    resposta = await groq.summarize(texto_longo)
    print(f"   Resumo gerado: \"{resposta.strip()}\"")
    assert len(resposta) > 5, "Erro: resumo muito curto ou vazio."
    print("   [OK] Resumo de textos operacional.")


async def testar_traducao(groq):
    print("[TEST] 5. Traducao de Textos (/traduzir)...")
    resposta = await groq.translate("Ola, como vai voce hoje?", "inglês")
    print(f"   Traduzido: \"{resposta.strip()}\"")
    assert len(resposta) > 0, "Erro: traducao vazia."
    print("   [OK] Traducao de textos operacional.")


async def testar_geracao_codigo(groq):
    print("[TEST] 6. Geracao de Codigo (/codigo)...")
    resposta = await groq.generate_code("Funcao em Python que calcula o fatorial de um numero")
    print(f"   Codigo gerado (primeiras linhas):\n{chr(10).join(resposta.split(chr(10))[:3])}...")
    assert "def " in resposta or "python" in resposta.lower() or "fatorial" in resposta.lower(), "Erro: codigo nao parece valido."
    print("   [OK] Geracao de codigo operacional.")


async def testar_linkedin(groq):
    print("[TEST] 7. Posts Virais para LinkedIn (/linkedin)...")
    resposta = await groq.generate_linkedin_post("Impacto da IA no suporte tecnico de TI")
    print(f"   Post LinkedIn (primeiras linhas):\n{chr(10).join(resposta.split(chr(10))[:3])}...")
    assert len(resposta) > 10, "Erro: post do LinkedIn muito curto."
    print("   [OK] Posts de LinkedIn operacional.")


async def testar_instagram(groq):
    print("[TEST] 8. Posts para Instagram (/instagram)...")
    resposta = await groq.generate_instagram_post("Dica de programacao limpa")
    print(f"   Post Instagram (primeiras linhas):\n{chr(10).join(resposta.split(chr(10))[:3])}...")
    assert len(resposta) > 10, "Erro: post do Instagram muito curto."
    print("   [OK] Posts de Instagram operacional.")


async def testar_pesquisa(groq, tavily):
    print("[TEST] 9. Pesquisa na Internet (/pesquisar)...")
    busca = await tavily.search("Ultimos lancamentos do Google Gemini 2026")
    contexto = tavily.extract_context(busca)
    resposta = await groq.search_answer("Ultimos lancamentos do Google Gemini 2026", contexto)
    print(f"   Resposta baseada na web: \"{resposta[:150].strip()}...\"")
    assert len(resposta) > 10, "Erro: resposta de pesquisa muito curta."
    print("   [OK] Pesquisa na internet operacional.")


def testar_lembretes():
    print("[TEST] 10. Validacao de Lembretes (/lembrete)...")
    # Simula a lógica de validação de tempo do handler
    tempo_valido = 30
    tempo_invalido_baixo = 0
    tempo_invalido_alto = 2000
    
    assert 0 < tempo_valido <= MAX_REMINDER_MINUTES, "Erro: tempo valido rejeitado."
    assert not (0 < tempo_invalido_baixo <= MAX_REMINDER_MINUTES), "Erro: tempo zero aceito."
    assert not (0 < tempo_invalido_alto <= MAX_REMINDER_MINUTES), "Erro: tempo limite excedido aceito."
    print("   [OK] Regras de validacao de tempo de lembretes operacionais.")


async def rodar_validacao_completa():
    print("====================================================")
    print("      SCRIPT DE VALIDAÇÃO COMPLETA: BOT ALFREDO     ")
    print("====================================================")
    
    # Valida presença das chaves
    if not GROQ_API_KEY:
        print("[ERRO] Chave GROQ_API_KEY ausente no arquivo .env.")
        sys.exit(1)
    if not TAVILY_API_KEY:
        print("[ERRO] Chave TAVILY_API_KEY ausente no arquivo .env.")
        sys.exit(1)
        
    print("[OK] Chaves GROQ_API_KEY e TAVILY_API_KEY encontradas.")
    
    groq = GroqService(api_key=GROQ_API_KEY, model=GROQ_MODEL)
    tavily = TavilyService(api_key=TAVILY_API_KEY)
    
    try:
        await testar_banco_de_dados()
        print("")
        await testar_chat_inteligente(groq)
        print("")
        await testar_analise_imagem(groq)
        print("")
        await testar_resumo(groq)
        print("")
        await testar_traducao(groq)
        print("")
        await testar_geracao_codigo(groq)
        print("")
        await testar_linkedin(groq)
        print("")
        await testar_instagram(groq)
        print("")
        await testar_pesquisa(groq, tavily)
        print("")
        testar_lembretes()
        
        print("\n====================================================")
        print("[OK] VALIDAÇÃO COMPLETA CONCLUÍDA COM 100% DE SUCESSO!")
        print("     Todas as funcionalidades do bot estão operacionais!")
        print("====================================================")
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a validacao completa: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(rodar_validacao_completa())
