# Pendências do Projeto

> Arquivo central de pendências — **resolvidas e não resolvidas**.
> Toda pendência encontrada em qualquer arquivo do projeto deve ser registrada aqui com um ID único.
> Ao resolver uma, marcar como `✅ Resolvida` com a sessão em que foi corrigida.
>
> Última atualização: 2026-08-28 (Sessão 7 — Fase 1.7, migração híbrida do Anchor)

## Não Resolvidas

### P1 — `GET /v1/fiis/{cnpj}/properties` não distingue CNPJ desconhecido de FII sem imóvel

`data: []` é a resposta pra ambos os casos (CNPJ inexistente na CVM, e CNPJ válido de um FII de
papel/recebíveis que legitimamente não tem imóvel nenhum) — diferente de `/monthly-indicators`,
que devolve 404 pra CNPJ desconhecido. Achado na Sessão 7 ao planejar a migração do Anchor:
`fetch_property_data` (`api/app/sources/cvm_fii.py`) devolve lista vazia nos dois casos, sem
jeito de diferenciar com o dado que a própria CVM fornece — unificar o comportamento com
`/monthly-indicators` corre o risco real de classificar um FII de papel válido como "não
encontrado" na primeira chamada. Decisão consciente (confirmada com o dono do projeto): não
mexer por enquanto — consumidores (o cliente HTTP do Anchor, `data-collector/super_api_client.py`)
devem tratar `data: []` como "sem imóvel", nunca como erro.

## Resolvidas

## Resolvidas

Nenhuma ainda.
