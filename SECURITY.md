# Política de segurança

## Como reportar uma vulnerabilidade

Se você encontrou uma falha de segurança, **não abra uma issue pública**. Use a opção **"Report a vulnerability"** na aba **Security** deste repositório, ou escreva para sabrinacsilva09@gmail.com com o assunto "Segurança Pista".

Inclua o que você encontrou, como reproduzir e o impacto que imagina. Respondo em até 7 dias.

## Versões com suporte

| Versão | Recebe correções de segurança |
|---|---|
| Mais recente | ✅ |
| Anteriores | ❌ |

## O que o projeto protege

| O que proteger | De quê | Como |
|---|---|---|
| A chave da API do Gemini | Vazamento e uso indevido | Só existe nos segredos do servidor; nunca no front-end nem no Git; varredura de segredos ativada |
| A resposta da questão | Ser entregue antes da hora | Gabarito nunca enviado ao navegador antes da explicação; guardrail de saída; testes de vazamento |
| O comportamento do tutor | Manipulação do prompt ("ignore as instruções") | Guardrail de entrada, instruções fixas no servidor, testes automáticos de manipulação |
| A privacidade dos alunos | Coleta e exposição de dados pessoais | Conta opcional só com apelido e senha, sessão anônima para quem não tem conta, logs sem texto das mensagens |
| As contas | Senha adivinhada ou vazada | Senhas e códigos de recuperação com scrypt e sal, tokens guardados só como hash, limite de 5 tentativas de login a cada 15 minutos, mesma resposta para apelido inexistente e senha errada |
| O orçamento | Abuso que esgota o plano gratuito | Limite de requisições por sessão e por IP, limite diário de chamadas à IA |
| O banco de dados | Acesso indevido e perda de dados | Usuário com privilégio mínimo, consultas parametrizadas pelo ORM, backup testado |
| A cadeia de dependências | Pacotes com falhas conhecidas | Dependabot, `pip-audit` e `npm audit` no CI, CodeQL |

## Privacidade e LGPD

- O Pista não pede nome, e-mail, CPF, idade nem qualquer dado pessoal.
- A conta é opcional. Ela guarda só o apelido escolhido, o hash da senha, a meta de estudo, as habilidades em foco, o tema e o histórico de questões resolvidas.
- A tela de cadastro orienta a não usar o próprio nome como apelido.
- A recuperação de conta é feita com um código mostrado uma única vez no cadastro, e não por e-mail, justamente para não coletar e-mail.
- O aluno pode apagar a conta a qualquer momento, e isso apaga também todo o histórico (direito à eliminação, LGPD art. 18).
- O identificador da sessão é aleatório (UUID) e gerado pelo servidor.
- O endereço IP é usado só para limitar abusos e não é salvo no banco.
- As interações são apagadas após 30 dias. Só ficam números agregados, sem ligação com nenhuma pessoa.
- Muitos estudantes do ENEM são menores de idade, por isso o projeto foi desenhado para não coletar dados pessoais desde o início (LGPD, art. 14).
- **Plano gratuito do Gemini:** nesse plano, o Google pode usar o conteúdo enviado para melhorar os produtos dele. Por isso a interface vai avisar para não digitar dados pessoais nas mensagens, e o tutor não pede nem comenta dados pessoais. Se o projeto passar a ter muitos usuários, a migração para o plano pago (em que os dados não são usados) entra no planejamento.
- Mensagens bloqueadas pelo guardrail de entrada não são guardadas, nem no histórico da sessão.
- No navegador, o token da conta fica no `localStorage` e vence em 30 dias. Isso exige proteger o site contra XSS: o Markdown é renderizado sem HTML bruto, e a política de segurança de conteúdo (CSP) entra na Fase 9.

## Controles técnicos

- HTTPS em todos os serviços
- CORS liberado apenas para o domínio do front-end
- Cabeçalhos de segurança: Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options
- Validação de todas as entradas com Pydantic
- Configurações de segurança de conteúdo do Gemini ativadas
- `main` protegida: mudanças só entram por pull request com o CI verde

O plano de implementação destes controles está na Fase 9 do [cronograma](docs/CRONOGRAMA.md).
