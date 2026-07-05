# Product Requirements Document (PRD) — ALFREDO

Este documento especifica os requisitos de negócio e comportamento do assistente pessoal inteligente **ALFREDO** para Telegram, utilizando a sintaxe **EARS (Easy Approach to Requirements Syntax)**.

---

## 🎯 Escopo Geral
O ALFREDO é um bot no Telegram voltado a auxiliar usuários em conversação contextualizada, análise visual, geração de código, tradução, pesquisa em tempo real na internet e agendamento de lembretes.

---

## 📋 Requisitos do Sistema (Formato EARS)

### Ubiquitous Requirements (Requisitos Ubíquos)
* **UR01:** O sistema deve executar continuamente em segundo plano, escutando e respondendo às requisições da API do Telegram.
* **UR02:** O sistema deve gerenciar e persistir o histórico de interações de conversação em um banco de dados SQLite local de forma assíncrona (`aiosqlite`).
* **UR03:** O sistema deve consumir a API oficial do Google Gemini (`google-genai`) para processamento e geração de conteúdo textual e visual.
* **UR04:** O sistema deve carregar suas configurações e segredos a partir de variáveis de ambiente gerenciadas por um arquivo `.env`.

### Event-Driven Requirements (Orientados a Eventos)
* **ER01:** Quando um usuário enviar uma mensagem de texto livre, o sistema deve processar o histórico recente do chat e gerar uma resposta contextualizada através do Gemini.
* **ER02:** Quando um usuário enviar uma imagem (com ou sem legenda), o sistema deve submetê-la ao Gemini Vision e retornar a descrição e análise visual da imagem.
* **ER03:** Quando um usuário invocar o comando `/resumir <texto>` ou responder a uma mensagem longa com `/resumir`, o sistema deve retornar um resumo claro e conciso.
* **ER04:** Quando um usuário invocar o comando `/traduzir [idioma] <texto>`, o sistema deve traduzir o texto para o idioma desejado (padrão: Inglês).
* **ER05:** Quando um usuário invocar o comando `/codigo <descrição>`, o sistema deve gerar código-fonte estruturado compatível com a linguagem descrita.
* **ER06:** Quando um usuário invocar o comando `/pesquisar <termo>`, o sistema deve realizar uma consulta na web usando a API do Tavily e retornar notícias e artigos recentes de forma consolidada.
* **ER07:** Quando um usuário invocar o comando `/lembrete <minutos> <mensagem>`, o sistema deve agendar uma notificação de lembrete com a mensagem especificada no tempo estipulado.
* **ER08:** Quando um usuário invocar o comando `/nova`, o sistema deve apagar o histórico de mensagens da sessão de conversação no banco de dados.
* **ER09:** Quando um usuário invocar o comando `/status`, o sistema deve exibir informações sobre o status da sessão e integridade do bot.
* **ER10:** Quando o usuário invocar o comando `/help` ou `/start`, o sistema deve retornar a lista e descrição dos comandos disponíveis.

### State-Driven Requirements (Orientados a Estado)
* **SR01:** Enquanto houver uma sessão de conversação activa para um chat ID específico, o sistema deve anexar o histórico de mensagens ao contexto do prompt de envio do Gemini para manter a memória da conversa.

### Unwanted Behavior Requirements (Comportamento Indesejado / Tratamento de Erros)
* **UB01:** Se o token `TELEGRAM_BOT_TOKEN` ou a chave `GEMINI_API_KEY` estiverem ausentes no arquivo `.env` durante a inicialização, o sistema deve interromper a execução e registrar um log de erro crítico.
* **UB02:** Se a chave de API `TAVILY_API_KEY` estiver ausente no ambiente ao invocar o comando `/pesquisar`, o sistema deve notificar o usuário de que a busca na internet está desativada por falta de configuração.
* **UB03:** Se o tempo fornecido no comando `/lembrete` não for um número válido entre 1 e 1440 minutos, o sistema deve retornar uma mensagem de erro indicando o formato correto do comando.
