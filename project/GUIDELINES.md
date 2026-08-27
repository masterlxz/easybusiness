# Diretriz de código (IMPORTANTE — sempre seguir)

**Todo código novo deve ser escrito em inglês — sem exceção** (mesma convenção usada nos
outros dois projetos públicos do autor, TruthID e Anchor):
- Strings visíveis (respostas de API, mensagens de erro, documentação da API pública): inglês
- Nomes de variáveis, funções, classes, arquivos, rotas: inglês
- Comentários no código: podem ficar em português (não são visíveis a quem consome a API)
- Documentação em `project/`, README e mensagens de commit: português (consistente com
  TruthID/Anchor)

**Segredos**: repo público desde o primeiro commit — nunca commitar chave de API, connection
string ou credencial. Usar variável de ambiente / `.env` (gitignored), com um `.env.example`
documentando as chaves esperadas (mesmo padrão do `anchor/data-collector/.env.example`).

**Reuso consciente do Anchor**: ao portar uma fonte de dado de `anchor/data-collector/sources/`
pra cá (ver catálogo em `CONTEXT.md`), não copiar o arquivo Python 1:1 — reimplementar na stack
escolhida (ver `ARCHITECTURE.md`), usando o cliente existente como referência de comportamento
(quais campos a fonte retorna, limites de taxa conhecidos, formato de data/número).

**Confiabilidade antes de cobertura**: o objetivo declarado do projeto é reunir o máximo de
informação possível deixando-a "o mais confiável e simples possível". Ao integrar uma fonte
nova, preferir poucas fontes bem tratadas (retry, timeout, normalização, teste contra a API
real) a muitas fontes frágeis adicionadas às pressas.
