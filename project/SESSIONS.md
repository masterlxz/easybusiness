## Log de Sessões

### 2026-08-27 — Sessão 1

**Objetivo**: bootstrap do projeto EasyBusiness a partir do blueprint original
(`blueprint_plataforma_opensource.md.docx`).

**O que foi feito**:
- Lido o blueprint (`.docx`, extraído via `python3`/`zipfile` já que não havia `pandoc`/
  `python-docx` disponíveis no ambiente) — descreve uma plataforma de 3 camadas (APIs/SDKs,
  Workspace web, módulo B3).
- Decidido, junto com o dono do projeto, que o MVP começa pela camada financeira: uma "Super
  API" alimentando um "Super Banco de Dados" central, com o objetivo declarado de centralizar
  a coleta de dados que hoje está espalhada no projeto Anchor.
- Estudado `anchor/data-collector/sources/` (12 clientes Python: Yahoo Finance, bolsai, B3,
  BCB SGS, CVM DFP/FII, SEC EDGAR, Yahoo Metais, CoinGecko, DefiLlama, alternative.me,
  ultrasound.money) — catalogado em `CONTEXT.md` como ponto de partida da Fase 1.
- Estudada a estrutura `project/` do TruthID
  (`INDEX/OVERVIEW/CONTEXT/ARCHITECTURE/GUIDELINES/PHASE/ROADMAP/PENDING/SESSIONS.md`) como
  modelo — replicada aqui com conteúdo próprio do EasyBusiness (sem `AUTH_FLOW.md`, que é
  específico do fluxo de login do TruthID).
- Criado o repositório público `masterlxz/easybusiness` no GitHub.
- Removido `blueprint_plataforma_opensource.md.docx` do repo — conteúdo já incorporado em
  `CONTEXT.md`/`ROADMAP.md`.

**Estado ao final**: `project/` criado com as 9 páginas; nenhum código escrito ainda (Fase 1,
etapa 1.2, decidir a stack, é o próximo passo).

### 2026-08-27 — Sessão 2

**Objetivo**: primeira prova de conceito ponta a ponta da Super API (Fase 1, etapas 1.2-1.5).

**O que foi feito**:
- Stack decidida com o dono do projeto via `AskUserQuestion`: Python + FastAPI (reaproveita o
  conhecimento do `data-collector` do Anchor).
- Pesquisado `aporte-facil` (outro projeto do autor) como referência de infraestrutura — é o
  único projeto irmão já rodando Python + PostgreSQL via Docker Compose; seguido o mesmo padrão
  (`docker-compose.yml` na raiz orquestrando componentes por pasta, `user: "1000:1000"` pra
  evitar arquivos root via bind mount, credenciais fixas em dev).
- Criado o componente `api/` (FastAPI + SQLAlchemy + Alembic): `app/config.py` (settings via
  env), `app/database.py`, `app/auth.py` (API key estática via header `X-API-Key`),
  `app/models/macro_series.py` (tabela `macro_series_monthly`, PK composta
  series_code+reference_month), `app/sources/bcb_sgs.py` (cliente BCB SGS reimplementado a
  partir de `anchor/data-collector/sources/bcb_sgs.py`), `app/sources/catalog.py` (catálogo
  travado: só CDI e IPCA, as séries já validadas em produção pelo Anchor),
  `app/services/macro_series_service.py` (cache-through: serve do Postgres se fresco, senão
  busca na fonte e faz upsert via `ON CONFLICT DO UPDATE`), `app/routers/macro_series.py`
  (`GET /v1/macro-series/{series_code}`).
- Migration Alembic inicial (`0001_create_macro_series_monthly`).
- `docker-compose.yml` (raiz), `api/Dockerfile`, `.env.example`, `requirements.txt`.
- `README.md`, `LICENSE` (MIT, mesmo texto do `anchor/LICENSE`) e `.gitignore` criados na raiz
  do repo — antes só existia `project/`.
- 14 testes automatizados (mockados, sem rede real) cobrindo o cliente BCB SGS, o service de
  cache-through e o router — dois bugs reais achados e corrigidos pelos próprios testes: (1) o
  parsing da resposta do BCB não estava dentro do `try/except`, então um payload malformado
  vazava `KeyError` cru em vez de virar `BcbSgsError`; (2) `alembic.ini` sem
  `prepend_sys_path = .` fazia o `ModuleNotFoundError: No module named 'app'` no `alembic
  upgrade head` dentro do container (cwd `/app` não entra em `sys.path` sozinho pra um console
  script instalado).
- Validado ao vivo contra a API real do BCB (`docker compose up`, sem mock): CDI (481 pontos
  desde 1986-08) e IPCA (559 pontos) retornados com sucesso; segunda chamada imediata serviu do
  Postgres (`cached: true`, sem bater no BCB de novo); 401 sem header/com chave errada; 404 pra
  série fora do catálogo (`selic`); dados conferidos direto via `psql`.
- `project/PHASE.md`, `ARCHITECTURE.md` e `OVERVIEW.md` atualizados refletindo o progresso.

**Estado ao final**: Fase 1, etapas 1.2-1.5 concluídas e validadas ponta a ponta. Próximo passo
é a 1.6 (portar as fontes restantes do catálogo). Trabalho ainda não commitado — falta
confirmar com o dono do projeto antes do push.

### 2026-08-27 — Sessão 3

**Objetivo**: Fase 1.6, primeira fonte adicional — Yahoo Finance (cotação, técnicos,
dividendos, histórico de preço).

**O que foi feito**:
- Escopo confirmado com o dono do projeto via `AskUserQuestion`: portar as 5 capacidades do
  `acoes_yahoo.py` do Anchor de uma vez (não só cotação) — fatia maior que a da Sessão 2, mas
  mesmo padrão de arquitetura (source → service cache-through → schema → router).
- Extraído `_is_fresh` de `macro_series_service.py` pra `app/services/freshness.py`
  (compartilhado com o novo `stock_service.py`), única mudança em código já existente.
- `app/sources/acoes_yahoo.py`: reimplementação das 5 funções do Anchor
  (`fetch_quote`/`fetch_price_history`/`fetch_dividends_avg`/`fetch_technicals`/
  `fetch_dividend_payments`), recebendo um ticker por chamada (não lista, diferente do Anchor
  — nossa API é por-requisição) com um helper HTTP compartilhado.
- 5 tabelas novas (`api/app/models/stock.py`, migration `0002`): `stock_quotes`,
  `stock_technicals`, `stock_dividends_avg` (upsert por sobrescrita) e `stock_price_history`,
  `stock_dividend_payments` (upsert só-insere, fato histórico imutável).
- `app/services/stock_service.py`: dois orquestradores genéricos reaproveitados pelas 5
  capacidades (`_get_or_refresh_single_row`, `_get_or_refresh_list`), mais o tratamento
  especial de `dividends-avg` (estado "sem dado" — 404 só sem cache, senão mantém servindo o
  cache existente).
- 5 rotas sob `GET /v1/stocks/{ticker}/...` (`quote`, `technicals`, `dividends-avg`,
  `price-history`, `dividend-payments`), mesma auth por `X-API-Key`.
- 30 novos testes automatizados (mockados) — cliente Yahoo, service (padrão 1-linha via quote,
  padrão lista-append via price-history, smoke tests dos outros 3) e router — todos passaram
  de primeira, mais os 14 já existentes (44 no total).
- Validado ao vivo contra o Yahoo real (ticker PETR4): cotação R$42,70, técnicos (SMA/CAGR)
  calculados, dividendo médio 5a R$7,88, 2.491 pontos de histórico de preço, 34 pagamentos de
  dividendo; MGLU3 confirmou que `dividends-avg` funciona pra outro ticker; cache confirmado
  (`cached: true` numa segunda chamada de `/quote`); 401 sem header.
- `project/PHASE.md` e `ARCHITECTURE.md` atualizados.

**Estado ao final**: Fase 1.6 com 2 de ~11 fontes portadas (BCB SGS, Yahoo Finance). Próxima
fonte candidata: bolsai (fundamentos de ação BR, mas exige API key própria — diferente das
duas primeiras) ou CVM DFP/FII (dados abertos, sem chave). Trabalho ainda não commitado.

### 2026-08-27/28 — Sessão 4

**Objetivo**: Fase 1.6, terceira fonte — CVM (fundamentos DFP: ROE/payout/DCF; FII: indicadores
mensais + imóveis).

**O que foi feito**:
- Escopo confirmado com o dono do projeto via `AskUserQuestion`: portar `cvm_dfp.py` completo +
  `cvm_fii.py` (não só uma fatia). Antes de planejar em detalhe, baixei e inspecionei os zips
  reais da CVM (DFP e FII) pra confirmar 100% do schema documentado nos docstrings do Anchor
  (formato de `CD_CVM`/`CNPJ_Fundo_Classe`/datas, nomes de coluna) em vez de planejar em cima de
  suposição — zips apagados depois da inspeção.
- Decisão de design central: como a resolução ticker→código-CVM/CNPJ do Anchor depende da
  bolsai (fonte paga, não portada), os 5 endpoints novos recebem **código CVM**/**CNPJ**
  diretamente (não ticker) — `resolve_cnpj` do Anchor não foi portado.
- `api/app/sources/cvm_dfp.py`/`cvm_fii.py`: reimplementação completa (identificadores em
  inglês) — download+cache de zip em disco (`api/.cache/`, gitignored), parsing de CSV
  `;`-delimitado/`latin1`, `_find_exact`/`_find_by_keyword` (D&A/Capex por busca de texto,
  contas sem código padronizado entre empresas), `_effective_tax_rate`, `_nwc_change`,
  normalização de CNPJ (`normalize_cnpj`).
- 5 tabelas novas (`api/app/models/company.py`/`fii.py`, migration `0003`): `company_roe`,
  `company_payout_avg`, `company_dcf_fundamentals` (1 linha por cvm_code, overwrite),
  `fii_monthly_indicators` (1 linha por cnpj, overwrite), `fii_properties` (N linhas por cnpj,
  refresh via delete-e-insere do conjunto inteiro).
- Extraído `app/services/single_row_cache.py` — generaliza o cache-through "1 linha, overwrite"
  que antes só existia dentro de `stock_service.py`; refatorado `stock_service.py` pra usar a
  versão compartilhada (comportamento idêntico, suite de 44 testes da Sessão 3 confirmada sem
  regressão antes de seguir com CVM).
- `app/services/company_service.py` (roe/payout/dcf via helper compartilhado) +
  `app/services/fii_service.py` (monthly_indicators via helper compartilhado; properties com
  lógica própria de delete-e-insere).
- 5 rotas: `GET /v1/companies/{cvm_code}/{roe,payout,dcf-fundamentals}` e
  `GET /v1/fiis/{cnpj}/{monthly-indicators,properties}`, mesma auth por `X-API-Key`.
- 39 novos testes automatizados (mockados) — incluindo `tests/cvm_fixtures.py` (helper que monta
  zip em memória com CSV fiel ao schema real confirmado) — todos passaram de primeira nos
  clientes CVM (14) e services/routers (25); suite completa: 83 testes.
- Validado ao vivo contra a CVM real: VALE3 (CD_CVM 4170) — ROE 6,25%, **alíquota efetiva
  55,75% batendo exatamente com o número citado no docstring original do Anchor pra essa mesma
  empresa** (forte confirmação da lógica portada), payout médio 5a 61,38% (~19s, 5 zips); FII
  CNPJ `00332266000131` — indicador mensal e imóvel (Via Parque Shopping) corretos; 404/401/
  cache confirmados.
- `project/PHASE.md` e `ARCHITECTURE.md` atualizados.

**Estado ao final**: Fase 1.6 com 3 de ~11 fontes portadas (BCB SGS, Yahoo Finance, CVM
DFP+FII). Próxima fonte candidata: bolsai (exige API key própria) ou uma das fontes de cripto
(CoinGecko/DefiLlama/alternative.me/ultrasound.money, todas sem chave). Trabalho ainda não
commitado — falta confirmar com o dono do projeto antes do push.
