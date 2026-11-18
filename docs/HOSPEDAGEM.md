# Hospedagem

Onde o Pista roda e como colocar no ar. Tudo no plano gratuito.

| Parte | Onde | Endereço |
|---|---|---|
| Site (front-end) | GitHub Pages | https://sabrinasiilva.github.io/pista-enem/ |
| API | Render (Docker) | https://pista-api.onrender.com (o Render confirma o nome na criação) |
| Banco de dados | Neon (PostgreSQL) | só a API acessa |
| IA | Google Gemini | só a API acessa |

```mermaid
flowchart LR
    A[Aluno] --> S[Site<br/>GitHub Pages]
    S -->|HTTPS| R[API<br/>Render]
    R --> N[(Banco<br/>Neon)]
    R --> G[Gemini]
```

**Por que o banco não fica no Render:** o disco do serviço gratuito é apagado a cada deploy (as contas sumiriam), e o PostgreSQL gratuito do Render expira em 30 dias. O Neon é gratuito, não expira e tem 1 GB.

**Limites do plano gratuito do Render** (conferidos em novembro de 2026):
- A API dorme depois de 15 minutos sem acesso e leva até 1 minuto para acordar. O site avisa quando isso acontece.
- São 750 horas por mês, divididas entre todos os serviços gratuitos da conta (o CO2Bank inclusive). Serviço dormindo não gasta horas.
- **Não use "pings" para manter a API acordada** (UptimeRobot a cada 5 minutos, por exemplo). Com dois serviços acordados o mês inteiro, as horas acabam e o Render suspende os dois até o mês seguinte.

---

## 1. Chave do Gemini

1. Entre em [aistudio.google.com](https://aistudio.google.com) com a sua conta Google.
2. Clique em **Get API key** e depois em **Create API key**. Se pedir um projeto do Google Cloud, deixe criar um novo.
3. Copie a chave e guarde num lugar seguro (gerenciador de senhas ou nota privada).
4. Recomendado: no [Google Cloud Console](https://console.cloud.google.com/apis/credentials), abra a chave e, em **API restrictions**, restrinja a **Generative Language API**. Se a chave vazar, ela só serve para isso.

Cuidados:
- A chave **nunca** vai para o GitHub, nem para o chat. Ela fica só no Render (passo 3) e no arquivo `api/.env` do seu computador, que o Git ignora.
- No plano gratuito, o Google pode usar o conteúdo enviado para melhorar os produtos dele. Por isso o site pede para não escrever dados pessoais.

Para usar a IA localmente também, copie `api/.env.example` para `api/.env` e preencha `GEMINI_API_KEY=`.

## 2. Banco no Neon

1. Entre em [neon.tech](https://neon.tech), clique em **Sign up** e em **Continue with GitHub**.
2. Crie um projeto:
   - **Project name:** `pista`
   - **Postgres version:** a que vier marcada
   - **Region:** AWS US East 1 (N. Virginia), a mesma região da API no Render
3. No painel do projeto, clique em **Connect**. Deixe **Connection pooling** ligado e copie a **connection string**. Ela começa com `postgresql://` e tem a senha do banco dentro, então trate como a chave do Gemini.

Não é preciso criar tabelas: a API cria tudo sozinha ao iniciar (migrações do Alembic).

## 3. API no Render

1. Entre em [dashboard.render.com](https://dashboard.render.com) com a mesma conta do CO2Bank.
2. Clique em **New +** e depois em **Blueprint**.
3. Conecte o repositório `sabrinasiilva/pista-enem`. Se ele não aparecer, clique em **Configure account** e dê acesso a esse repositório no GitHub.
4. O Render lê o arquivo `render.yaml` e mostra o serviço `pista-api`. Ele vai pedir duas variáveis:
   - `GEMINI_API_KEY`: a chave do passo 1
   - `DATABASE_URL`: a connection string do passo 2
5. Clique em **Deploy Blueprint** (ou **Apply**). O primeiro deploy leva de 3 a 5 minutos.
6. Quando terminar, abra `https://<endereço-do-serviço>/health`. Deve aparecer `"status":"ok"` e `"ia":"gemini"`.

Depois disso, todo push na `main` que mude a API refaz o deploy sozinho.

## 4. Site no GitHub Pages

O site é publicado automaticamente pelo workflow `publicar-site.yml` a cada mudança em `web/` na `main`.

- Se o endereço da API **for** `https://pista-api.onrender.com`, não precisa fazer nada.
- Se o Render der outro nome, crie no GitHub uma variável com o endereço certo: **Settings › Secrets and variables › Actions › Variables › New repository variable**, nome `API_URL`. Depois rode o workflow de novo em **Actions › Publicar site › Run workflow**.

## 5. Conferir

1. Abra https://sabrinasiilva.github.io/pista-enem/
2. Resolva uma questão errando de propósito. A pista deve responder ao seu erro, e o aviso de "modo básico" não deve aparecer.
3. Crie uma conta, resolva outra questão e veja se ela aparece em **Meu progresso**.

## 6. Usuário do banco com permissão mínima

Por padrão, a API usa o usuário dono do banco (`neondb_owner`), que pode apagar tabelas. O mais seguro é a API usar no dia a dia um usuário que só lê e escreve dados, e deixar o dono apenas para as migrações. Assim, mesmo que alguém consiga mandar um comando malicioso, ele não apaga a estrutura do banco.

1. Gere uma senha longa (32 caracteres ou mais) no seu gerenciador de senhas. Use só letras e números, para não precisar escapar nada na URL.
2. No Neon, abra o projeto **pista** e clique em **SQL Editor**. Cole o código abaixo, troque `SENHA_FORTE` pela senha do passo 1 e clique em **Run**:

```sql
-- usuário da API: entra no banco, mas não cria nem apaga tabelas
CREATE ROLE pista_app WITH LOGIN PASSWORD 'SENHA_FORTE';
GRANT CONNECT ON DATABASE neondb TO pista_app;
GRANT USAGE ON SCHEMA public TO pista_app;

-- pode ler e escrever nas tabelas que já existem...
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pista_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pista_app;

-- ...e nas que as migrações criarem no futuro
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pista_app;
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO pista_app;
```

3. Monte a connection string do usuário novo: pegue a que você já usa e troque só o começo, `neondb_owner:senha-antiga@`, por `pista_app:SENHA_FORTE@`. O resto (servidor, `/neondb?sslmode=require...`) fica igual.
4. No Render, abra **pista-api › Environment** e:
   - crie `MIGRACOES_DATABASE_URL` com a connection string **antiga** (a do dono);
   - troque o valor de `DATABASE_URL` pela connection string **nova** (a do `pista_app`);
   - clique em **Save, rebuild, and deploy**.
5. Depois do deploy, abra `/health`: deve continuar com `"status":"ok"`.

Se o nome do banco ou do dono for diferente de `neondb` e `neondb_owner`, eles aparecem na própria connection string: `postgresql://DONO:senha@servidor/BANCO`.

## Monitoramento

O workflow `monitor.yml` confere o site e a API de 6 em 6 horas. Se algo cair (ou a IA sair do ar), ele falha e o GitHub manda um e-mail. Quatro visitas por dia gastam pouco das horas gratuitas do Render.

## Se algo der errado

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Site mostra "Não consegui falar com o servidor" | API dormindo ou endereço errado | Espere 1 minuto e recarregue; confira a variável `API_URL` |
| Site aparece em "modo básico" | `GEMINI_API_KEY` vazia ou errada no Render | Confira a variável em **Render › pista-api › Environment** |
| Deploy no Render falha logo no início | `DATABASE_URL` errada | Copie de novo a connection string do Neon |
| Erro de CORS no console do navegador | Site num endereço diferente de `sabrinasiilva.github.io` | Ajuste `CORS_ORIGENS` no Render |
