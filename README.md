# 🤖 ALFREDO — Assistente Pessoal no Telegram

Bot assistente pessoal inteligente para Telegram, alimentado por **Google Gemini**.
Mantém conversas contextuais, analisa imagens, resume textos, traduz, gera código e cria lembretes.

## ✨ Funcionalidades

| Recurso | Comando | Descrição |
|---------|---------|-----------|
| 💬 Chat Inteligente | _(mensagem livre)_ | Conversa com IA sobre qualquer assunto |
| 📷 Análise de Imagens | _(envie foto)_ | Analisa e descreve imagens com Gemini Vision |
| 📝 Resumo | `/resumir` | Resume textos longos |
| 🌐 Tradução | `/traduzir` | Traduz entre 16 idiomas |
| 💻 Geração de Código | `/codigo` | Gera código a partir de descrições |
| 🔍 Pesquisa Internet | `/pesquisar` | Pesquisa na internet em tempo real via Tavily |
| ⏰ Lembretes | `/lembrete` | Cria lembretes programados |
| 🔄 Nova Conversa | `/nova` | Limpa histórico e reinicia |
| 📊 Status | `/status` | Informações da sessão |

## 🛠️ Stack Tecnológica

- **Python** 3.11+
- **python-telegram-bot** 21.x (com job-queue para lembretes)
- **google-genai** — SDK unificado do Google Gemini
- **aiosqlite** — SQLite assíncrono para persistência
- **tavily-python** — Pesquisa na internet em tempo real
- **python-dotenv** — Gerenciamento de variáveis de ambiente

## 🚀 Início Rápido

### 1. Pré-requisitos

- Python 3.11 ou superior
- Token do Bot Telegram ([@BotFather](https://t.me/BotFather))
- Chave da API Gemini ([Google AI Studio](https://aistudio.google.com/apikey))

### 2. Instalação

```bash
# Clone ou acesse o diretório do projeto
cd hello-world-1

# Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração

```bash
# Copie o template de variáveis
copy .env.example .env

# Edite o .env com suas credenciais
notepad .env
```

Preencha os valores no arquivo `.env`:

```env
TELEGRAM_BOT_TOKEN=seu_token_do_botfather
GEMINI_API_KEY=sua_chave_do_google_ai_studio
GEMINI_MODEL=gemini-2.5-flash
BOT_NAME=ALFREDO
TAVILY_API_KEY=sua_chave_do_tavily
```

### 4. Executar

```bash
python run.py
```

## 📁 Estrutura do Projeto

```
hello-world-1/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point — inicializa e roda o bot
│   ├── config.py             # Configurações e variáveis de ambiente
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py          # /start e /help
│   │   ├── chat.py           # Conversa com texto e imagens
│   │   ├── settings.py       # /nova e /status
│   │   └── tools.py          # /resumir, /traduzir, /codigo, /lembrete
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_service.py # Integração com Google Gemini
│   └── database/
│       ├── __init__.py
│       └── db.py             # Persistência SQLite assíncrona
├── .env.example              # Template de variáveis
├── .gitignore
├── requirements.txt
├── run.py                    # Script de inicialização
└── README.md
```

## 🔧 Comandos do Bot

### Conversa
- Envie qualquer mensagem de texto para conversar
- Envie uma foto para análise (com ou sem legenda)
- **`/nova`** — Limpa o histórico e inicia nova conversa

### Ferramentas
- **`/resumir <texto>`** — Resume um texto (ou responda a uma mensagem)
- **`/traduzir [idioma] <texto>`** — Traduz (padrão: inglês). Idiomas: `en`, `es`, `fr`, `de`, `it`, `ja`, `ko`, `zh`, etc.
- **`/codigo <descrição>`** — Gera código de programação
- **`/pesquisar <termo>`** — Pesquisa na internet em tempo real
- **`/lembrete <minutos> <mensagem>`** — Cria um lembrete (1 a 1440 min)

### Sistema
- **`/status`** — Informações da sessão atual
- **`/help`** — Guia completo de comandos

## 📝 Licença

Projeto pessoal — uso livre.
