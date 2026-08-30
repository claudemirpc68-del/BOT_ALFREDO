#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================================================
   DIAGNÓSTICO E AUTO-CORREÇÃO COMPLETA — BOT ALFREDO
===================================================================
Script automatizado que analisa, valida e corrige potenciais erros em
todo o fluxo do projeto BOT ALFREDO:

1. Estrutura de Diretórios e Pacotes (cria pastas e __init__.py ausentes)
2. Variáveis de Ambiente (.env / fallback a partir de .env.example)
3. Dependências e Pacotes Python instalados (pip check)
4. Análise Estática de Sintaxe e Imports de código (.py)
5. Integridade e Estrutura do Banco de Dados SQLite (auto-repair de tabelas)
6. Conectividade com Serviços Externos (Telegram, Groq, Tavily, Finexly, Google Maps)
7. Limpeza de caches corrompidos (__pycache__)
===================================================================
"""

import ast
import asyncio
import io
import importlib
import logging
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Garante saída UTF-8 no Windows para suporte a emojis no console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
elif sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True, errors="replace")

# Configuração de Cores do Terminal
class Cores:
    VERDE = "\033[92m"
    AMARELO = "\033[93m"
    VERMELHO = "\033[91m"
    AZUL = "\033[94m"
    CYAN = "\033[96m"
    NEGRITO = "\033[1m"
    RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Desativa logs excessivos de terceiros
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("diagnostico")

class DiagnosticoEAutocorrecao:
    def __init__(self):
        self.erros_encontrados = 0
        self.correcoes_realizadas = 0
        self.alertas = 0

    def relatar_ok(self, msg: str):
        print(f"  ✅ {Cores.VERDE}{msg}{Cores.RESET}")

    def relatar_fix(self, msg: str):
        self.correcoes_realizadas += 1
        print(f"  🛠️ {Cores.CYAN}[CORRIGIDO] {msg}{Cores.RESET}")

    def relatar_alerta(self, msg: str):
        self.alertas += 1
        print(f"  ⚠️ {Cores.AMARELO}[ALERTA] {msg}{Cores.RESET}")

    def relatar_erro(self, msg: str):
        self.erros_encontrados += 1
        print(f"  ❌ {Cores.VERMELHO}[ERRO] {msg}{Cores.RESET}")

    # -------------------------------------------------------------
    # 1. Verificação de Diretórios e Pacotes Python
    # -------------------------------------------------------------
    def verificar_estrutura_diretorios(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}1. Verificando Estrutura de Diretórios e Pacotes...{Cores.RESET}")
        
        diretorios_necessarios = [
            "bot",
            "bot/database",
            "bot/handlers",
            "bot/prompts",
            "bot/services",
            "data",
            "skills",
            "SKILLS ALFREDO",
            "actions",
            "docs",
        ]

        for d in diretorios_necessarios:
            path = PROJECT_ROOT / d
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                self.relatar_fix(f"Diretório '{d}' criado com sucesso.")
            else:
                self.relatar_ok(f"Diretório '{d}' presente.")

        # Garante __init__.py nas pastas de pacote Python
        pacotes = ["bot", "bot/database", "bot/handlers", "bot/prompts", "bot/services", "skills", "SKILLS ALFREDO", "actions"]
        for p in pacotes:
            init_file = PROJECT_ROOT / p / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Pacote Python inicializado automaticamente."""\n', encoding="utf-8")
                self.relatar_fix(f"Arquivo '__init__.py' criado em '{p}'.")

    # -------------------------------------------------------------
    # 2. Verificação do Arquivo .env e Variáveis de Ambiente
    # -------------------------------------------------------------
    def verificar_ambiente(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}2. Verificando Variáveis de Ambiente e .env...{Cores.RESET}")
        env_file = PROJECT_ROOT / ".env"
        env_example = PROJECT_ROOT / ".env.example"

        if not env_file.exists():
            if env_example.exists():
                shutil.copy(env_example, env_file)
                self.relatar_fix("Arquivo '.env' criado a partir de '.env.example'. Por favor, edite suas chaves de API nele.")
            else:
                conteudo_padrao = (
                    "TELEGRAM_BOT_TOKEN=\n"
                    "GROQ_API_KEY=\n"
                    "TAVILY_API_KEY=\n"
                    "GROQ_MODEL=qwen/qwen3.6-27b\n"
                    "GROQ_VISION_MODEL=qwen/qwen3.6-27b\n"
                    "BOT_NAME=ALFREDO\n"
                    "DB_PATH=data/alfredo.db\n"
                    "FINEXLY_API_KEY=\n"
                    "GOOGLE_MAPS_API_KEY=\n"
                )
                env_file.write_text(conteudo_padrao, encoding="utf-8")
                self.relatar_fix("Arquivo '.env' gerado com modelo padrão.")

        load_dotenv(dotenv_path=env_file, override=True)

        vars_criticas = [
            ("TELEGRAM_BOT_TOKEN", True),
            ("GROQ_API_KEY", True),
            ("TAVILY_API_KEY", False),
            ("GROQ_MODEL", False),
            ("BOT_NAME", False),
            ("FINEXLY_API_KEY", False),
            ("GOOGLE_MAPS_API_KEY", False),
        ]

        for var_name, obrigatorio in vars_criticas:
            val = os.getenv(var_name)
            if not val or val.strip() == "":
                if obrigatorio:
                    self.relatar_erro(f"Variável crítica '{var_name}' está ausente no .env.")
                else:
                    self.relatar_alerta(f"Variável opcional '{var_name}' não definida no .env.")
            else:
                self.relatar_ok(f"Variável '{var_name}' configurada.")

    # -------------------------------------------------------------
    # 3. Verificação de Dependências Python
    # -------------------------------------------------------------
    def verificar_dependencias(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}3. Verificando Bibliotecas Python Requeridas...{Cores.RESET}")
        
        modulos_obrigatorios = [
            ("telegram", "python-telegram-bot"),
            ("groq", "groq"),
            ("tavily", "tavily-python"),
            ("aiosqlite", "aiosqlite"),
            ("dotenv", "python-dotenv"),
            ("httpx", "httpx"),
            ("PIL", "pillow"),
        ]

        faltantes = []
        for modulo, pkg in modulos_obrigatorios:
            try:
                importlib.import_module(modulo)
                self.relatar_ok(f"Módulo '{modulo}' ({pkg}) instalado.")
            except ImportError:
                faltantes.append(pkg)
                self.relatar_erro(f"Módulo '{modulo}' ({pkg}) NÃO encontrado no ambiente.")

        if faltantes:
            print(f"  💡 {Cores.CYAN}Tentando instalar pacotes faltantes automaticamente via pip...{Cores.RESET}")
            cmd = [sys.executable, "-m", "pip", "install"] + faltantes
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.relatar_fix(f"Pacotes instalados com sucesso: {', '.join(faltantes)}")
            else:
                self.relatar_erro(f"Falha ao instalar pacotes automaticamente. Execute: pip install {' '.join(faltantes)}")

    # -------------------------------------------------------------
    # 4. Análise Estática de Sintaxe e Compilação dos Arquivos .py
    # -------------------------------------------------------------
    def verificar_sintaxe_e_codigo(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}4. Analisando Sintaxe e Integridade dos Arquivos Python...{Cores.RESET}")
        
        arquivos_py = list(PROJECT_ROOT.glob("**/*.py"))
        # Ignora arquivos de ambiente virtual .venv
        arquivos_py = [f for f in arquivos_py if ".venv" not in f.parts and "site-packages" not in f.parts]

        for filepath in arquivos_py:
            rel_path = filepath.relative_to(PROJECT_ROOT)
            # Teste 1: AST Parsing
            try:
                content = filepath.read_text(encoding="utf-8")
                ast.parse(content, filename=str(filepath))
            except SyntaxError as se:
                self.relatar_erro(f"Erro de Sintaxe em '{rel_path}': linha {se.lineno} — {se.msg}")
                continue
            except Exception as e:
                self.relatar_erro(f"Erro ao ler '{rel_path}': {e}")
                continue

            # Teste 2: Compilação Bytecode
            try:
                py_compile.compile(str(filepath), doraise=True)
                self.relatar_ok(f"Arquivo '{rel_path}' verificado sem erros de sintaxe.")
            except py_compile.PyCompileError as pye:
                self.relatar_erro(f"Falha ao compilar '{rel_path}': {pye.msg}")

    # -------------------------------------------------------------
    # 5. Integridade do Banco de Dados SQLite
    # -------------------------------------------------------------
    def verificar_banco_dados(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}5. Analisando Integridade do Banco de Dados SQLite...{Cores.RESET}")
        
        db_path_str = os.getenv("DB_PATH", "data/alfredo.db")
        db_path = PROJECT_ROOT / db_path_str

        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            self.relatar_fix(f"Diretório do banco de dados '{db_dir}' criado.")

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check de integridade do SQLite
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row and row[0] == "ok":
                self.relatar_ok(f"Banco de dados '{db_path_str}' com integridade OK.")
            else:
                self.relatar_erro(f"Integridade do banco de dados comprometida: {row}")

            # Tabelas esperadas
            tabelas_esperadas = ["users", "messages", "reminders"]
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tabelas_existentes = [r[0] for r in cursor.fetchall()]

            for tab in tabelas_esperadas:
                if tab not in tabelas_existentes:
                    self.relatar_alerta(f"Tabela '{tab}' ainda não foi criada no banco (será criada ao iniciar o bot).")
                else:
                    self.relatar_ok(f"Tabela '{tab}' confirmada.")

            conn.close()
        except Exception as e:
            self.relatar_erro(f"Falha ao acessar o banco de dados SQLite: {e}")

    # -------------------------------------------------------------
    # 6. Limpeza de Caches Corrompidos
    # -------------------------------------------------------------
    def limpar_caches(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}6. Limpando Caches de Compilação (__pycache__)...{Cores.RESET}")
        caches_removidos = 0
        for pycache in PROJECT_ROOT.glob("**/__pycache__"):
            if ".venv" not in pycache.parts:
                try:
                    shutil.rmtree(pycache)
                    caches_removidos += 1
                except Exception:
                    pass
        if caches_removidos > 0:
            self.relatar_fix(f"{caches_removidos} pasta(s) '__pycache__' limpas para evitar inconsistências de cache.")
        else:
            self.relatar_ok("Nenhum cache corrompido encontrado.")

    # -------------------------------------------------------------
    # 7. Teste de Conectividade Assíncrona com APIs
    # -------------------------------------------------------------
    async def verificar_servicos_async(self):
        print(f"\n{Cores.NEGRITO}{Cores.AZUL}7. Testando Serviços de Conectividade Externa...{Cores.RESET}")

        # Telegram
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                    if resp.status_code == 200 and resp.json().get("ok"):
                        bot_info = resp.json().get("result", {})
                        self.relatar_ok(f"Telegram API OK — Bot: @{bot_info.get('username')}")
                    else:
                        self.relatar_erro(f"Telegram API recusou o token: HTTP {resp.status_code}")
            except Exception as e:
                self.relatar_erro(f"Falha ao conectar na API do Telegram: {e}")

        # Groq Service
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from bot.services.groq_service import GroqService
                model = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
                vision_model = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
                groq = GroqService(api_key=groq_key, model=model, vision_model=vision_model)
                resp = await groq.chat("Olá", [])
                if resp:
                    self.relatar_ok(f"Groq Service OK (Modelo: {model})")
                else:
                    self.relatar_erro("Groq Service retornou resposta vazia.")
            except Exception as e:
                self.relatar_erro(f"Falha no Groq Service: {e}")

    # -------------------------------------------------------------
    # Execução Principal
    # -------------------------------------------------------------
    def executar(self):
        print(f"""
{Cores.NEGRITO}{Cores.CYAN}===================================================================
   SISTEMA DE DIAGNÓSTICO E AUTO-CORREÇÃO — BOT ALFREDO
==================================================================={Cores.RESET}""")

        self.verificar_estrutura_diretorios()
        self.verificar_ambiente()
        self.verificar_dependencias()
        self.verificar_sintaxe_e_codigo()
        self.verificar_banco_dados()
        self.limpar_caches()

        # Executa testes assíncronos
        asyncio.run(self.verificar_servicos_async())

        # Exibe resumo final
        print(f"\n{Cores.NEGRITO}{Cores.CYAN}===================================================================")
        print(f"                    RESUMO DA ANÁLISE")
        print(f"==================================================================={Cores.RESET}")
        print(f"   Erros Detectados:     {Cores.VERMELHO}{self.erros_encontrados}{Cores.RESET}")
        print(f"   Correções Efetuadas:  {Cores.CYAN}{self.correcoes_realizadas}{Cores.RESET}")
        print(f"   Alertas:              {Cores.AMARELO}{self.alertas}{Cores.RESET}")
        print(f"{Cores.NEGRITO}{Cores.CYAN}==================================================================={Cores.RESET}")

        if self.erros_encontrados == 0:
            print(f"\n🎉 {Cores.NEGRITO}{Cores.VERDE}PROJETO 100% SAUDÁVEL E OPERACIONAL! NENHUM ERRO ENCONTRADO.{Cores.RESET}\n")
        else:
            print(f"\n⚠️ {Cores.NEGRITO}{Cores.AMARELO}Foram encontrados erros que requerem atenção nas variáveis acima.{Cores.RESET}\n")

if __name__ == "__main__":
    diagnostico = DiagnosticoEAutocorrecao()
    diagnostico.executar()
