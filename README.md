# Questionário Streamlit + Google Sheets

Esta versão grava diretamente todas as respostas numa Google Sheet.

## Ficheiros do projeto

```text
app.py
scenarios.json
requirements.txt
README.md
.streamlit/secrets.example.toml
assets/scenarios/
```

## Como funciona

Cada participante gera 16 linhas na folha `responses`, uma por cenário.

A aplicação cria automaticamente a folha `responses` e os cabeçalhos, desde que a Google Sheet exista e esteja partilhada com a Service Account.

## Passo 1 — Criar Google Sheet

1. Abre Google Sheets.
2. Cria uma folha nova.
3. Copia o ID da folha.

Exemplo:

```text
https://docs.google.com/spreadsheets/d/1ABCDEF123456789/edit
```

O ID é:

```text
1ABCDEF123456789
```

## Passo 2 — Criar Service Account

1. Vai a Google Cloud Console.
2. Cria um projeto.
3. Ativa a Google Sheets API.
4. Cria uma Service Account.
5. Cria uma chave JSON.
6. Copia os campos do ficheiro JSON.

## Passo 3 — Partilhar a Google Sheet

No ficheiro JSON existe um email do tipo:

```text
xxxxx@xxxxx.iam.gserviceaccount.com
```

Na Google Sheet, clica em Partilhar e dá permissão de Editor a esse email.

## Passo 4 — Configurar Streamlit Secrets

No Streamlit Community Cloud:

```text
App → Settings → Secrets
```

Cola o conteúdo baseado no ficheiro:

```text
.streamlit/secrets.example.toml
```

Nunca coloques as credenciais reais no GitHub.

## Passo 5 — Dashboards

Coloca os dashboards em:

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

Enquanto não existirem, a aplicação mostra placeholders.

## Passo 6 — Editar dados da IA

Edita:

```text
scenarios.json
```

Campos:

```text
ai_signal
ai_confidence
ai_factors
```

## Deploy no Streamlit

No Streamlit Community Cloud:

```text
Repository: o teu repositório
Branch: main
Main file path: app.py
```

Depois clica em Deploy.