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
- [ ] 1.8 — Documentação pública da API (README + docs, mesmo padrão do TruthID `docs/`)

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
