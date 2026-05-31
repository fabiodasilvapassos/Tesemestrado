import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import uuid

st.set_page_config(
    page_title="Questionário — Decisão Humana e IA",
    layout="centered"
)

DATA_FILE = "responses.csv"
SCENARIOS_FILE = "scenarios.json"

DECISIONS = ["Long", "Neutro", "Short"]
SCALE_1_7 = list(range(1, 8))

MAIN_FACTORS = [
    "Evolução recente do preço",
    "Médias móveis",
    "RSI",
    "Volume",
    "Volatilidade",
    "Combinação de fatores",
    "Intuição/Experiência"
]

def load_scenarios():
    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def init_state():
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if "started_at" not in st.session_state:
        st.session_state.started_at = datetime.now().isoformat(timespec="seconds")

def save_response(data):
    df = pd.DataFrame(data)
    file_exists = os.path.exists(DATA_FILE)

    df.to_csv(
        DATA_FILE,
        mode="a",
        index=False,
        header=not file_exists,
        encoding="utf-8-sig"
    )

def show_scale(label, key, low=None, high=None):
    help_text = ""
    if low and high:
        help_text = f"1 = {low} | 7 = {high}"
    return st.radio(
        label,
        SCALE_1_7,
        horizontal=True,
        key=key,
        help=help_text
    )

def show_scenario(s):
    st.header(s["label"])

    image_path = Path(s["image"])
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.info(f"[INSERIR DASHBOARD: {s['image']}]")

    st.subheader("Bloco A — Modelo Humano")

    hum_decision = st.radio(
        "Qual seria a sua decisão para a próxima sessão de mercado?",
        DECISIONS,
        horizontal=True,
        key=f"{s['id']}_hum_decision"
    )

    hum_confidence = show_scale(
        "Qual o grau de confiança na sua decisão inicial?",
        f"{s['id']}_hum_confidence",
        "Muito baixa",
        "Muito elevada"
    )

    hum_factor = st.radio(
        "Qual o principal fator que influenciou a sua decisão?",
        MAIN_FACTORS,
        key=f"{s['id']}_hum_factor"
    )

    hum_risk = show_scale(
        "Como classifica o risco deste cenário?",
        f"{s['id']}_hum_risk",
        "Muito baixo",
        "Muito elevado"
    )

    st.subheader("Bloco B — Modelo IA")

    st.markdown(
        f"""
        **Sinal da IA:** {s["ai_signal"]}  
        **Confiança do modelo:** {s["ai_confidence"]}  
        **Principais fatores:** {", ".join(s["ai_factors"])}
        """
    )

    ia_agreement = show_scale(
        "Antes de observar a explicação da IA, qual o grau de concordância com a recomendação apresentada?",
        f"{s['id']}_ia_agreement",
        "Discordância total",
        "Concordância total"
    )

    ia_trust = show_scale(
        "Qual o grau de confiança que deposita nesta recomendação da IA?",
        f"{s['id']}_ia_trust",
        "Nenhuma confiança",
        "Confiança muito elevada"
    )

    ia_explainability = show_scale(
        "Os fatores apresentados pela IA ajudaram a compreender a recomendação?",
        f"{s['id']}_ia_explainability",
        "Nada",
        "Muito"
    )

    st.subheader("Bloco C — Modelo Híbrido")

    hyb_change = st.radio(
        "Após observar a recomendação da IA pretende:",
        ["Manter a decisão inicial", "Alterar a decisão inicial"],
        key=f"{s['id']}_hyb_change"
    )

    hyb_final_decision = st.radio(
        "Qual é a sua decisão final?",
        DECISIONS,
        horizontal=True,
        key=f"{s['id']}_hyb_final_decision"
    )

    hyb_influence = show_scale(
        "Em que medida a IA influenciou a sua decisão final?",
        f"{s['id']}_hyb_influence",
        "Nenhuma influência",
        "Influência muito elevada"
    )

    hyb_final_confidence = show_scale(
        "Qual o grau de confiança na sua decisão final?",
        f"{s['id']}_hyb_final_confidence",
        "Muito baixa",
        "Muito elevada"
    )

    return {
        "scenario_id": s["id"],
        "scenario_label": s["label"],
        "hum_decision_initial": hum_decision,
        "hum_confidence_initial": hum_confidence,
        "hum_main_factor": hum_factor,
        "hum_risk_perceived": hum_risk,
        "ai_signal": s["ai_signal"],
        "ai_confidence": s["ai_confidence"],
        "ai_factors": "; ".join(s["ai_factors"]),
        "ia_agreement": ia_agreement,
        "ia_trust": ia_trust,
        "ia_explainability": ia_explainability,
        "hyb_change": hyb_change,
        "hyb_decision_final": hyb_final_decision,
        "hyb_influence": hyb_influence,
        "hyb_confidence_final": hyb_final_confidence,
        "decision_changed": int(hum_decision != hyb_final_decision)
    }

def main():
    init_state()
    scenarios = load_scenarios()

    st.title("Questionário — Decisão Humana, IA e Modelo Híbrido")

    st.write(
        "Este estudo analisa decisões de investimento em cenários financeiros anonimizados, "
        "comparando decisão humana, recomendação de IA e decisão final híbrida."
    )

    with st.form("questionnaire_form"):
        st.header("Parte 1 — Consentimento informado")

        consent = st.radio(
            "Declaro que compreendi o objetivo do estudo e aceito participar voluntariamente.",
            ["Sim, aceito participar", "Não aceito participar"]
        )

        st.header("Parte 2 — Caracterização do participante")

        perfil_01 = st.radio(
            "Experiência em mercados financeiros",
            [
                "Sem experiência relevante",
                "Conhecimento académico",
                "Investidor particular",
                "Experiência profissional em investimento",
                "Experiência profissional em corretagem",
                "Experiência profissional em gestão de risco",
                "Outro"
            ]
        )

        perfil_02 = st.radio(
            "Frequência com que acompanha mercados financeiros",
            ["Raramente", "Mensalmente", "Semanalmente", "Diariamente", "Várias vezes por dia"]
        )

        perfil_03 = st.radio(
            "Familiaridade com análise técnica",
            ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"]
        )

        perfil_04 = st.radio(
            "Familiaridade com Inteligência Artificial aplicada a finanças",
            ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"]
        )

        perfil_05 = st.radio(
            "Familiaridade com estratégias Short",
            ["Nenhuma", "Baixa", "Moderada", "Elevada"]
        )

        st.header("Parte 3 — Instruções gerais")
        st.markdown(
            """
            O questionário contém **16 cenários financeiros anonimizados**.

            O horizonte de decisão corresponde à **próxima sessão de mercado**.

            Não existem respostas certas ou erradas.

            Utilize apenas a informação disponível até ao ponto de decisão.

            Cada cenário apresenta informação baseada em:

            - Market Evolution
            - Moving Average Structure
            - Relative Strength Structure, RSI
            - Relative Trading Activity
            - Market Risk Regime, Volatility
            """
        )

        scenario_answers = []

        for s in scenarios:
            st.divider()
            scenario_answers.append(show_scenario(s))

        st.divider()
        st.header("Parte 5 — Questões finais")

        final_01 = show_scale("FINAL_01 — Dificuldade geral dos cenários", "final_01", "Muito baixa", "Muito elevada")
        final_02 = show_scale("FINAL_02 — Confiança geral nas suas decisões", "final_02", "Muito baixa", "Muito elevada")
        final_03 = show_scale("FINAL_03 — Utilidade percebida da IA", "final_03", "Muito baixa", "Muito elevada")

        final_04 = st.radio(
            "FINAL_04 — Com que frequência a IA levou-o(a) a rever decisões?",
            ["Nunca", "Poucas vezes", "Algumas vezes", "Muitas vezes", "Sempre"]
        )

        final_05 = st.radio(
            "FINAL_05 — Em quantos cenários acredita ter tomado a decisão correta?",
            ["0–25%", "26–50%", "51–75%", "76–100%"]
        )

        final_06 = show_scale(
            "FINAL_06 — Em contexto real de investimento, estaria disposto a utilizar recomendações geradas por IA?",
            "final_06",
            "Nunca",
            "Sempre"
        )

        submitted = st.form_submit_button("Submeter respostas")

    if submitted:
        if consent == "Não aceito participar":
            st.warning("Obrigado pelo seu tempo. Como não aceitou participar, as restantes respostas não serão registadas.")
            return

        finished_at = datetime.now().isoformat(timespec="seconds")

        rows = []
        for ans in scenario_answers:
            row = {
                "participant_id": st.session_state.participant_id,
                "started_at": st.session_state.started_at,
                "finished_at": finished_at,
                "consent": consent,
                "perfil_01": perfil_01,
                "perfil_02": perfil_02,
                "perfil_03": perfil_03,
                "perfil_04": perfil_04,
                "perfil_05": perfil_05,
                "final_01": final_01,
                "final_02": final_02,
                "final_03": final_03,
                "final_04": final_04,
                "final_05": final_05,
                "final_06": final_06,
            }
            row.update(ans)
            rows.append(row)

        save_response(rows)

        st.success("Obrigado. As suas respostas foram registadas com sucesso.")

if __name__ == "__main__":
    main()