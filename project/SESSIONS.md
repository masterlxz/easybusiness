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

### 2026-08-28 — Sessão 5

**Objetivo**: Fase 1.6, quarta fonte — cripto (CoinGecko + DefiLlama + alternative.me +
ultrasound.money).

**O que foi feito**:
- Escopo confirmado com o dono do projeto via `AskUserQuestion`: tudo — indicadores de saúde do
  ETH (TVL trend, net issuance, fees vs emissão, NVT ratio), Fear & Greed global, e
  cotação/histórico de qualquer moeda por símbolo.
- Decisão de design central: os 4 indicadores do ETH viram **um endpoint parametrizado por
  código** (`GET /v1/crypto/eth-indicators/{indicator_code}`), reaproveitando o padrão de
  catálogo já usado em `/v1/macro-series/{series_code}` — mais consistente aqui do que "1
  endpoint por capacidade" (padrão Yahoo/CVM) porque as 4 leituras são literalmente o mesmo
  shape (um número), só vindo de fontes HTTP diferentes. Sem a classificação GREEN/RED do
  Anchor (isso é regra de negócio da aplicação, não dado da fonte).
- `app/sources/crypto_common.py` (`CryptoDataError` único, compartilhado pelas 4 fontes) +
  `cripto_defillama.py`/`cripto_ultrasound.py`/`cripto_feargreed.py`/`cripto_coingecko.py`
  (reimplementação das 5 funções do Anchor) + `crypto_indicator_catalog.py` (catálogo travado
  aos 4 códigos já validados em produção).
- **Achado de testabilidade durante a implementação**: o catálogo inicialmente importava as
  funções de fetch direto (`from app.sources.cripto_defillama import fetch_tvl_trend_mom`),
  congelando a referência no dict no momento da construção — `patch()` nos testes não tinha
  efeito nenhum, porque o dataclass já guardava o objeto função original, não um lookup por
  nome. Corrigido trocando pra closures que fazem o lookup do atributo do módulo em tempo de
  chamada (`lambda: cripto_defillama.fetch_tvl_trend_mom()`) — mesma técnica que permite mockar
  função importada sem reescrever a chamada.
- 5 tabelas novas (`api/app/models/crypto.py`, migration `0004`): `crypto_indicators`,
  `crypto_fear_greed` (singleton, `id` sempre 1), `crypto_coin_resolution`, `crypto_quotes` (1
  linha, overwrite) e `crypto_price_history` (append-only).
- Extraído `app/services/append_only_list_cache.py` — generaliza o `_get_or_refresh_list` que
  só existia em `stock_service.py` (2º uso real do shape); `stock_service.py` refatorado pra
  usar a versão compartilhada, suite completa (83 testes) confirmada sem regressão antes de
  seguir com cripto.
- `app/services/crypto_service.py`: indicadores/Fear&Greed via `single_row_cache`; resolução
  símbolo→coin_id com cache próprio (TTL longo), reaproveitado entre `/quote` e
  `/price-history` (confirmado por teste: só 1 chamada de resolução pras duas rotas).
- 4 rotas sob `/v1/crypto/...` (`eth-indicators/{code}`, `fear-greed`, `{symbol}/quote`,
  `{symbol}/price-history`), mesma auth por `X-API-Key`.
- 30 novos testes automatizados (mockados) — todos passaram (após o fix de testabilidade
  acima); suite completa: 113 testes.
- Validado ao vivo contra as 4 APIs reais: TVL trend +21,4%, net issuance +0,86% anualizado,
  fees/emissão 0,015, NVT ratio 0,79 (todos os 4 indicadores do ETH); Fear & Greed 73
  ("Greed"); BTC quote ~US$80.462 e 365 pontos de histórico de preço; cache confirmado
  (`cached: true`); 404 pra indicador e símbolo desconhecidos; 401 sem chave.
- `project/PHASE.md` e `ARCHITECTURE.md` atualizados.

**Estado ao final**: Fase 1.6 com 7 de 11 fontes portadas (BCB SGS já contava fora da 1.6; nesta
fase: Yahoo Finance, CVM DFP+FII, CoinGecko+DefiLlama+alternative.me+ultrasound.money). Restam
4: bolsai (única que exige API key própria), B3 index stats, SEC EDGAR, Yahoo Metais. Trabalho
ainda não commitado — falta confirmar com o dono do projeto antes do push.

### 2026-08-28 — Sessão 6

**Objetivo**: fechar a Fase 1.6 — as últimas 4 fontes do catálogo (B3 index stats, Yahoo
Metais, bolsai, SEC EDGAR).

**O que foi feito**:
- Dois bloqueios de credencial resolvidos no início da sessão: `BOLSAI_API_KEY` (o dono do
  projeto tinha a chave, mas não sabia onde estava salva — encontrada em
  `anchor/data-collector/.env`, copiada pra `api/.env`) e `SEC_EDGAR_CONTACT_EMAIL` (confirmado
  com o dono do projeto). Ambas gitignored, nunca commitadas.
- Escopo confirmado via `AskUserQuestion`: tudo numa fatia só (SEC EDGAR sozinho tem
  complexidade parecida com a CVM — resolução ticker→CIK, fundamentos+DCF+payout, fallback de
  tags — mas o dono do projeto preferiu fechar a fase de uma vez), sem REIT fundamentals
  (capacidade extra do Anchor fora do catálogo original de 12 fontes).
- Achado ao reler `stocks.py` durante o planejamento: `acoes_yahoo.fetch_quote`/
  `fetch_price_history` usam `suffix=".SA"` por padrão e nunca eram chamadas com outro valor —
  `/v1/stocks/{ticker}/...` só serve tickers B3. Por isso SEC EDGAR (mercado americano) ganhou
  namespace próprio (`/v1/us-stocks/{ticker}/...`) em vez de reaproveitar `/v1/stocks/`.
- `api/app/sources/b3_index_stats.py` + `b3_index_catalog.py` (catálogo travado: IFIX/SMLL/IDIV,
  ano-base fixo por índice).
- `api/app/sources/metals_catalog.py` — **sem cliente HTTP novo**, reusa
  `acoes_yahoo.fetch_quote`/`fetch_price_history` direto com `suffix=""` (só um catálogo de 4
  símbolos XAU/XAG/XPT/XPD).
- `api/app/sources/acoes_bolsai.py` (fundamentos BR, expõe `cvm_code` pra encadear com
  `/v1/companies/...`; `roe` exposto como vem da fonte, com ressalva de confiabilidade
  documentada) e `api/app/sources/sec_edgar.py` (fundamentos/DCF/payout US, resolução
  ticker→CIK cacheada, rate limit ~9 req/s portado do Anchor).
- Renomeado `cvm_ttl_seconds` → `fundamentals_ttl_seconds` em `config.py`/`.env`/
  `.env.example`/`companies.py`/`fiis.py` — bolsai e SEC EDGAR reusam o mesmo campo (3º uso da
  mesma semântica: fundamento trimestral/anual).
- 8 tabelas novas (migration `0005`): `b3_index_history`, `metal_quotes`,
  `metal_price_history`, `stock_bolsai_fundamentals`, `sec_edgar_cik_resolution`,
  `us_stock_fundamentals`, `us_stock_dcf_fundamentals`, `us_stock_payout_avg`.
- Serviços: `b3_index_service.py`, `metal_service.py`, `us_stock_service.py` (resolução de CIK
  reaproveitada entre os 3 endpoints, mesmo padrão do `crypto_coin_resolution`), e
  `stock_service.py` ganhou `get_or_refresh_bolsai_fundamentals`.
- 7 rotas novas: `GET /v1/b3-indexes/{index_code}/history`, `GET /v1/metals/{metal_code}/
  {quote,price-history}`, `GET /v1/stocks/{ticker}/bolsai-fundamentals` (no router já
  existente), `GET /v1/us-stocks/{ticker}/{fundamentals,dcf-fundamentals,payout}`.
- 49 novos testes automatizados (mockados) — incluindo o SEC EDGAR com fixtures de tags XBRL
  fiéis ao formato real (duration/instant rows) — todos passaram; suite completa: 162 testes.
- Validado ao vivo contra as 4 APIs reais: IFIX com 3.885 pontos desde 2010; ouro (XAU)
  cotado; bolsai/PETR4 retornando `cvm_code: "9512"` (bate com o CVM); **SEC EDGAR/AAPL com
  payout médio 5a de 15,08% — número real e bem conhecido (a Apple retém a maior parte do lucro
  pra buyback em vez de dividendo)**, forte confirmação da lógica portada; **JPM (banco)
  retornou 404 em `/dcf-fundamentals` como esperado**, confirmando que a lacuna de taxonomia
  bancária documentada pelo Anchor foi reproduzida corretamente; cache/401/404 confirmados em
  todos os endpoints novos.
- `project/PHASE.md`, `ARCHITECTURE.md` e `OVERVIEW.md` atualizados.

**Estado ao final**: **Fase 1.6 completa — as 11 fontes do catálogo original portadas.**
Próximo passo natural: Fase 1.7 (migrar o Anchor pra consumir a Super API em vez de rodar
`data-collector/main.py` localmente) ou Fase 1.8 (documentação pública da API). Trabalho ainda
não commitado — falta confirmar com o dono do projeto antes do push.

### 2026-08-28 — Sessão 7

**Objetivo**: Fase 1.7 — migrar o Anchor (`../anchor`) pra consumir a Super API em vez de rodar
`data-collector/main.py` localmente. Confirmado commit da Sessão 6 já estava no repo
(`4072a3e`) antes de começar.

**O que foi feito**:
- 2 agentes `Explore` em paralelo (um por repo) mapearam o contrato completo: toda função de
  `anchor/data-collector/sources/*.py` (assinatura, shape de retorno, chaves de API) de um lado,
  todo endpoint/schema da Super API do outro. Achado central: **a Super API não cobre 100% do
  que o Anchor fazia** — cotação/técnicos/dividendos/preço de ticker sem sufixo `.SA` (ação
  US/ETF US/REIT), indicadores imobiliários de REIT, IBOV, e `resolve_cnpj` de FII (nunca
  portada, decisão da Sessão 4) não têm endpoint equivalente.
- Escopo confirmado com o dono do projeto via `AskUserQuestion`: migração **híbrida** — migra o
  que a API já cobre, deixa o resto local, sem estender a API agora (candidato a "Fase 1.6b"
  registrado em `ROADMAP.md`).
- Bug achado na exploração (`GET /v1/fiis/{cnpj}/properties` não captura `FundNotFoundError`) —
  investigado a fundo antes de "corrigir": lendo `fii_service.py` de verdade, a causa não é um
  bug de exceção não capturada, é ambiguidade de fonte — lista vazia serve tanto pra CNPJ
  desconhecido quanto pra FII de papel/recebíveis sem imóvel nenhum, e não dá pra distinguir os
  dois com o dado que a CVM fornece. Confirmado com o dono do projeto: **não mexer**, documentar
  como limitação consciente (`PENDING.md` item P1) — "corrigir" arriscaria classificar um FII de
  papel válido como "não encontrado" na primeira chamada.
- `anchor/data-collector/sources/super_api_client.py` (módulo novo, repo do Anchor): ~20
  funções-wrapper que replicam a forma exata das funções antigas que substituem, escondendo o
  loop por identificador (Super API só aceita um por chamada, decisão de design já registrada em
  `ARCHITECTURE.md`) — mantém o corpo das `collect_*` de `main.py` quase intocado.
- Módulos deletados no Anchor (100% redundantes): `bcb_sgs.py`, `cvm_dfp.py`,
  `b3_index_stats.py`, `metais_yahoo.py`, `cripto_defillama.py`, `cripto_ultrasound.py`,
  `cripto_feargreed.py`, `cripto_coingecko.py`. Trimados (só a fatia migrada saiu):
  `acoes_bolsai.py`, `cvm_fii.py`, `sec_edgar.py`.
- **2 bugs achados e corrigidos durante a validação ao vivo** (não durante o planejamento):
  (1) primeira versão do `super_api_client.py` capturava `SuperApiError` genérico dentro do loop
  por-ticker — rodando com a Super API derrubada de propósito (`docker compose stop api`), o
  coletor terminava `exit 0`/"Updated 0 quote(s)" em vez de falhar alto, mascarando
  indisponibilidade total como "sem dado nenhum". Corrigido pra só capturar 404
  (`SuperApiNotFoundError`) dentro do loop, erro de rede/5xx propaga. (2) `/v1/metals/{code}` e
  `/v1/b3-indexes/{code}` usam catálogo minúsculo (`xau`, `ifix`), Anchor sempre trabalhou
  maiúsculo — `.lower()` só na URL, sem mudar o ticker gravado no SQLite dele. (3) códigos dos 4
  indicadores ETH usam hífen (`tvl-trend`), Anchor usa underscore internamente (`tvl_trend`,
  chave de `indicator_thresholds`) — corrigido nos call sites, sem tocar no schema do Anchor.
- Validado ao vivo, ponta a ponta, contra a Super API real (`docker compose up`) e o
  `anchor.db` real: `--ticker PETR4`/`MGLU3`, `crypto` (4 indicadores ETH), `--crypto-ticker
  BTC`, `--metal-ticker XAU`, `--benchmark-returns` (7 benchmarks), `--fii-cvm-data`, `--us-ticker
  AAPL` (payout 15,08%, mesmo número confirmado na Sessão 6). Confirmado que o que ficou local
  segue funcionando sem a Super API: `--reit-ticker`, `--etf-us-ticker`, `--fii-resolve-cnpj`.
  Suíte da Super API: 162/162 (sem regressão, nenhum endpoint tocado).
- `project/PENDING.md`, `PHASE.md`, `ROADMAP.md` (aqui) e `project/SESSIONS.md` do Anchor
  (Sessão 88, relato completo da migração do lado dele) atualizados.

**Estado ao final**: Fase 1.7 completa (migração híbrida). Próximo passo natural: Fase 1.8
(documentação pública da API) ou, no Anchor, considerar a "Fase 1.6b" registrada em
`ROADMAP.md` se algum consumidor futuro precisar do que ficou de fora. Trabalho ainda não
commitado nos dois repos — falta confirmar com o dono do projeto antes do push.
