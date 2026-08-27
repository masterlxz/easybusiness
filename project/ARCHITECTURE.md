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

---

## Débitos Técnicos de Arquitetura

Nenhum ainda.
