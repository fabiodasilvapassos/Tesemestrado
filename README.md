# Questionário Streamlit — Decisão Humana, IA e Modelo Híbrido

## Como usar localmente

1. Instalar dependências:

```bash
pip install -r requirements.txt
```

2. Executar:

```bash
streamlit run app.py
```

## Dashboards

Colocar as imagens dos cenários nesta pasta:

```text
assets/scenarios/
```

Com estes nomes:

```text
c01.png
c02.png
...
c16.png
```

Enquanto as imagens não existirem, a app mostra placeholders.

## Dados da IA

Editar o ficheiro:

```text
scenarios.json
```

Campos principais:

- ai_signal
- ai_confidence
- ai_factors

## Exportação

As respostas são guardadas automaticamente no ficheiro:

```text
responses.csv
```

Cada linha corresponde a uma resposta de um participante para um cenário.