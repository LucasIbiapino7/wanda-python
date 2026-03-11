# wanda-python

Microserviço Python da plataforma Wanda. Responsável pela validação e feedback do código dos alunos, execução de rounds das partidas e integração com a API da OpenAI.

---

## Pré-requisitos

**Para rodar com Docker:**
- Docker
- Docker Compose

**Para rodar manualmente:**
- Python 3.12
- Poetry

---

## Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

### Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `OPENAI_API_KEY` | Chave de acesso à API da OpenAI — **obrigatória** | `sk-proj-...` |
| `SERVICE_NAME` | Nome do serviço nos logs | `wanda-python` |
| `LOG_FORMAT` | Formato dos logs: `text` (dev) ou `json` (prod) | `text` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `OTEL_ENDPOINT` | Endpoint do OpenTelemetry Collector | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | Nome do serviço no OpenTelemetry | `wanda-python` |

> **Sobre a `OPENAI_API_KEY`:** a aplicação não sobe corretamente sem uma chave válida — ela é utilizada diretamente no fluxo de validação e feedback do código dos alunos.

> **Sobre o `OTEL_ENDPOINT`:** o endpoint padrão do OpenTelemetry Collector é `http://localhost:4317`. Não é obrigatório para o funcionamento da aplicação, mas se o collector não estiver rodando, erros de conexão aparecerão no terminal continuamente.

---

## Rodando com Docker

```bash
# Sobe o container (builda a imagem na primeira vez)
docker-compose up --build

# Rodar em background
docker-compose up --build -d

# Parar
docker-compose down
```

A aplicação estará disponível em `http://localhost:8000`.

> **Atenção:** o compose usa a rede externa `wanda-network`. Se ela não existir, crie antes:
> ```bash
> docker network create wanda-network
> ```

---

## Rodando manualmente

O projeto usa **python-dotenv** — as variáveis são lidas automaticamente do `.env` na raiz do projeto. Basta configurar o `.env` e rodar:

```bash
poetry run uvicorn wanda_python.app:app --host 0.0.0.0 --port 8000
```

A aplicação estará disponível em `http://localhost:8000`.

---

## Instalando dependências

```bash
poetry install
```
