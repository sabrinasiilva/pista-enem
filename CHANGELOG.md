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
- Tutor no terminal (`python -m app.tutor.terminal`) e script da rodada contra vazamento (`evals/vazamento.py`)
