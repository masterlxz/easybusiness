## Decisões de Arquitetura em Aberto

| Decisão | Opções | Status |
|---|---|---|
| Linguagem/framework da Super API | Python (FastAPI, reaproveita o conhecimento do `data-collector` do Anchor) vs Node/TypeScript vs Rust | **Decidido (Sessão 2) — Python + FastAPI**, confirmado com o dono do projeto via `AskUserQuestion` |
| Banco de dados (Super DB) | PostgreSQL vs SQLite (Anchor usa SQLite hoje, mas é single-consumer; Super DB precisa servir múltiplos consumidores concorrentes) | **Decidido (Sessão 2) — PostgreSQL** (17-alpine via Docker Compose) |
| Autenticação da API | API key simples (header) vs OAuth/JWT | **Decidido (Sessão 2) — API key estática via header `X-API-Key`**, lista de chaves aceitas em `API_KEYS` (env, separadas por vírgula) — sem tabela/admin de chaves ainda, decisão consciente de MVP; virar multi-consumidor de verdade (chave por consumidor, rotação) é trabalho futuro |
| Hospedagem | Self-host (Docker, mesmo padrão do TruthID/Anchor) vs Cloud gerenciado | **Decidido (Sessão 2) — self-host via Docker Compose**, mesmo padrão usado pelo `aporte-facil` (o projeto irmão mais próximo em stack: Python + Postgres + Docker) — `docker-compose.yml` na raiz do repo, `api/` como componente (`build: ./api`); cloud gerenciado fica pra Fase 4 (Workspace) do blueprint |
| Cadência de coleta por fonte | Sob demanda (como o botão manual do Anchor) vs job agendado (cron) vs híbrido | **Pendente para as próximas fontes** — BCB SGS (Sessão 2) usa cache-through sob demanda com TTL configurável (`CACHE_TTL_SECONDS`, padrão 3600s), não cron; cadência das demais fontes do catálogo (`CONTEXT.md`) segue em aberto |
| Licença open-source | MIT (mesma do TruthID/Anchor) vs AGPL (mencionada no blueprint como opção pro open-core) | **Decidido (Sessão 2) — MIT**, mesma licença do TruthID/Anchor/aporte-facil |

---

## Catálogo técnico das fontes

Ver tabela completa (fonte × domínio × observação) em `CONTEXT.md`, seção "Catálogo de Fontes
de Dados". Esta seção registra, por fonte, decisões técnicas de implementação conforme forem
tomadas.

### BCB SGS (`api/app/sources/bcb_sgs.py`) — Sessão 2

- Biblioteca HTTP: `requests`, timeout 15s, sem retry ainda (erro vira `BcbSgsError` e propaga
  — MVP; se já existir cache pra série, o service serve stale em vez de falhar, ver
  `macro_series_service.py`).
- Séries portadas: CDI (código BCB 4391), IPCA (código BCB 433) — catálogo travado em
  `api/app/sources/catalog.py`, não adicionar código especulativo sem confirmar contra a API
  real primeiro.
- TTL de cache: configurável via `CACHE_TTL_SECONDS` (padrão 3600s).
- Upsert: `INSERT ... ON CONFLICT (series_code, reference_month) DO UPDATE` — equivalente
  Postgres do `INSERT OR REPLACE` que o Anchor usa pra essas duas séries (BCB revisa o valor do
  mês corrente depois de publicado).
- Validado ao vivo contra a API real (Sessão 2): 481 pontos de CDI (desde 1986-08),
  559 pontos de IPCA (desde ~1979), ambos servidos do cache numa segunda chamada imediata.

### Yahoo Finance (`api/app/sources/acoes_yahoo.py`) — Sessão 3

- Biblioteca HTTP: `requests`, timeout 15s, helper privado `_fetch_chart()` compartilhado
  pelas 5 funções (evita repetir o bloco try/except 5x como o Anchor faz).
- Capacidades portadas: cotação (`/quote`), técnicos SMA50/100/200 + CAGR5/10y
  (`/technicals`), dividendo médio 5 anos (`/dividends-avg`), histórico diário de preço 10
  anos (`/price-history`), histórico de pagamentos de dividendo (`/dividend-payments`) — todas
  sob `GET /v1/stocks/{ticker}/...`.
  Diferença de design vs. o Anchor: cada função recebe **um** ticker (não uma lista) — nossa
  API atende um ticker por requisição, então erro de um ticker é erro da requisição, não algo
  a "pular e continuar" (isso só faz sentido em job batch).
- TTL: `stock_quote_ttl_seconds` (padrão 300s, preço muda rápido) só pra `/quote`;
  `cache_ttl_seconds` (padrão 3600s) pras outras 4 (mudam devagar).
- Upsert: `stock_quotes`/`stock_technicals`/`stock_dividends_avg` — `ON CONFLICT DO UPDATE`
  (1 linha por ticker, sobrescrita a cada refresh). `stock_price_history`/
  `stock_dividend_payments` — `ON CONFLICT DO NOTHING` (fato histórico imutável, mesmo
  raciocínio do `INSERT OR IGNORE` que o Anchor usa pra essas duas tabelas).
- `dividends-avg` tem um terceiro estado além de sucesso/erro de fonte: "sem dado" (ticker sem
  histórico de dividendo, ex. growth stock) — não é falha, vira 404 só quando não há cache
  nenhum ainda; se já existe cache, o serviço mantém servindo o valor existente em vez de
  apagá-lo.
- Validado ao vivo contra a API real (Sessão 3, ticker PETR4): cotação R$42,70, 2.491 pontos de
  histórico de preço (desde ~2016), 34 pagamentos de dividendo, técnicos e dividendo médio
  (5y) calculados corretamente; segunda chamada de `/quote` serviu do cache
  (`cached: true`).

---

## Débitos Técnicos de Arquitetura

Nenhum ainda.
