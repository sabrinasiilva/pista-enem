# Cronograma

Plano completo do Pista, da preparação ao lançamento. Cada fase tem objetivo, tarefas, entregável e critério de pronto.

## Ritmo considerado

| Período | Horas por semana | Contexto |
|---|---|---|
| 18/11 a 06/12/2026 | 12 h | Estágio de dia, faculdade à noite: duas noites de 2 h e o fim de semana |
| 07/12/2026 a 03/01/2027 | 4 h | Trabalho temporário (15h às 23h) e festas de fim de ano |
| 04/01 a 07/02/2027 | 12 h | Férias da faculdade |

Total estimado: **cerca de 110 horas**.

## Visão geral

| Fase | Tema | Período | Horas | Versão |
|---|---|---|---|---|
| 0 | Preparação do projeto | 18 a 19/11 | 4 | v0.1.0 |
| 1 | Dados do MVP | 20 a 22/11 | 8 | v0.1.0 |
| 2 | Núcleo do tutor e guardrails | 23 a 27/11 | 10 | v0.1.0 |
| 3 | API mínima | 28 a 29/11 | 6 | v0.1.0 |
| 4 | Front-end mínimo | 30/11 a 03/12 | 8 | v0.1.0 |
| 5 | Infraestrutura, banco e deploy do MVP | 04 a 05/12 | 6 | v0.1.0 |
| 6 | Avaliação inicial e segurança essencial | 05 a 06/12 | 4 | v0.1.0 |
| 7 | RAG e ampliação dos dados | 07/12 a 03/01 | 16 | v0.2.0 |
| 8 | Avaliação completa | 04 a 12/01 | 12 | v1.0.0 |
| 9 | Segurança e privacidade completas | 13 a 19/01 | 10 | v1.0.0 |
| 10 | Qualidade, acessibilidade e questões com imagem | 20 a 26/01 | 12 | v1.0.0 |
| 11 | Observabilidade e release v1.0.0 | 27 a 31/01 | 6 | v1.0.0 |
| 12 | Lançamento e divulgação | 01 a 07/02 | 4 | — |

---

## Fase 0 · Preparação do projeto
**Período:** 18 a 19/11/2026 · **Horas:** 4

**Objetivo:** deixar o repositório, as regras de trabalho e as ferramentas prontas antes de escrever código.

- [x] README, cronograma, arquitetura e política de segurança publicados
- [x] Licença MIT, `.gitignore` e `CHANGELOG.md`
- [x] Marcos (milestones) v0.1.0, v0.2.0 e v1.0.0 e issues por fase no GitHub
- [x] Quadro Kanban no GitHub Projects (A fazer, Fazendo, Revisão, Feito)
- [x] Padrão de commits definido (Conventional Commits, em português)
- [x] Fluxo de branches: `main` protegida, trabalho em `feat/...` e `fix/...`, entrada via pull request
- [x] Alertas do Dependabot e varredura de segredos ativados
- [ ] Chave da API do Gemini criada e guardada fora do repositório
- [ ] Contas criadas: Neon (banco) e Render (API)

**Entregável:** repositório organizado, com documentação e quadro de tarefas.
**Pronto quando:** qualquer pessoa entende o projeto só lendo o README, e toda tarefa do cronograma existe como issue.

## Fase 1 · Dados do MVP
**Período:** 20 a 22/11/2026 · **Horas:** 8

**Objetivo:** ter um banco inicial de questões confiável.

- [x] Ler os termos de uso das provas do Inep e registrar a conclusão em `docs/DADOS.md`
- [x] Pesquisar conjuntos de dados abertos de questões do ENEM e comparar com os PDFs oficiais
- [x] Baixar provas e gabaritos de Matemática de 2022 a 2024 (2025 passou para a Fase 7: o conjunto aberto vai só até 2024)
- [x] Script `data/extrair.py` que transforma as questões em JSON (enunciado, alternativas, gabarito, ano, número, habilidade)
- [x] Revisão manual das questões extraídas (feita em 100% das candidatas, não só 20%, porque o conjunto aberto tinha erros)
- [x] Selecionar 60 questões de Matemática sem imagem para o MVP
- [x] Para cada alternativa errada, registrar o engano mais provável (ex.: "trocou o sinal")
- [x] Baixar a matriz de referência do ENEM e mapear as habilidades de Matemática (H1 a H30)
- [x] Testes do script de extração (formato, gabarito válido, cinco alternativas)

**Entregável:** `data/questoes-mvp.json` com 60 questões revisadas e anotadas.
**Pronto quando:** 100% das questões têm gabarito conferido com o oficial e fonte registrada.

## Fase 2 · Núcleo do tutor e guardrails
**Período:** 23 a 27/11/2026 · **Horas:** 10

**Objetivo:** o coração do projeto: conduzir o raciocínio sem entregar a resposta.

- [x] Máquina de estados da sessão: `respondendo` → `pista_1` → `pista_2` → `explicacao` → `concluida`
- [x] Verificação da resposta feita no código, comparando com o gabarito (a IA não decide se o aluno acertou)
- [x] Prompts versionados em `prompts/` (ex.: `tutor_v1.md`), com regras para cada nível
- [x] Diagnóstico do engano a partir da alternativa marcada e da anotação da Fase 1
- [x] Guardrail de saída: antes do nível 3, detectar se a resposta revela a alternativa correta e, se revelar, gerar outra
- [x] Guardrail de entrada: limite de tamanho e detecção de tentativas de manipulação ("ignore as instruções")
- [x] Integração com o Gemini com tempo limite, novas tentativas e mensagem padrão quando a IA falhar (o plano B que já usei no CO2Bank)
- [x] Testes unitários com a IA simulada (mock): transições de estado, guardrails e plano B

**Entregável:** módulo `api/app/tutor` funcionando no terminal com uma questão real.
**Pronto quando:** os testes passam e nenhuma das 60 questões vaza a resposta antes do nível 3 numa rodada manual (`evals/vazamento.py`, com a IA de verdade).

## Fase 3 · API mínima
**Período:** 28 a 29/11/2026 · **Horas:** 6

**Objetivo:** expor o tutor para o front-end.

- [x] Projeto FastAPI com configurações por variável de ambiente
- [x] `GET /questoes` (lista filtrada por área e ano) e `GET /questoes/{id}`
- [x] `POST /sessoes` (sessão anônima) e `POST /sessoes/{id}/respostas`
- [x] `POST /sessoes/{id}/mensagens` com resposta em streaming
- [x] `GET /health`
- [x] Validação de entrada e saída com Pydantic e erros padronizados
- [x] Documentação automática (Swagger) revisada
- [x] Testes de integração das rotas

**Entregável:** API rodando localmente com Docker (a imagem é construída e testada no CI a cada PR).
**Pronto quando:** dá para resolver uma questão inteira só pelo Swagger.

## Fase 4 · Front-end mínimo
**Período:** 30/11 a 03/12/2026 · **Horas:** 8

**Objetivo:** uma interface simples e agradável para o aluno.

- [x] Projeto React + TypeScript + Tailwind com Vite
- [x] Tela inicial: o que é o Pista e botão para começar
- [x] Tela da questão: enunciado, fórmulas com KaTeX, alternativas e fonte (Inep, ano, número)
- [x] Conversa com o tutor, mostrando o nível da pista atual e o texto chegando em streaming
- [x] Botão "quero a explicação completa", com confirmação
- [x] Estados de carregamento, erro e IA indisponível
- [x] Layout responsivo (celular primeiro)
- [x] Testes de componentes com Vitest e Testing Library

**Entregável:** front-end consumindo a API local.
**Pronto quando:** uma pessoa que nunca viu o projeto resolve uma questão sem ajuda.

## Fase 4.5 · Contas, foco e tema (pedida em 17/11/2026)
**Período:** 17/11/2026 · fora do plano original

**Objetivo:** guardar o progresso de quem quiser, sem coletar dados pessoais, e dar formas de estudar com foco.

- [x] Banco de dados com SQLAlchemy e migrações do Alembic (SQLite local, pronto para o PostgreSQL da Fase 5)
- [x] Conta opcional só com apelido e senha, com código de recuperação no lugar do e-mail
- [x] Cadastro em três passos: acesso, meta e áreas de foco, código de recuperação
- [x] Entrar, sair, recuperar a conta, trocar a senha e apagar a conta com todo o histórico
- [x] Segurança das contas: scrypt, tokens guardados só como hash, limite de tentativas de login
- [x] Meta semanal, sequência de dias e desempenho por assunto ("Meu progresso")
- [x] Lista de questões para revisar ("Revisar erros")
- [x] Modo foco: quantidade, tempo e áreas, com fila recomendada, cronômetro e resumo
- [x] Menu lateral no computador e menu que abre no celular
- [x] Tema claro, escuro e automático, salvo na conta
- [x] Testes da API e do front-end para tudo isso

**Entregável:** contas, progresso, revisão, modo foco e tema funcionando no site.
**Pronto quando:** um aluno cria a conta, resolve questões, vê o progresso e refaz os erros, no celular e no computador.

## Fase 5 · Infraestrutura, banco e deploy do MVP
**Período:** 04 a 05/12/2026 · **Horas:** 6

**Objetivo:** colocar o MVP no ar.

- [ ] Banco PostgreSQL no Neon, com usuário de aplicação de privilégio mínimo
- [ ] Migrações com Alembic (tabelas de questões, alternativas, sessões e interações)
- [ ] Script de carga das 60 questões no banco
- [x] `Dockerfile` da API e configuração do Render (`render.yaml`), com a chave do Gemini nas variáveis do Render
- [ ] Serviço criado no Render e no ar
- [x] Publicação do front-end no GitHub Pages (`publicar-site.yml`)
- [ ] Site no ar, apontando para a API do Render
- [ ] CORS liberado só para o domínio do front-end
- [ ] Workflow de CI: lint, checagem de tipos e testes a cada push e pull request
- [ ] Workflow de CD: deploy do front e da API quando a `main` muda
- [ ] Exigir o CI verde para fazer merge na `main` (regra de proteção da branch)
- [ ] Monitor de disponibilidade no UptimeRobot

**Entregável:** Pista acessível por um link público.
**Pronto quando:** o fluxo completo funciona no ar, e um push na `main` atualiza tudo sem passo manual.

## Fase 6 · Avaliação inicial e segurança essencial
**Período:** 05 a 06/12/2026 · **Horas:** 4

**Objetivo:** medir antes de divulgar.

- [ ] Conjunto de avaliação com 30 casos (respostas erradas reais e tentativas de manipulação)
- [ ] Script `evals/rodar.py` que mede vazamento de resposta e resistência a manipulação
- [ ] Limite de requisições por sessão e por IP
- [ ] Limite diário de chamadas à IA (proteção de custo)
- [ ] Primeiros resultados em `docs/AVALIACAO.md`
- [ ] **Release v0.1.0:** tag, notas da versão e `CHANGELOG.md` atualizado

**Entregável:** v0.1.0 publicada, com métricas.
**Pronto quando:** vazamento de 0% no conjunto de avaliação e release criada no GitHub.

## Fase 7 · RAG e ampliação dos dados
**Período:** 07/12/2026 a 03/01/2027 · **Horas:** 16 (ritmo leve)

**Objetivo:** pistas apoiadas na matriz oficial e mais questões.

- [ ] Extensão pgvector ativada no Neon
- [ ] Embeddings das habilidades da matriz de referência e das questões
- [ ] Busca por habilidades relacionadas a cada questão, usada para montar as pistas
- [ ] Sugestão de "questão parecida para praticar" ao final da sessão
- [ ] Avaliação da busca (Recall@5) com 40 questões anotadas à mão
- [ ] Questões de Matemática de 2025 transcritas da prova oficial, com o mesmo processo de revisão
- [ ] Questões de Ciências da Natureza sem imagem (meta: mais 60)
- [ ] Prompt `tutor_v2` comparado com o `tutor_v1` no conjunto de avaliação
- [ ] **Release v0.2.0**

**Entregável:** v0.2.0 com RAG e duas áreas do conhecimento.
**Pronto quando:** Recall@5 ≥ 90% e nenhuma métrica da v0.1.0 piorou.

## Fase 8 · Avaliação completa
**Período:** 04 a 12/01/2027 · **Horas:** 12

**Objetivo:** provar a qualidade do tutor com números.

- [ ] Ampliar o conjunto de avaliação para 120 casos
- [ ] Métricas de aderência socrática e de diagnóstico do engano
- [ ] Avaliação automática com um segundo modelo como juiz, com critérios escritos
- [ ] Revisão humana de uma amostra para conferir o juiz automático
- [ ] Workflow manual (`workflow_dispatch`) que roda a avaliação e salva o relatório
- [ ] Comparação entre versões de prompt documentada em `docs/AVALIACAO.md`
- [ ] Teste com 5 estudantes reais e registro dos aprendizados (sem dados pessoais)

**Entregável:** relatório de avaliação publicado no README.
**Pronto quando:** todas as metas da tabela de avaliação estão medidas e documentadas.

## Fase 9 · Segurança e privacidade completas
**Período:** 13 a 19/01/2027 · **Horas:** 10

**Objetivo:** tratar segurança como parte do produto.

- [ ] Modelo de ameaças documentado em `SECURITY.md` (o que proteger, de quem e como)
- [ ] Testes automáticos de manipulação de prompt (pelo menos 30 variações)
- [ ] Cabeçalhos de segurança (CSP, HSTS, X-Content-Type-Options)
- [ ] Logs sem dados pessoais e sem o texto completo das mensagens
- [ ] Retenção: interações apagadas após 30 dias, só métricas agregadas ficam
- [ ] Aviso de privacidade no site, em linguagem simples
- [ ] Análise de código com CodeQL e auditoria de dependências (`pip-audit`, `npm audit`) no CI
- [ ] Configurações de segurança do Gemini revisadas (conteúdo impróprio bloqueado)
- [ ] Backup do banco testado (restaurar num banco vazio)

**Entregável:** `SECURITY.md` completo e CI com checagens de segurança.
**Pronto quando:** nenhum alerta crítico aberto e todos os testes de manipulação falham para o atacante.

## Fase 10 · Qualidade, acessibilidade e questões com imagem
**Período:** 20 a 26/01/2027 · **Horas:** 12

**Objetivo:** deixar o produto acessível e mais completo.

- [ ] Acessibilidade WCAG AA: teclado, leitor de tela, contraste e foco visível
- [ ] Fórmulas acessíveis para leitores de tela
- [ ] Questões com imagem, usando a leitura de imagens do Gemini
- [ ] Testes de ponta a ponta com Playwright (fluxo completo no celular e no computador)
- [x] Tema claro e escuro (feito na Fase 4.5)
- [ ] Revisão de desempenho do front-end (Lighthouse ≥ 90)

**Entregável:** front-end acessível e questões com imagem disponíveis.
**Pronto quando:** Lighthouse ≥ 90 em acessibilidade e desempenho, e testes de ponta a ponta passando no CI.

## Fase 11 · Observabilidade e release v1.0.0
**Período:** 27 a 31/01/2027 · **Horas:** 6

**Objetivo:** saber o que acontece em produção e fechar a primeira versão estável.

- [ ] Logs estruturados com identificador de requisição
- [ ] Métricas: latência p95, taxa de erro, tokens por sessão e uso por área
- [ ] Alerta quando a taxa de erro ou o custo diário passarem do limite
- [ ] README final com GIF de demonstração, resultados da avaliação e instruções completas
- [ ] Versão do README em inglês
- [ ] **Release v1.0.0**

**Entregável:** v1.0.0 estável e documentada.
**Pronto quando:** todas as caixas deste cronograma estão marcadas.

## Fase 12 · Lançamento e divulgação
**Período:** 01 a 07/02/2027 · **Horas:** 4

- [ ] Vídeo curto de demonstração
- [ ] Estudo de caso no portfólio, no mesmo formato do CO2Bank
- [ ] Post no LinkedIn contando o problema, o diferencial e os números da avaliação
- [ ] Projeto fixado no perfil do GitHub e citado no currículo

---

## Versionamento

- **Código:** [Versionamento Semântico](https://semver.org/lang/pt-BR/). `0.x` enquanto o projeto muda rápido, `1.0.0` na primeira versão estável.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em português (ex.: `feat: pista de nível 2`).
- **Branches:** `main` sempre publicável. Trabalho em `feat/...`, `fix/...` e `docs/...`, entrando por pull request com o CI verde.
- **Banco:** toda mudança de tabela vira uma migração do Alembic.
- **Prompts:** cada prompt tem versão (`tutor_v1`, `tutor_v2`), e a troca de versão só acontece se a avaliação não piorar.
- **Histórico:** `CHANGELOG.md` no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/) e uma release no GitHub para cada versão.

## Riscos e como lidar

| Risco | Impacto | O que fazer |
|---|---|---|
| Extração dos PDFs do Inep com erros (fórmulas, tabelas) | Questões erradas no tutor | Revisão manual, começar só com questões sem imagem, testes do script |
| A IA entrega a resposta sem querer | Perde o propósito do produto | Guardrail de saída, conjunto de avaliação, prompts versionados |
| Limites do plano gratuito do Gemini ou da hospedagem | Site fora do ar ou lento | Limite diário de chamadas, plano B com mensagem padrão, conferir os limites atuais de cada serviço |
| Termos de uso das questões do Inep | Problema legal ao publicar dados | Verificar na Fase 1, sempre citar a fonte, não redistribuir os PDFs |
| Pouco tempo em dezembro | Atraso da v0.2.0 | Ritmo leve já previsto; o MVP fica pronto antes |
| Dados de menores de idade | Risco de privacidade | Sem cadastro, sem dados pessoais, retenção de 30 dias |

## Definição de pronto (vale para toda tarefa)

- Código revisado em pull request, com CI verde
- Testes escritos para o comportamento novo
- Documentação atualizada quando a mudança afeta quem usa ou quem desenvolve
- Nenhum segredo ou dado pessoal no código ou nos logs
