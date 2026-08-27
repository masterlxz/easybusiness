# O que é o EasyBusiness

EasyBusiness é uma plataforma open-source de automação, finanças e gestão para o
empreendedor brasileiro. A visão completa (3 camadas: APIs/SDKs, Workspace web, módulo B3)
vem do blueprint original do projeto (`blueprint_plataforma_opensource.md.docx`, lido na
Sessão 1 e removido do repo depois de incorporado à documentação — ver `CONTEXT.md` e
`ROADMAP.md` para o conteúdo completo).

**MVP atual (decidido na Sessão 1)**: em vez de atacar as 3 camadas do blueprint de uma vez, o
ponto de partida é a **Super API financeira**, que alimenta um **Super Banco de Dados**
centralizado. A ideia nasce de um problema concreto: o projeto irmão
[Anchor](../../anchor) já resolve boa parte da coleta de dados financeiros (cotações B3,
cripto, macro, fundamentos) espalhada em ~12 scripts Python independentes, cada um falando com
uma fonte diferente e escrevendo direto no SQLite local do Anchor — funciona, mas fica preso a
um único consumidor e sem camada de confiabilidade compartilhada. O EasyBusiness deve virar
essa coleta um serviço único, confiável e documentado, exposto via API — que o próprio Anchor
passa a consumir (em vez de rodar o coletor localmente), e que qualquer outro projeto (ou
usuário externo, no modelo pay-as-you-go do blueprint) também pode consumir.

Stack: **ainda não decidida** — ver `ARCHITECTURE.md`, seção "Decisões de Arquitetura em Aberto".

---

# Status Geral

```
Fase 1 — Super API Financeira + Super DB (MVP)   [ ] Não iniciada
Fase 2 — Engine Fiscal (SEFAZ)                    [ ] Não iniciada
Fase 3 — Meta Cloud API & Automação (WhatsApp)    [ ] Não iniciada
Fase 4 — Workspace Web App                        [ ] Não iniciada
```

---

# Checklist antes do próximo release

Projeto em fase de bootstrap — ainda não há código (Fase 1, etapa 1.1, decidir a stack, é o
próximo passo). Esta seção existe para manter o padrão dos outros projetos do autor
(`truthid/project/OVERVIEW.md`, `anchor/project/OVERVIEW.md`) e será preenchida quando a
Fase 1 tiver algo rodando de ponta a ponta.
