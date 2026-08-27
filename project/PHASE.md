## Fases Detalhadas

### Fase 1 — Super API Financeira + Super DB (MVP)

**Objetivo**: centralizar, num único serviço confiável, a coleta de dados financeiros que hoje
o Anchor faz de forma isolada (`data-collector/`), expondo tudo via uma API HTTP/JSON — ver
`CONTEXT.md` para o PRD completo e o catálogo de fontes herdado do Anchor.

**Etapas**:
- [x] 1.1 — Setup do repositório (Sessão 1: GitHub criado, `project/` criado com o blueprint incorporado)
- [ ] 1.2 — Decidir a stack (linguagem/framework da API, banco de dados) — ver `ARCHITECTURE.md`
- [ ] 1.3 — Desenhar o schema do Super DB (normalizar os ~12 formatos de fonte diferentes numa representação comum por domínio: cotação, fundamento, série macro, índice cripto)
- [ ] 1.4 — Portar a primeira fonte de dado (candidata: BCB SGS ou Yahoo Finance — nenhuma exige API key própria, mais simples pra validar o pipeline ponta a ponta)
- [ ] 1.5 — Definir o contrato da API pública (rotas, autenticação por API key, formato de resposta)
- [ ] 1.6 — Portar as fontes restantes do catálogo, uma a uma
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
