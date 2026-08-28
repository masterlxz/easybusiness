## Fases Detalhadas

### Fase 1 — Super API Financeira + Super DB (MVP)

**Objetivo**: centralizar, num único serviço confiável, a coleta de dados financeiros que hoje
o Anchor faz de forma isolada (`data-collector/`), expondo tudo via uma API HTTP/JSON — ver
`CONTEXT.md` para o PRD completo e o catálogo de fontes herdado do Anchor.

**Etapas**:
- [x] 1.1 — Setup do repositório (Sessão 1: GitHub criado, `project/` criado com o blueprint incorporado)
- [x] 1.2 — Stack decidida (Sessão 2): Python + FastAPI, PostgreSQL, self-host via Docker Compose
- [x] 1.3 — Schema inicial via Alembic: `macro_series_monthly` (series_code, reference_month, value_pct, source, fetched_at) — `api/app/models/macro_series.py`
- [x] 1.4 — Primeira fonte portada (Sessão 2): BCB SGS (CDI e IPCA), reimplementada em `api/app/sources/bcb_sgs.py`, validada ao vivo contra a API real (481 pontos de CDI desde 1986, 559 de IPCA)
- [x] 1.5 — Contrato definido e validado: `GET /v1/macro-series/{series_code}` com auth por `X-API-Key`, cache-through com TTL configurável (`api/app/services/macro_series_service.py`)
- [~] 1.6 — Portar as fontes restantes do catálogo, uma a uma (7/11 portadas)
  - [x] Yahoo Finance (Sessão 3): cotação, técnicos (SMA/CAGR), dividendo médio 5a, histórico de preço, histórico de pagamentos — `api/app/sources/acoes_yahoo.py`, 5 endpoints sob `/v1/stocks/{ticker}/...`, validado ao vivo (PETR4/MGLU3)
  - [x] CVM DFP + FII (Sessão 4): ROE, payout médio 5a, 9 campos do DCF (empresas, por código CVM) + indicadores mensais e imóveis (FII, por CNPJ) — `api/app/sources/cvm_dfp.py`/`cvm_fii.py`, 5 endpoints sob `/v1/companies/{cvm_code}/...` e `/v1/fiis/{cnpj}/...`, validado ao vivo (VALE3/CD_CVM 4170, FII CNPJ 00332266000131)
  - [x] Cripto — CoinGecko + DefiLlama + alternative.me + ultrasound.money (Sessão 5): 4 indicadores de saúde do ETH (TVL trend, net issuance, fees vs emissão, NVT ratio) via catálogo parametrizado, Fear & Greed global, cotação/histórico de qualquer moeda por símbolo — `api/app/sources/cripto_*.py`, 4 endpoints sob `/v1/crypto/...`, validado ao vivo (indicadores reais do ETH, BTC quote+365 pontos de histórico)
  - [ ] bolsai (exige API key própria), B3 index stats, SEC EDGAR, metais Yahoo
- [ ] 1.7 — Anchor passa a consumir a Super API em vez de rodar `data-collector/main.py` localmente (migração do maior consumidor-alvo)
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
