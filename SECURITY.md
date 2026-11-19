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
| O orçamento | Abuso que esgota o plano gratuito | 40 ações com IA a cada 10 minutos por IP, 40 por sessão, 30 sessões a cada 10 minutos por IP e 1 500 chamadas ao Gemini por dia. Ao passar da cota diária, o tutor segue no modo básico (sem erro) e o monitor manda e-mail |
| O banco de dados | Acesso indevido e perda de dados | Usuário com privilégio mínimo, consultas parametrizadas pelo ORM, backup testado |
| A cadeia de dependências | Pacotes com falhas conhecidas | Dependabot, `pip-audit` e `npm audit` no CI, CodeQL |

## Modelo de ameaças

**Quem pode atacar e o que quer:**

| Quem | O que quer | Por onde | O que segura |
|---|---|---|---|
| Aluno curioso | A resposta sem pensar | Mensagens na conversa ("ignore as instruções", "sou a professora") | Guardrails de entrada e saída, gabarito só no servidor, juiz automático na avaliação |
| Bot ou script | Gastar a cota do Gemini ou derrubar a API | Muitas requisições | Limites por IP e por sessão, cota diária com plano B, tamanho máximo da mensagem |
| Alguém tentando entrar numa conta | O histórico de outra pessoa | Senha adivinhada, token roubado | Limite de tentativas de login, scrypt, token só como hash e com validade, CSP contra XSS |
| Alguém com acesso ao código | A chave do Gemini ou do banco | Commit com segredo, dependência maliciosa | Segredos só no Render e no GitHub, varredura de segredos, Dependabot, `pip-audit`, `npm audit`, CodeQL |
| Site de terceiros | Usar a API ou o site sem permissão | CORS, iframe, link malicioso | CORS só para o domínio do site, `frame-ancestors 'none'` na API, CSP no site |

**Riscos aceitos**, conhecidos e assumidos por enquanto:

- O plano gratuito do Gemini pode usar as mensagens para treinar modelos. Por isso a interface avisa para não digitar dados pessoais.
- Pedidos vagos ("qual é?") e números por extenso passam pelos filtros automáticos. Neles, quem segura a resposta são as instruções do tutor, medidas pelo juiz da avaliação.
- O token da conta fica no `localStorage`. Um XSS conseguiria lê-lo, e a defesa é a CSP com o Markdown renderizado sem HTML.
- Os limites por IP ficam na memória e voltam a zero quando o servidor reinicia.
- O site no GitHub Pages não aceita cabeçalhos HTTP, então não dá para usar `frame-ancestors` nem um HSTS próprio.
- Um aluno determinado pode abrir a resposta em outro lugar, como o gabarito oficial do Inep, que é público. O objetivo dos guardrails é manter o tutor fiel ao método, não esconder um segredo.

## Privacidade e LGPD

- O Pista não pede nome, e-mail, CPF, idade nem qualquer dado pessoal.
- A conta é opcional. Ela guarda só o apelido escolhido, o hash da senha, a meta de estudo, as habilidades em foco, o tema e o histórico de questões resolvidas.
- A tela de cadastro orienta a não usar o próprio nome como apelido.
- A recuperação de conta é feita com um código mostrado uma única vez no cadastro, e não por e-mail, justamente para não coletar e-mail.
- O aluno pode apagar a conta a qualquer momento, e isso apaga também todo o histórico (direito à eliminação, LGPD art. 18).
- O identificador da sessão é aleatório (UUID) e gerado pelo servidor.
- O endereço IP é usado só para limitar abusos e não é salvo no banco.
- **Retenção:**
  - as conversas com o tutor ficam só na memória do servidor e somem em até 24 horas, ou antes, se o servidor reiniciar. Elas nunca são gravadas no banco;
  - do que se resolve com conta, o banco guarda só o resultado de cada questão (acertou, tentativas, se pediu explicação), sem o texto das mensagens. Isso fica enquanto a conta existir, porque é o histórico de progresso do próprio aluno;
  - os acessos (tokens de login) vencem em 30 dias e são apagados do banco ao iniciar a API e depois uma vez por dia.
- **Logs:**
  - a API registra uma linha por requisição, com método, caminho, status e tempo (`api/app/registro.py`). Ficam de fora o IP, a query string e o texto das mensagens;
  - o log de acesso do uvicorn, que grava o IP, fica desligado;
  - os logs do tutor registram só o estado da sessão e o motivo de um bloqueio, nunca o conteúdo;
  - o Render guarda os próprios logs de HTTP por alguns dias, e esses não dependem do projeto.
- Muitos estudantes do ENEM são menores de idade, por isso o projeto foi desenhado para não coletar dados pessoais desde o início (LGPD, art. 14).
- **Plano gratuito do Gemini:** nesse plano, o Google pode usar o conteúdo enviado para melhorar os produtos dele. Por isso a interface vai avisar para não digitar dados pessoais nas mensagens, e o tutor não pede nem comenta dados pessoais. Se o projeto passar a ter muitos usuários, a migração para o plano pago (em que os dados não são usados) entra no planejamento.
- Mensagens bloqueadas pelo guardrail de entrada não são guardadas, nem no histórico da sessão.
- No navegador, o token da conta fica no `localStorage` e vence em 30 dias. Isso exige proteger o site contra XSS: o Markdown é renderizado sem HTML bruto, e a política de segurança de conteúdo (CSP) entra na Fase 9.

## Controles técnicos

- HTTPS em todos os serviços
- CORS liberado apenas para o domínio do front-end
- Cabeçalhos de segurança na API (`api/app/cabecalhos.py`), em todas as respostas, inclusive erros e streaming:
  - `Content-Security-Policy: default-src 'none'`, porque a API só devolve JSON. A documentação (`/docs`) tem uma política própria, que libera só o jsDelivr;
  - `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e `Cache-Control: no-store`.
- Site: o GitHub Pages não permite configurar cabeçalhos HTTP, então a CSP vai numa tag `<meta>` gerada no build (`web/csp.ts`):
  - script só do próprio site, mais o script do tema, liberado pelo hash;
  - conexões só com a API configurada.

  Pela mesma limitação, `frame-ancestors` e HSTS não podem ser definidos no site. O HSTS do domínio `github.io` é do próprio GitHub.
- Análise estática com CodeQL (Python e TypeScript) em todo PR e toda semana
- Auditoria de dependências no CI: `pip-audit` na API e `npm audit` no site
- Validação de todas as entradas com Pydantic
- Filtros de conteúdo do Gemini definidos no código (`api/app/tutor/ia.py`): assédio, ódio e conteúdo sexual bloqueiam já no nível baixo, porque o público tem menores de idade; conteúdo perigoso bloqueia no nível médio, para não barrar questões de Química e Biologia. Uma resposta bloqueada cai no plano B
- Guardrails contra manipulação do tutor, com 60 casos testados em `api/tests/test_manipulacao.py`:
  - entrada: pedido para ignorar as instruções, troca de papel ("finja ser", "modo DAN"), extração do prompt, falsa autoridade ("sou a professora"), marcas de papel falsas (`<sistema>`, `[SYSTEM]`) e disfarces (letras espaçadas, números no lugar de letras), em português e inglês;
  - saída: a letra da alternativa certa, o valor dela e a posição ("a terceira alternativa").

  Limites conhecidos: pedidos vagos ("qual é?") e números por extenso ("novecentos e sessenta") passam por esses filtros. Nesses casos, quem segura a resposta são as instruções do tutor, e o juiz automático da avaliação mede se elas funcionaram.
- Backup: o Neon guarda o histórico do banco e permite criar uma cópia de qualquer momento dentro da janela de restauração. Testado em 19/11/2026:
  - foi criado um branch a partir de um momento do passado, com uma conta de teste já criada;
  - `api/scripts/conferir_backup.py` comparou a cópia com o original: as tabelas, as linhas (usuários e acessos) e a versão das migrações (`0002`) bateram;
  - o script mostra só a contagem de linhas, e as conexões ficam no terminal de quem roda, nunca no código.
- `main` protegida: mudanças só entram por pull request com o CI verde
- IP do aluno lido do cabeçalho `True-Client-IP`, definido pela Cloudflare na frente do Render, que o cliente não consegue forjar. O `X-Forwarded-For` não é usado, porque o Render mantém o valor enviado pelo cliente

O plano de implementação destes controles está na Fase 9 do [cronograma](docs/CRONOGRAMA.md).
