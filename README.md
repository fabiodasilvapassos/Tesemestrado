# Questionário Streamlit + Supabase

## Ficheiros principais

```text
app.py
scenarios.json
requirements.txt
supabase_schema.sql
.streamlit/secrets.example.toml
assets/scenarios/
```

## O que muda face à versão Google Sheets

Esta versão grava diretamente na tabela `responses` do Supabase.

Já não precisa de:
- Google Cloud
- Google Sheets API
- Service Account
- Credenciais JSON

## Passo 1 — Criar projeto no Supabase

1. Vai a https://supabase.com
2. Cria conta gratuita.
3. Cria um novo projeto.
4. Guarda a password da base de dados.

## Passo 2 — Criar tabela

1. No Supabase, vai a SQL Editor.
2. Abre o ficheiro `supabase_schema.sql`.
3. Copia o conteúdo.
4. Cola no SQL Editor.
5. Clica em Run.

Isto cria a tabela:

```text
responses
```

## Passo 3 — Obter URL e anon key

No Supabase:

```text
Project Settings
↓
API
```

Copia:

```text
Project URL
anon public key
```

## Passo 4 — Configurar Streamlit Secrets

No Streamlit Community Cloud:

```text
App
↓
Settings
↓
Secrets
```

Cola:

```toml
[supabase]
url = "COLOCAR_SUPABASE_PROJECT_URL"
key = "COLOCAR_SUPABASE_ANON_KEY"
```

## Passo 5 — Substituir ficheiros no GitHub

Substitui no teu repositório:

```text
app.py
requirements.txt
scenarios.json
```

Adiciona:

```text
supabase_schema.sql
.streamlit/secrets.example.toml
```

Mantém:

```text
assets/scenarios/
```

## Passo 6 — Dashboards

Quando tiveres os dashboards, coloca na pasta:

```text
assets/scenarios/
```

Com nomes:

```text
c01.png
c02.png
...
c16.png
```

## Passo 7 — Dados IA

Editar em:

```text
scenarios.json
```

Campos:

```text
ai_signal
ai_confidence
ai_factors
```

## Passo 8 — Exportar respostas

No Supabase:

```text
Table Editor
↓
responses
↓
Export CSV
```