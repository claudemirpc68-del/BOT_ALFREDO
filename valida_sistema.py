#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Validação e Verificação Consolidado para o BOT ALFREDO.
Testa:
1. Variáveis de ambiente (.env)
2. Conectividade e validade do Token do Telegram (getMe)
3. Conectividade com a API da Groq (Chat completions com o modelo configurado)
4. Conectividade com a API do Tavily (Busca Web)
5. Banco de dados local SQLite (aiosqlite)
"""

import os
import sys
import asyncio
import logging
import sqlite3
from dotenv import load_dotenv

# Garante saída em UTF-8 no Windows para evitar problemas com emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuração de cores para o terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    NEGRITO = '\033[1m'
    RESET = '\033[0m'

# Carrega o .env
load_dotenv()

async def testar_env():
    print(f"{Cores.NEGRITO}1. Verificando Variáveis de Ambiente (.env)...{Cores.RESET}")
    vars_obrigatorias = [
        "TELEGRAM_BOT_TOKEN",
        "GROQ_API_KEY",
        "TAVILY_API_KEY",
        "GROQ_MODEL",
        "BOT_NAME"
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
        print(f"  🔴 {Cores.VERMELHO}Falha na validação do .env. Corrija os erros antes de prosseguir.{Cores.RESET}\n")
        return False
    print(f"  🟢 {Cores.VERDE}Variáveis de ambiente validadas com sucesso!{Cores.RESET}\n")
    return True

async def testar_telegram():
    print(f"{Cores.NEGRITO}2. Testando Conexão com a API do Telegram...{Cores.RESET}")
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
                    print(f"  🟢 {Cores.VERDE}Token do Telegram é válido.{Cores.RESET}\n")
                    return True
            print(f"  ❌ {Cores.VERMELHO}Erro na API do Telegram: {resp.status_code} - {resp.text}{Cores.RESET}\n")
            return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  ❌ {Cores.VERMELHO}Falha ao conectar na API do Telegram: {repr(e)}{Cores.RESET}\n")
        return False

async def testar_groq():
    print(f"{Cores.NEGRITO}3. Testando Conexão com a API da Groq...{Cores.RESET}")
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)
        
        # Teste simples de completação de chat
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Diga 'OK'"}],
            max_tokens=10,
            temperature=0.0
        )
        resposta = resp.choices[0].message.content.strip()
        print(f"  ✅ Groq respondeu: \"{resposta}\" (Modelo: {model})")
        print(f"  🟢 {Cores.VERDE}Conexão e Autenticação com a Groq estão OK!{Cores.RESET}\n")
        return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Falha na API da Groq: {e}{Cores.RESET}\n")
        return False

async def testar_tavily():
    print(f"{Cores.NEGRITO}4. Testando Conexão com a API do Tavily (Busca Web)...{Cores.RESET}")
    api_key = os.getenv("TAVILY_API_KEY")
    
    try:
        import httpx
        # Usamos requisição direta para evitar overhead de inicialização da SDK no teste
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": "Últimas notícias de tecnologia",
            "search_depth": "basic",
            "max_results": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                dados = resp.json()
                resultados = dados.get("results", [])
                print(f"  ✅ Tavily respondeu com sucesso! Encontrado: \"{resultados[0].get('title') if resultados else 'Nada'}\"")
                print(f"  🟢 {Cores.VERDE}Conexão e Chave do Tavily estão OK!{Cores.RESET}\n")
                return True
            else:
                print(f"  ❌ {Cores.VERMELHO}Erro do Tavily: Status {resp.status_code} - {resp.text}{Cores.RESET}\n")
                return False
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Falha ao conectar com o Tavily: {e}{Cores.RESET}\n")
        return False

async def testar_sqlite():
    print(f"{Cores.NEGRITO}5. Testando Banco de Dados Local (SQLite)...{Cores.RESET}")
    db_path = "data/alfredo.db"
    
    try:
        import aiosqlite
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        async with aiosqlite.connect(db_path) as db:
            # Executa uma query simples
            async with db.execute("SELECT sqlite_version()") as cursor:
                row = await cursor.fetchone()
                versao = row[0] if row else "Desconhecida"
                print(f"  ✅ SQLite inicializado e operacional. Versão: {versao}")
                print(f"  ✅ Arquivo do banco de dados: {db_path}")
                print(f"  🟢 {Cores.VERDE}Banco de dados SQLite está OK!{Cores.RESET}\n")
                return True
    except Exception as e:
        print(f"  ❌ {Cores.VERMELHO}Falha ao inicializar/testar o SQLite: {e}{Cores.RESET}\n")
        return False

async def rodar_validacao():
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}       SISTEMA DE VALIDAÇÃO COMPLETA - ALFREDO       {Cores.RESET}")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}\n")
    
    if not await testar_env():
        print(f"🔴 {Cores.VERMELHO}Validação abortada devido a erros no arquivo .env.{Cores.RESET}")
        sys.exit(1)
        
    tarefas = [
        testar_telegram(),
        testar_groq(),
        testar_tavily(),
        testar_sqlite()
    ]
    
    resultados = await asyncio.gather(*tarefas)
    
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    print(f"{Cores.NEGRITO}                  RESUMO DOS TESTES                  {Cores.RESET}")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    
    testes = ["Telegram API", "Groq API", "Tavily API", "Banco de Dados"]
    sucesso = True
    for teste, res in zip(testes, resultados):
        status = f"{Cores.VERDE}PASSOUS{Cores.RESET}" if res else f"{Cores.VERMELHO}FALHOU{Cores.RESET}"
        print(f"  - {teste:<15}: {status}")
        if not res:
            sucesso = False
            
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}")
    if sucesso:
        print(f"🎉 {Cores.VERDE}{Cores.NEGRITO}TODOS OS TESTES PASSARAM COM SUCESSO!{Cores.RESET}")
        print(f"🤖 O bot ALFREDO está 100% operacional e pronto para rodar.")
    else:
        print(f"⚠️ {Cores.AMARELO}{Cores.NEGRITO}ALGUNS TESTES FALHARAM.{Cores.RESET}")
        print(f"Corrija os serviços que falharam listados acima.")
    print(f"{Cores.NEGRITO}===================================================={Cores.RESET}\n")
    
    if not sucesso:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(rodar_validacao())
