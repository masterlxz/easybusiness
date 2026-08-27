## Decisões de Arquitetura em Aberto

| Decisão | Opções | Status |
|---|---|---|
| Linguagem/framework da Super API | Python (FastAPI, reaproveita o conhecimento do `data-collector` do Anchor) vs Node/TypeScript vs Rust | **Pendente** |
| Banco de dados (Super DB) | PostgreSQL vs SQLite (Anchor usa SQLite hoje, mas é single-consumer; Super DB precisa servir múltiplos consumidores concorrentes) | **Pendente — Postgres é o favorito**, dado o objetivo de servir múltiplos consumidores (SQLite não foi pensado pra concorrência de escrita) |
| Autenticação da API | API key simples (header) vs OAuth/JWT | **Pendente — API key é o favorito** pro MVP, mesmo padrão simples que o blueprint descreve pro modelo pay-as-you-go ("chamadas JSON diretas") |
| Hospedagem | Self-host (Docker, mesmo padrão do TruthID/Anchor) vs Cloud gerenciado | **Pendente** — provavelmente self-host no MVP (open-core: comunidade hospeda a própria instância); cloud gerenciado fica pra Fase 4 (Workspace) do blueprint |
| Cadência de coleta por fonte | Sob demanda (como o botão manual do Anchor) vs job agendado (cron) vs híbrido | **Pendente** — cada fonte do catálogo (`CONTEXT.md`) pode ter uma cadência diferente (câmbio muda todo dia, fundamentos de CVM mudam por trimestre) |
| Licença open-source | MIT (mesma do TruthID/Anchor) vs AGPL (mencionada no blueprint como opção pro open-core) | **Pendente** |

---

## Catálogo técnico das fontes

Ver tabela completa (fonte × domínio × observação) em `CONTEXT.md`, seção "Catálogo de Fontes
de Dados". Esta seção aqui é pra registrar, por fonte, decisões técnicas de implementação
conforme forem tomadas (biblioteca HTTP usada, estratégia de retry, TTL de cache) — vazia por
enquanto, projeto ainda não tem código.

---

## Débitos Técnicos de Arquitetura

Nenhum ainda — projeto em bootstrap (Sessão 1), sem código escrito.
