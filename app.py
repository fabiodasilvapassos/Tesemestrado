import json
import uuid
from datetime import datetime
from pathlib import Path

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


st.set_page_config(
    page_title="Questionário — Decisão Humana e IA",
    layout="centered"
)

SCENARIOS_FILE = "scenarios.json"
WORKSHEET_NAME = "responses"

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

HEADERS = [
    "participant_id",
    "started_at",
    "finished_at",
    "consentimento",
    "perfil_01",
    "perfil_02",
    "perfil_03",
    "perfil_04",
    "perfil_05",
    "scenario_id",
    "scenario_label",
    "hum_decision_initial",
    "hum_confidence_initial",
    "hum_main_factor",
    "hum_risk_perceived",
    "ai_signal",
    "ai_confidence",
    "ai_factors",
    "ia_agreement",
    "ia_trust",
    "ia_explainability",
    "hyb_change",
    "hyb_decision_final",
    "hyb_influence",
    "hyb_confidence_final",
    "decision_changed",
    "confidence_change",
    "final_01_difficulty",
    "final_02_general_confidence",
    "final_03_ai_usefulness",
    "final_04_ai_revision_frequency",
    "final_05_perceived_correctness",
    "final_06_willingness_to_use_ai"
]


def load_scenarios():
    with open(SCENARIOS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def init_state():
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())

    if "started_at" not in st.session_state:
        st.session_state.started_at = datetime.now().isoformat(timespec="seconds")

    if "submitted" not in st.session_state:
        st.session_state.submitted = False


@st.cache_resource
def get_worksheet():
    if "gcp_service_account" not in st.secrets:
        st.error("Falta configurar o bloco [gcp_service_account] nos Streamlit Secrets.")
        st.stop()

    service_account_info = dict(st.secrets["gcp_service_account"])

    if "spreadsheet_id" not in service_account_info:
        st.error("Falta o campo spreadsheet_id nos Streamlit Secrets.")
        st.stop()

    spreadsheet_id = service_account_info.pop("spreadsheet_id")

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=2000,
            cols=len(HEADERS)
        )
        worksheet.append_row(HEADERS)

    current_headers = worksheet.row_values(1)

    if current_headers != HEADERS:
        worksheet.clear()
        worksheet.append_row(HEADERS)

    return worksheet


def save_rows_to_google_sheets(rows):
    worksheet = get_worksheet()
    values = [[row.get(header, "") for header in HEADERS] for row in rows]
    worksheet.append_rows(values, value_input_option="USER_ENTERED")


def scale_question(label, key, low_label=None, high_label=None):
    help_text = ""
    if low_label and high_label:
        help_text = f"1 = {low_label} | 7 = {high_label}"

    return st.radio(
        label,
        SCALE_1_7,
        horizontal=True,
        key=key,
        help=help_text
    )


def render_scenario(scenario):
    st.header(scenario["label"])

    image_path = Path(scenario["image"])
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.info(f"[INSERIR DASHBOARD: {scenario['image']}]")

    st.subheader("Bloco A — Modelo Humano")

    hum_decision_initial = st.radio(
        "Qual seria a sua decisão para a próxima sessão de mercado?",
        DECISIONS,
        horizontal=True,
        key=f"{scenario['id']}_hum_decision_initial"
    )

    hum_confidence_initial = scale_question(
        "Qual o grau de confiança na sua decisão inicial?",
        f"{scenario['id']}_hum_confidence_initial",
        "Muito baixa",
        "Muito elevada"
    )

    hum_main_factor = st.radio(
        "Qual o principal fator que influenciou a sua decisão?",
        MAIN_FACTORS,
        key=f"{scenario['id']}_hum_main_factor"
    )

    hum_risk_perceived = scale_question(
        "Como classifica o risco deste cenário?",
        f"{scenario['id']}_hum_risk_perceived",
        "Muito baixo",
        "Muito elevado"
    )

    st.subheader("Bloco B — Modelo IA")

    st.markdown(
        f"""
        **Sinal da IA:** {scenario["ai_signal"]}  
        **Confiança do modelo:** {scenario["ai_confidence"]}  
        **Principais fatores:** {", ".join(scenario["ai_factors"])}
        """
    )

    ia_agreement = scale_question(
        "Antes de observar a explicação da IA, qual o grau de concordância com a recomendação apresentada?",
        f"{scenario['id']}_ia_agreement",
        "Discordância total",
        "Concordância total"
    )

    ia_trust = scale_question(
        "Qual o grau de confiança que deposita nesta recomendação da IA?",
        f"{scenario['id']}_ia_trust",
        "Nenhuma confiança",
        "Confiança muito elevada"
    )

    ia_explainability = scale_question(
        "Os fatores apresentados pela IA ajudaram a compreender a recomendação?",
        f"{scenario['id']}_ia_explainability",
        "Nada",
        "Muito"
    )

    st.subheader("Bloco C — Modelo Híbrido")

    hyb_change = st.radio(
        "Após observar a recomendação da IA pretende:",
        ["Manter a decisão inicial", "Alterar a decisão inicial"],
        key=f"{scenario['id']}_hyb_change"
    )

    hyb_decision_final = st.radio(
        "Qual é a sua decisão final?",
        DECISIONS,
        horizontal=True,
        key=f"{scenario['id']}_hyb_decision_final"
    )

    hyb_influence = scale_question(
        "Em que medida a IA influenciou a sua decisão final?",
        f"{scenario['id']}_hyb_influence",
        "Nenhuma influência",
        "Influência muito elevada"
    )

    hyb_confidence_final = scale_question(
        "Qual o grau de confiança na sua decisão final?",
        f"{scenario['id']}_hyb_confidence_final",
        "Muito baixa",
        "Muito elevada"
    )

    return {
        "scenario_id": scenario["id"],
        "scenario_label": scenario["label"],
        "hum_decision_initial": hum_decision_initial,
        "hum_confidence_initial": hum_confidence_initial,
        "hum_main_factor": hum_main_factor,
        "hum_risk_perceived": hum_risk_perceived,
        "ai_signal": scenario["ai_signal"],
        "ai_confidence": scenario["ai_confidence"],
        "ai_factors": "; ".join(scenario["ai_factors"]),
        "ia_agreement": ia_agreement,
        "ia_trust": ia_trust,
        "ia_explainability": ia_explainability,
        "hyb_change": hyb_change,
        "hyb_decision_final": hyb_decision_final,
        "hyb_influence": hyb_influence,
        "hyb_confidence_final": hyb_confidence_final,
        "decision_changed": int(hum_decision_initial != hyb_decision_final),
        "confidence_change": hyb_confidence_final - hum_confidence_initial
    }


def main():
    init_state()

    if st.session_state.submitted:
        st.success("As suas respostas já foram registadas. Obrigado pela participação.")
        return

    scenarios = load_scenarios()

    st.title("Questionário — Decisão Humana, IA e Modelo Híbrido")

    st.write(
        "Este estudo analisa decisões de investimento em cenários financeiros anonimizados, "
        "comparando decisão humana, recomendação de Inteligência Artificial e decisão final híbrida."
    )

    with st.form("survey_form"):
        st.header("Parte 1 — Consentimento informado")

        consentimento = st.radio(
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

        for scenario in scenarios:
            st.divider()
            scenario_answers.append(render_scenario(scenario))

        st.divider()
        st.header("Parte 5 — Questões finais")

        final_01 = scale_question(
            "FINAL_01 — Dificuldade geral dos cenários",
            "final_01",
            "Muito baixa",
            "Muito elevada"
        )

        final_02 = scale_question(
            "FINAL_02 — Confiança geral nas suas decisões",
            "final_02",
            "Muito baixa",
            "Muito elevada"
        )

        final_03 = scale_question(
            "FINAL_03 — Utilidade percebida da IA",
            "final_03",
            "Muito baixa",
            "Muito elevada"
        )

        final_04 = st.radio(
            "FINAL_04 — Com que frequência a IA levou-o(a) a rever decisões?",
            ["Nunca", "Poucas vezes", "Algumas vezes", "Muitas vezes", "Sempre"]
        )

        final_05 = st.radio(
            "FINAL_05 — Em quantos cenários acredita ter tomado a decisão correta?",
            ["0–25%", "26–50%", "51–75%", "76–100%"]
        )

        final_06 = scale_question(
            "FINAL_06 — Em contexto real de investimento, estaria disposto a utilizar recomendações geradas por IA?",
            "final_06",
            "Nunca",
            "Sempre"
        )

        submitted = st.form_submit_button("Submeter respostas")

    if submitted:
        if consentimento == "Não aceito participar":
            st.warning("Obrigado pelo seu tempo. Como não aceitou participar, as respostas não foram registadas.")
            return

        finished_at = datetime.now().isoformat(timespec="seconds")

        rows = []

        for answer in scenario_answers:
            row = {
                "participant_id": st.session_state.participant_id,
                "started_at": st.session_state.started_at,
                "finished_at": finished_at,
                "consentimento": consentimento,
                "perfil_01": perfil_01,
                "perfil_02": perfil_02,
                "perfil_03": perfil_03,
                "perfil_04": perfil_04,
                "perfil_05": perfil_05,
                "final_01_difficulty": final_01,
                "final_02_general_confidence": final_02,
                "final_03_ai_usefulness": final_03,
                "final_04_ai_revision_frequency": final_04,
                "final_05_perceived_correctness": final_05,
                "final_06_willingness_to_use_ai": final_06
            }

            row.update(answer)
            rows.append(row)

        try:
            save_rows_to_google_sheets(rows)
            st.session_state.submitted = True
            st.success("Obrigado. As suas respostas foram registadas com sucesso na Google Sheets.")
        except Exception as error:
            st.error("Ocorreu um erro ao gravar as respostas. Por favor, contacte o investigador responsável.")
            st.exception(error)


if __name__ == "__main__":
    main()