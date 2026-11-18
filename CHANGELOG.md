# Changelog

Todas as mudanças importantes do projeto ficam registradas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e o projeto usa [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- README com o problema, a ideia, a arquitetura e as metas de avaliação
- Cronograma completo, da preparação ao lançamento
- Documentação de arquitetura, avaliação e política de segurança
- Licença MIT
- Banco inicial de 60 questões de Matemática do ENEM (2022 a 2024), transcritas da prova oficial, com gabarito e habilidade conferidos nos microdados do Inep, resolução e engano provável de cada alternativa errada
- Scripts de download, extração, conferência e seleção das questões, com testes
- Matriz de referência de Matemática (7 competências e 30 habilidades) em JSON
- Documentação dos dados: fontes, termos de uso e problemas encontrados no conjunto aberto
- CI que valida os dados a cada pull request
- Núcleo do tutor: máquina de estados da sessão, verificação da resposta pelo código e prompts versionados (`tutor_v1`)
- Guardrail de saída contra vazamento da resposta e guardrail de entrada contra manipulação do prompt
- Integração com o Gemini com tempo limite, novas tentativas, modelo reserva e plano B
- Tutor no terminal (`python -m app.tutor.terminal`)
- Avaliação: 30 casos fixos e `evals/rodar.py`, que mede vazamento, manipulação, pistas em pergunta e latência, contra a API no ar ou localmente
- API FastAPI: questões sem o gabarito, sessões anônimas, respostas, conversa em streaming (SSE) e explicação
- Erros padronizados, validação com Pydantic, CORS configurável e documentação no Swagger
- Imagem Docker sem privilégios, construída e testada no CI
- Front-end em React, TypeScript e Tailwind: página inicial, página da questão com fórmulas em KaTeX, níveis de pista, conversa em streaming e explicação com confirmação
- Testes de componentes com Vitest e Testing Library, e CI do front-end com checagem de dependências
- Novo visual: exemplo de pista na página inicial, questões em abas por ano, página da questão em duas colunas no computador e ícone do site
- Contas opcionais só com apelido e senha, com código de recuperação, troca de senha e exclusão da conta e do histórico
- Banco de dados com SQLAlchemy e migrações do Alembic (SQLite local, pronto para PostgreSQL)
- Progresso: meta da semana, sequência de dias, desempenho por habilidade e questões para revisar
- Recomendações para o modo foco
- Site: menu lateral, criar conta em três passos, entrar, recuperar a conta, perfil, meu progresso, revisar erros, modo foco com cronômetro e resumo
- Tema claro, escuro e automático
- Hospedagem: `render.yaml` para a API no Render, driver do PostgreSQL (Neon), publicação do site no GitHub Pages e aviso de "servidor acordando"

### Alterado
- Tutor mais rápido: Gemini 3.5 Flash-Lite com raciocínio mínimo como modelo principal (3.8 Flash como reserva), limite de espera de 12 s e respostas de até 60 palavras, sem cumprimentos
- Indicador "o tutor está pensando" enquanto a pista é gerada, e tempo de cada chamada à IA no log
- Limites de uso por IP, por sessão e cota diária do Gemini, com o tutor em modo básico quando a cota acaba
- Migrações podem usar um usuário do banco diferente (`MIGRACOES_DATABASE_URL`), para a API rodar com um usuário de permissão mínima

### Corrigido
- O limite de tentativas de login usava o IP do proxy do Render: cinco erros de qualquer pessoa bloqueavam o login de todos. Agora usa o IP real do aluno
- Prévia das questões mostrava LaTeX e pedaços de tabela; agora é texto puro
- Pontuação logo depois de uma fórmula ia sozinha para a linha de baixo
