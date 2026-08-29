## Fases Detalhadas

### Fase 1 — Finance API + Finance DB (MVP)

**Objetivo**: centralizar, num único serviço confiável, a coleta de dados financeiros que hoje
o Anchor faz de forma isolada (`data-collector/`), expondo tudo via uma API HTTP/JSON — ver
`CONTEXT.md` para o PRD completo e o catálogo de fontes herdado do Anchor.

**Etapas**:
- [x] 1.1 — Setup do repositório (Sessão 1: GitHub criado, `project/` criado com o blueprint incorporado)
- [x] 1.2 — Stack decidida (Sessão 2): Python + FastAPI, PostgreSQL, self-host via Docker Compose
- [x] 1.3 — Schema inicial via Alembic: `macro_series_monthly` (series_code, reference_month, value_pct, source, fetched_at) — `api/app/models/macro_series.py`
- [x] 1.4 — Primeira fonte portada (Sessão 2): BCB SGS (CDI e IPCA), reimplementada em `api/app/sources/bcb_sgs.py`, validada ao vivo contra a API real (481 pontos de CDI desde 1986, 559 de IPCA)
- [x] 1.5 — Contrato definido e validado: `GET /v1/macro-series/{series_code}` com auth por `X-API-Key`, cache-through com TTL configurável (`api/app/services/macro_series_service.py`)
- [x] 1.6 — Portar as fontes restantes do catálogo, uma a uma (11/11 portadas — Fase 1.6 completa)
  - [x] Yahoo Finance (Sessão 3): cotação, técnicos (SMA/CAGR), dividendo médio 5a, histórico de preço, histórico de pagamentos — `api/app/sources/acoes_yahoo.py`, 5 endpoints sob `/v1/stocks/{ticker}/...`, validado ao vivo (PETR4/MGLU3)
  - [x] CVM DFP + FII (Sessão 4): ROE, payout médio 5a, 9 campos do DCF (empresas, por código CVM) + indicadores mensais e imóveis (FII, por CNPJ) — `api/app/sources/cvm_dfp.py`/`cvm_fii.py`, 5 endpoints sob `/v1/companies/{cvm_code}/...` e `/v1/fiis/{cnpj}/...`, validado ao vivo (VALE3/CD_CVM 4170, FII CNPJ 00332266000131)
  - [x] Cripto — CoinGecko + DefiLlama + alternative.me + ultrasound.money (Sessão 5): 4 indicadores de saúde do ETH (TVL trend, net issuance, fees vs emissão, NVT ratio) via catálogo parametrizado, Fear & Greed global, cotação/histórico de qualquer moeda por símbolo — `api/app/sources/cripto_*.py`, 4 endpoints sob `/v1/crypto/...`, validado ao vivo (indicadores reais do ETH, BTC quote+365 pontos de histórico)
  - [x] B3 index stats + Yahoo Metais + bolsai + SEC EDGAR (Sessão 6): histórico de índices B3 (IFIX/SMLL/IDIV, catálogo travado), cotação/histórico de metais preciosos (reaproveita `acoes_yahoo.py` sem cliente HTTP novo), fundamentos bolsai (ticker BR, chave própria), fundamentos/DCF/payout SEC EDGAR (ticker US, resolução CIK cacheada) — 7 endpoints novos sob `/v1/b3-indexes/...`, `/v1/metals/...`, `/v1/stocks/{ticker}/bolsai-fundamentals` e `/v1/us-stocks/...`, validado ao vivo (IFIX 3.885 pontos, ouro, PETR4 via bolsai, AAPL fundamentos/DCF/payout, JPM 404 esperado — banco sem taxonomia compatível)
- [x] 1.7 — Anchor passa a consumir a Finance API em vez de rodar `data-collector/main.py` localmente (Sessão 7, migração **híbrida**): tudo que a Finance API já cobre migrou pra HTTP (`anchor/data-collector/sources/finance_api_client.py`, módulo novo) — ação BR (cotação/técnicos/dividendos/histórico/proventos/fundamentos+DCF), CDI/IPCA, IFIX/SMLL/IDIV, FII (indicadores+imóveis), os 4 indicadores ETH + Fear&Greed + cotação/histórico de cripto, os 4 metais, fundamentos/DCF/payout de ação americana comum. Ficou local, sem endpoint equivalente na Finance API: cotação/técnicos/dividendos/preço de ticker sem sufixo `.SA` (US/ETF/REIT), REIT fundamentals, IBOV, `resolve_cnpj` de FII — candidatos a uma "Fase 1.6b" futura (ver `ROADMAP.md`). Bug achado nesta sessão em `/v1/fiis/{cnpj}/properties` (não distingue CNPJ desconhecido de FII sem imóvel) registrado como pendência consciente, não corrigido — ver `PENDING.md` item P1. Detalhes completos da migração (mapeamento função-por-função, achados de casing/exceção) no `SESSIONS.md` do Anchor, Sessão 88.
- [x] 1.8 — Documentação pública da API (Sessão 7): componente novo `docs/` — Next.js (App Router) +
  Fumadocs, mesmo padrão do TruthID (`site/frontend`, esclarecido nesta sessão: não é Docusaurus)
  mas bem mais enxuto (sem i18n/next-intl — inglês único, conforme `GUIDELINES.md`; sem conta/
  backend, que é conversa de Fase 4). Conteúdo em inglês: `index`/`quickstart` + 4 páginas de
  conceitos (`auth`/`caching`/`catalog`/`errors`) escritas à mão; a referência de cada endpoint
  (`content/docs/reference/`) é **gerada**, não commitada — `scripts/generate-reference.mjs` roda
  no `predev`/`prebuild` via `fumadocs-openapi`, lendo o `/openapi.json` que a FastAPI já expõe de
  graça, pra nunca ficar desatualizada conforme a API cresce. Novo serviço `docs` no
  `docker-compose.yml` (porta 3000, dev mode, mesmo padrão bind-mount + `npm run dev` do TruthID —
  inclusive sem `user: "1000:1000"`, pelo mesmo motivo que o `frontend` deles não tem: o volume
  nomeado de `node_modules` nasce root-owned). Busca embutida do Fumadocs (`/api/search`, Orama,
  zero serviço externo). Sem deploy público ainda (self-host, mesmo estágio da própria API).
  Validado ao vivo via `docker compose up --build` de ponta a ponta (não só localmente): API
  sobe, `docs` gera a referência contra `http://api:8000/openapi.json`, `next build` compila as
  34 páginas sem erro, `/docs`/`/docs/reference/...`/`/docs/concepts/...`/busca respondem 200 com
  conteúdo real. **Fase 1 completa.**
- [x] 1.9 — Deploy público dos docs no GitHub Pages (Sessão 8, mesmo dia): pedido explícito do
  dono do projeto, subpath padrão do GitHub Pages (`https://masterlxz.github.io/easybusiness/docs/`,
  sem domínio próprio). `next.config.ts` ganhou export estático condicional (`output: "export"` +
  `basePath` só quando `NEXT_BASE_PATH` está setada — dev/docker-compose continuam dinâmicos, sem
  mudança). `.github/workflows/deploy-docs.yml` (mesmo padrão do TruthID: `actions/checkout` →
  build → `actions/deploy-pages`) gera um snapshot do schema OpenAPI **sem precisar de banco nem
  API rodando** — `app.openapi()` é reflexão pura sobre rotas/schemas Pydantic, `create_engine()`
  nunca conecta de fato, então um `DATABASE_URL` placeholder basta só pra importar `app.main`
  (confirmado idêntico byte-a-byte contra o schema real antes de commitar essa abordagem).
  `scripts/generate-reference.mjs`/`lib/openapi.ts` ganharam um segundo modo
  (`OPENAPI_SCHEMA_PATH`, arquivo local) ao lado do HTTP existente, sem mudar o comportamento de
  dev. GitHub Pages habilitado no repo via `gh api repos/.../pages` (`build_type: workflow`).
  Validado ao vivo antes do push: build estático local com `NEXT_BASE_PATH=/easybusiness` — todo
  link/asset/favicon no HTML gerado já sai prefixado `/easybusiness/...` corretamente, página de
  referência real renderizada, índice de busca virou arquivo estático.
- [x] 1.10 — Modo SQLite "free/local" (Sessão 10): pedido do dono do projeto pra fechar o
  ciclo Open-Core registrado em `ROADMAP.md` — o Anchor precisa rodar a Finance API localmente
  sem Docker/Postgres, "já instalada", como binário sidecar compilado (mesmo mecanismo que
  `data-collector/` já usa no Anchor desde a Fase 11.3 dele). Achados os 3 únicos pontos
  Postgres-specific do código (`single_row_cache.py`/`append_only_list_cache.py`/
  `macro_series_service.py`, todos `sqlalchemy.dialects.postgresql.insert` com
  `on_conflict_do_*`) — resolvidos com um dispatcher de dialeto (`app/services/db_dialect.py`)
  que troca pra `sqlalchemy.dialects.sqlite.insert` em runtime (API idêntica nos dois dialetos,
  SQLite ≥3.24 suporta `ON CONFLICT` nativo). Nenhuma outra parte do código (`models/`,
  migrations Alembic) tinha algo Postgres-only. Novo `api/sidecar_main.py`: roda as migrations
  Alembic programaticamente até `head` (mesmo histórico do path Postgres, evolui um db local
  existente entre versões do app, ao contrário de `create_all()`), sobe uvicorn passando o objeto
  `app` direto (não a string `"app.main:app"` — binário PyInstaller-frozen não resolve import
  dinâmico), porta OS-assigned anunciada via `SIDECAR_PORT=<porta>` na primeira linha do stdout
  (sinal de prontidão pro processo que embutir o sidecar — Anchor, Fase 14.2 dele, ainda não
  desenhada). `DATABASE_URL`/`API_KEYS` continuam simples env vars, zero mudança em
  `config.py`/`auth.py`. Validado ao vivo: script interpretado E binário compilado
  (`pyinstaller --onefile`) rodando de verdade contra SQLite, Alembic criou as 22 tabelas das 5
  migrations, `/healthz` e `/v1/macro-series/{cdi,ipca}` responderam 200 com fetch real da BCB
  SGS + upsert de verdade no SQLite (não mock). Suite completa (`docker compose exec api pytest`,
  path Postgres) continua 162/162 depois do refactor do dialeto — sem regressão. Fecha só a
  camada de empacotamento; o consumo pelo Anchor (CI, lifecycle do sidecar, migração do
  fetch+write) fica pra sessões futuras, roadmap completo na Fase 14 do `PHASE.md` do Anchor.
- [x] 1.11 — Fecha a lacuna deixada pela migração híbrida (1.6b, ver `ROADMAP.md`): as 4
  capacidades que sobraram locais no `data-collector/` do Anchor por falta de endpoint
  equivalente. **1.11.1** — cotação/técnicos/dividendos/histórico de preço/proventos pra
  ticker sem sufixo `.SA` (ação americana, ETF-US, REIT, índices tipo IBOV): `acoes_yahoo.py`
  já aceitava `suffix=""`, só faltava a camada de API (`models/services/schemas/routers` de
  `us_stock`, 5 tabelas novas) — 5 endpoints novos sob `/v1/us-stocks/{ticker}/...`. IBOV
  (`^BVSP`) não ganhou endpoint próprio — passa pelos mesmos endpoints, mesma decisão que o
  `data-collector` do Anchor já tomava. **1.11.2** — indicadores imobiliários de REIT via SEC
  EDGAR (`fetch_reit_fundamentals` portado, endpoint `/v1/us-stocks/{ticker}/reit-fundamentals`):
  tabela `reit_fundamentals` é time-series (append-only por `reference_year`, não overwrite),
  reaproveitando o helper genérico de lista já existente (`get_or_refresh_list`) com o ano no
  lugar da data — resposta é a série completa, batendo com o jeito que o Rust do Anchor já lê
  essa tabela hoje (lista ordenada por `fetched_at`, não só a mais recente). **1.11.3** —
  resolução ticker→CNPJ de FII (`acoes_bolsai.fetch_fii_summary` + `cvm_fii.resolve_cnpj`
  portados, endpoint `GET /v1/fiis/resolve/{ticker}`, router separado do `{cnpj}`-prefixado
  existente por não ter colisão de rota). **Achado real, corrigido antes de fechar**: o arquivo
  `geral` da CVM devolve o CNPJ do fundo pontuado (18 caracteres), mas a coluna nova é
  `String(14)` (só dígitos) — sem normalizar, o insert quebrava com
  `StringDataRightTruncation` ao testar ao vivo contra HGLG11 real (que hoje responde como
  "PÁTRIA LOG", não mais "CSHG Logística" — fundo trocou de administrador/nome desde a
  implementação original do Anchor). Verificado ao vivo contra AAPL (5 endpoints 1.11.1),
  `^BVSP`/IBOV (quote + price-history, 2483 pregões), Realty Income e Simon Property (REIT,
  incluindo o fallback `NetIncomeLoss`→`ProfitLoss` da Simon Property) e HGLG11 (resolução real,
  cache confirmado na 2ª chamada). Suite completa **196/196** sem regressão. Fecha a Fase 1.11 —
  desbloqueia o resto da Fase 14.4 do Anchor (`main_us_stock`/`main_reit`/`main_etf_us`,
  benchmarks, `resolve_fii_cnpj`).

### Fase 2 — Engine Fiscal (SEFAZ)

Do blueprint original — NF-e/NFS-e via certificado digital A1, validação de schemas XML,
geração automática de DANFE. Sem desenho ainda; ver `ROADMAP.md`.

### Fase 3 — Meta Cloud API & Automação (WhatsApp)

Do blueprint original — WhatsApp Business API oficial (Meta Cloud API), disparo automático
pós-pagamento, abstração de tokens/webhooks/Message Templates. Sem desenho ainda.

### Fase 4 — Workspace Web App

Do blueprint original — painel gerenciado pro empreendedor não-técnico, modelo
pay-as-you-go, hub de comunicação (e-mail/WhatsApp), DRE simplificado, motor de automação
("Se X, então Y e Z"). Sem desenho ainda.
