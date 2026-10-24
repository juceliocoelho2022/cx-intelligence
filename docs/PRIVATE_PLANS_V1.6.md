# CX Intelligence v1.6 beta — Planos privados com OIDC e PostgreSQL

**Status:** funcionalidade opcional/experimental. **O Render público continua sem login e sem armazenamento de planos.** Última Release oficial: [v1.5.0](https://github.com/juceliocoelho2022/cx-intelligence/releases/tag/v1.5.0).

## Arquitetura

O acesso privado utiliza autenticação OpenID Connect nativa do Streamlit, validando emissor (iss), público (aud), identificador (sub) e expiração (exp). Cada conta recebe um identificador interno SHA-256 de emissor + separador + sujeito, não do e-mail. O PostgreSQL 16 usa Row-Level Security (RLS) forçada e um papel de conexão não privilegiado. A aplicação confere o estado da política RLS antes de ler ou gravar.

Somente ações e histórico sintéticos são persistidos após confirmação explícita. Metas e KPIs continuam calculados sob os filtros atuais. Salvamento de planos nomeados usa controle de versão otimista para detectar gravações simultâneas. Nenhuma senha ou token OIDC é gravado no banco de planos.

## Público e privado nunca se misturam

- Na demo pública, CX_PUBLIC_DEMO=true força o recurso privado a ficar desativado, mesmo que CX_PRIVATE_PLANS_ENABLED seja indevidamente configurado como true.
- No ambiente privado, CX_PRIVATE_PLANS_ENABLED=true precisa ser informado explicitamente e separado do Render público.
- Não há migração ou inicialização automática de tabelas na aplicação; a implantação exige um administrador.
- O produto **não** está homologado para dados reais de clientes, autenticação multiempresa, operações financeiras ou uso corporativo.

## Instalação privada

1. Execute: python -m pip install -r requirements-private.txt
2. Configure um cliente OIDC em um provedor confiável e registre o redirect_uri http://localhost:8501/oauth2callback para desenvolvimento; use HTTPS para implantação privada. Copie .streamlit/secrets.example.toml para .streamlit/secrets.toml e preencha dados reais **apenas** nesse arquivo ignorado pelo Git.
3. Em um banco PostgreSQL privado, aplique migrations/006_private_action_plans.sql com um **usuário de migração**, não o papel de execução.
4. Crie um usuário SQL específico da aplicação, não superusuário e sem BYPASSRLS, ownership da tabela ou DDL:

    CREATE ROLE cx_plan_app LOGIN PASSWORD 'SENHA_FORTE_ALEATORIA' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    GRANT USAGE ON SCHEMA public TO cx_plan_app;
    GRANT SELECT,INSERT,UPDATE,DELETE ON cx_private_action_plans TO cx_plan_app;

5. Defina variáveis **somente** na instalação privada:

    CX_PUBLIC_DEMO=false
    CX_PRIVATE_PLANS_ENABLED=true
    CX_PLAN_OIDC_ISSUER=https://accounts.google.com
    CX_PLAN_OIDC_CLIENT_ID=MESMO_CLIENT_ID_DO_SECRETS_TOML
    CX_PRIVATE_PLAN_DATABASE_URL=postgresql://cx_plan_app:SENHA@localhost:5432/NOME_DB

Para PostgreSQL em outra máquina, a conexão exige sslmode=verify-full e certificado válido. Não configure a URL do banco no Render público. Nunca inclua credenciais em commits.

## Fluxo

Na aba Metas v1.5, uma instalação privada mostra a seção **Meus planos privados**, permitindo login via provedor OIDC, salvar explicitamente, salvar como novo, carregar e **excluir** um plano salvo. Carregar substitui a lista de ações daquela sessão, não os KPIs; exporte JSON antes para conservar versões. Excluir exige confirmação específica do plano e revisão atualizada, removendo apenas o registro persistido — ações da sessão podem permanecer até logout/encerramento. A verificação de revisão impede sobrescrever ou excluir inadvertidamente uma versão alterada em outra sessão.

O Streamlit mantém cookies de identidade por até 30 dias; a aplicação compara o campo exp em cada uso privado e pode exigir novo login antecipado. O isolamento usa as claims OIDC verificadas pela biblioteca nativa; o usuário não seleciona um identificador de proprietário.

## Testes e limites

A suíte tests/test_private_plans.py verifica OIDC inválido/expirado, bloqueio no modo público, payloads inválidos, conexão remota com TLS verificado, acesso a contas diferentes via PostgreSQL RLS, papel runtime sem BYPASSRLS, atualização otimista e exclusão com confirmação de revisão. Os testes de integração usam exclusivamente TEST_DATABASE_URL de ambiente de CI, e não o banco de produção.

**A integração OIDC real com provedor externo ainda não foi testada**, pois não há cliente OIDC privado configurado para essa implantação. Essa etapa é necessária antes de considerar o armazenamento autenticado pronto para uso real. Não usar dados pessoais ou bancários reais nesta beta.
