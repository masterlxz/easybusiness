## Roadmap de Evoluções Planejadas

### Visão completa do blueprint original (registrado na Sessão 1)

O blueprint (`blueprint_plataforma_opensource.md.docx`, lido e removido do repo na Sessão 1)
descrevia 3 camadas: (A) Ponte para Desenvolvedores (APIs & SDKs — pagamentos unificados,
fiscal, WhatsApp, finanças/Open Finance), (B) Workspace do Empreendedor (web app), (C) Módulo
B3 & Mercado Financeiro. A decisão desta sessão foi começar pela fatia financeira de (A) e (C)
combinadas — a Finance API — por já ter um consumidor real pronto (o Anchor) e por ser a base de
que as outras camadas dependem (ex: o DRE do Workspace precisa de dados financeiros
centralizados; a conciliação de caixa corporativo do módulo B3 também).

### Modelo Open-Core & Monetização (do blueprint original)

| Componente | Versão Open-Source (Community) | Versão Cloud Hospedada (SaaS) |
|---|---|---|
| Público-Alvo | Desenvolvedores, Engenheiros de Software, DevOps | Empreendedores, Startups, Pequenos Lojistas |
| Hospedagem | Infraestrutura própria (VPS, Docker, PostgreSQL) | Nuvem nativa gerenciada (Zero setup) |
| Custo de Infra | Pago pelo próprio dev | Incluído na bilhetagem por uso |
| Modelo financeiro | Gratuito / Licença permissiva (MIT/AGPL) | Pay-as-you-go (margem sobre micro-transações) |

Monetização por consumo, exemplos do blueprint original: R$ 0,15 por nota fiscal emitida
(Fase 2), repasse do custo Meta + margem por mensagem enviada (Fase 3), micro-taxa sobre
webhooks e baixa automática de boletos/Pix. Nenhum desses se aplica à Fase 1 (dados
financeiros) ainda — como cobrar pelo uso da Finance API (por chamada? por volume de dado? tier
gratuito generoso pro open-source, cobrança só na versão cloud?) fica em aberto até a API
existir.

### Migração do Anchor pra Finance API — ideia central desta sessão (Sessão 1)

O Anchor (`../../anchor`) tinha `data-collector/` — 12 clientes Python independentes (ver
catálogo completo em `CONTEXT.md`), cada um escrevendo direto no SQLite local do app, disparado
como subprocess sob demanda pelo botão da UI. Isso funcionava, mas: (1) não tinha cache/reuso
entre os apps do Anchor (desktop, mobile ainda não sincroniza, futuro cross-device via TruthID);
(2) qualquer outro projeto financeiro do mesmo autor reimplementaria tudo de novo; (3) sem
camada de confiabilidade compartilhada (retry, fallback, normalização) além do que cada script
fazia sozinho. **Migrado na Sessão 7 (Fase 1.7, ver `PHASE.md`)** — híbrido, não 100%: o que a
Finance API cobre virou HTTP; o resto (ver "Fase 1.6b" abaixo) continua local.

### Fase 1.6b — fechar a lacuna deixada pela migração híbrida (candidato futuro, não desenhado)

A 1.7 (Sessão 7) revelou que a Finance API não cobre tudo que o Anchor precisa — 4 capacidades
continuam rodando local no `data-collector/` dele por falta de endpoint equivalente:
- Cotação/técnicos/dividendos/histórico de preço pra ticker **sem sufixo `.SA`** (ação
  americana comum, ETF US, REIT) — `/v1/stocks/...` hoje só serve B3.
- Indicadores imobiliários de REIT (FFO/AFFO não existem como tag XBRL, mas receita/patrimônio/
  LPA/lucro dão pra automatizar, mesmo espírito de `/v1/companies/...`).
- IBOV (`^BVSP`) — mesmo problema do primeiro item, é Yahoo sem sufixo.
- Resolução ticker→CNPJ de FII (`resolve_cnpj`) — cruza bolsai + nome oficial da CVM, nunca
  desenhada como endpoint (decisão da Sessão 4 do Anchor).

Nenhuma dessas foi sequenciada — fica registrado aqui só pra não se perder, caso algum dia outro
consumidor da Finance API precise do mesmo dado e justifique o esforço de portar.

### Ideias de Expansão (Brainstorm — sem `/plan`)

- Open Finance de verdade (extratos bancários via Open Finance Brasil) — mencionado no
  blueprint original, não pesquisado ainda.
- Unified Payment API (Asaas, Mercado Pago, Pagar.me, Stripe) — camada (A) do blueprint, ainda
  não sequenciada em relação às Fases 2-4 de `PHASE.md`.
- Expor o catálogo de fontes como um SDK (Python/Node), mesmo padrão que TruthID e Anchor usam
  pros próprios integradores.
