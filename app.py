import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from supabase import create_client, Client


st.set_page_config(
    page_title="Questionário — Decisão Humana e IA",
    layout="centered"
)

SCENARIOS_FILE = "scenarios.json"
SUPABASE_TABLE = "responses"

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


@st.cache_resource
def get_supabase_client() -> Client:
    if "supabase" not in st.secrets:
        st.error("Falta configurar o bloco [supabase] nos Streamlit Secrets.")
        st.stop()

    url = st.secrets["supabase"].get("url")
    key = st.secrets["supabase"].get("key")

    if not url or not key:
        st.error("Faltam os campos url e/ou key nos Streamlit Secrets.")
        st.stop()

    return create_client(url, key)


@st.cache_data
def load_scenarios():
    with open(SCENARIOS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def init_state():
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if "started_at" not in st.session_state:
        st.session_state.started_at = datetime.now().isoformat(timespec="seconds")
    if "page" not in st.session_state:
        st.session_state.page = 0
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "profile" not in st.session_state:
        st.session_state.profile = {}
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "final_answers" not in st.session_state:
        st.session_state.final_answers = {}


def next_page():
    st.session_state.page += 1
    st.rerun()


def previous_page():
    if st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()


def save_rows_to_supabase(rows):
    supabase = get_supabase_client()
    return supabase.table(SUPABASE_TABLE).insert(rows).execute()


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


def show_progress(total_pages):
    current = st.session_state.page + 1
    st.progress(current / total_pages)
    st.caption(f"Etapa {current} de {total_pages}")


def render_header():
    st.title("Questionário — Decisão Humana, IA e Modelo Híbrido")
    st.write(
        "Este estudo analisa decisões de investimento em cenários financeiros anonimizados, "
        "comparando decisão humana, recomendação de Inteligência Artificial e decisão final híbrida."
    )


def render_consent():
    render_header()
    st.header("Parte 1 — Consentimento informado")

    consentimento = st.radio(
        "Declaro que compreendi o objetivo do estudo e aceito participar voluntariamente.",
        ["Sim, aceito participar", "Não aceito participar"],
        key="consentimento"
    )

    if st.button("Continuar"):
        if consentimento == "Não aceito participar":
            st.warning("Obrigado pelo seu tempo. Como não aceitou participar, o questionário termina aqui.")
            st.stop()

        st.session_state.profile["consentimento"] = consentimento
        next_page()


def render_profile():
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
        ],
        key="perfil_01"
    )

    perfil_02 = st.radio(
        "Frequência com que acompanha mercados financeiros",
        ["Raramente", "Mensalmente", "Semanalmente", "Diariamente", "Várias vezes por dia"],
        key="perfil_02"
    )

    perfil_03 = st.radio(
        "Familiaridade com análise técnica",
        ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"],
        key="perfil_03"
    )

    perfil_04 = st.radio(
        "Familiaridade com Inteligência Artificial aplicada a finanças",
        ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"],
        key="perfil_04"
    )

    perfil_05 = st.radio(
        "Familiaridade com estratégias Short",
        ["Nenhuma", "Baixa", "Moderada", "Elevada"],
        key="perfil_05"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Continuar"):
            st.session_state.profile.update({
                "perfil_01": perfil_01,
                "perfil_02": perfil_02,
                "perfil_03": perfil_03,
                "perfil_04": perfil_04,
                "perfil_05": perfil_05
            })
            next_page()


def render_instructions():
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

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Começar cenários"):
            next_page()


def ensure_scenario_answer(scenario_id):
    if scenario_id not in st.session_state.answers:
        st.session_state.answers[scenario_id] = {}


def render_dashboard(scenario):
    image_path = Path(scenario["image"])
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.info(f"[INSERIR DASHBOARD: {scenario['image']}]")


def render_scenario_block_a(scenario):
    sid = scenario["id"]
    ensure_scenario_answer(sid)

    st.header(f"{scenario['label']} — Bloco A: Modelo Humano")
    render_dashboard(scenario)

    hum_decision_initial = st.radio(
        "Qual seria a sua decisão para a próxima sessão de mercado?",
        DECISIONS,
        horizontal=True,
        key=f"{sid}_hum_decision_initial"
    )

    hum_confidence_initial = scale_question(
        "Qual o grau de confiança na sua decisão inicial?",
        f"{sid}_hum_confidence_initial",
        "Muito baixa",
        "Muito elevada"
    )

    hum_main_factor = st.radio(
        "Qual o principal fator que influenciou a sua decisão?",
        MAIN_FACTORS,
        key=f"{sid}_hum_main_factor"
    )

    hum_risk_perceived = scale_question(
        "Como classifica o risco deste cenário?",
        f"{sid}_hum_risk_perceived",
        "Muito baixo",
        "Muito elevado"
    )

    st.info("A recomendação da IA será apresentada apenas na próxima etapa.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Guardar e continuar"):
            st.session_state.answers[sid].update({
                "scenario_id": sid,
                "scenario_label": scenario["label"],
                "hum_decision_initial": hum_decision_initial,
                "hum_confidence_initial": hum_confidence_initial,
                "hum_main_factor": hum_main_factor,
                "hum_risk_perceived": hum_risk_perceived,
            })
            next_page()


def render_scenario_block_b(scenario):
    sid = scenario["id"]
    ensure_scenario_answer(sid)

    st.header(f"{scenario['label']} — Bloco B: Modelo IA")

    st.markdown(
        f"""
        **Sinal da IA:** {scenario["ai_signal"]}  
        **Confiança do modelo:** {scenario["ai_confidence"]}  
        **Principais fatores:** {", ".join(scenario["ai_factors"])}
        """
    )

    ia_agreement = scale_question(
        "Antes de observar a explicação da IA, qual o grau de concordância com a recomendação apresentada?",
        f"{sid}_ia_agreement",
        "Discordância total",
        "Concordância total"
    )

    ia_trust = scale_question(
        "Qual o grau de confiança que deposita nesta recomendação da IA?",
        f"{sid}_ia_trust",
        "Nenhuma confiança",
        "Confiança muito elevada"
    )

    ia_explainability = scale_question(
        "Os fatores apresentados pela IA ajudaram a compreender a recomendação?",
        f"{sid}_ia_explainability",
        "Nada",
        "Muito"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Guardar e continuar"):
            st.session_state.answers[sid].update({
                "ai_signal": scenario["ai_signal"],
                "ai_confidence": scenario["ai_confidence"],
                "ai_factors": "; ".join(scenario["ai_factors"]),
                "ia_agreement": ia_agreement,
                "ia_trust": ia_trust,
                "ia_explainability": ia_explainability,
            })
            next_page()


def render_scenario_block_c(scenario):
    sid = scenario["id"]
    ensure_scenario_answer(sid)

    st.header(f"{scenario['label']} — Bloco C: Modelo Híbrido")

    previous_decision = st.session_state.answers[sid].get("hum_decision_initial", "não registada")
    st.caption(f"Decisão inicial registada no Bloco A: {previous_decision}")

    hyb_change = st.radio(
        "Após observar a recomendação da IA pretende:",
        ["Manter a decisão inicial", "Alterar a decisão inicial"],
        key=f"{sid}_hyb_change"
    )

    hyb_decision_final = st.radio(
        "Qual é a sua decisão final?",
        DECISIONS,
        horizontal=True,
        key=f"{sid}_hyb_decision_final"
    )

    hyb_influence = scale_question(
        "Em que medida a IA influenciou a sua decisão final?",
        f"{sid}_hyb_influence",
        "Nenhuma influência",
        "Influência muito elevada"
    )

    hyb_confidence_final = scale_question(
        "Qual o grau de confiança na sua decisão final?",
        f"{sid}_hyb_confidence_final",
        "Muito baixa",
        "Muito elevada"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Guardar e continuar"):
            initial_decision = st.session_state.answers[sid].get("hum_decision_initial")
            initial_confidence = st.session_state.answers[sid].get("hum_confidence_initial")

            st.session_state.answers[sid].update({
                "hyb_change": hyb_change,
                "hyb_decision_final": hyb_decision_final,
                "hyb_influence": hyb_influence,
                "hyb_confidence_final": hyb_confidence_final,
                "decision_changed": int(initial_decision != hyb_decision_final),
                "confidence_change": hyb_confidence_final - initial_confidence
            })
            next_page()


def render_final_questions():
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
        ["Nunca", "Poucas vezes", "Algumas vezes", "Muitas vezes", "Sempre"],
        key="final_04"
    )

    final_05 = st.radio(
        "FINAL_05 — Em quantos cenários acredita ter tomado a decisão correta?",
        ["0–25%", "26–50%", "51–75%", "76–100%"],
        key="final_05"
    )

    final_06 = scale_question(
        "FINAL_06 — Em contexto real de investimento, estaria disposto a utilizar recomendações geradas por IA?",
        "final_06",
        "Nunca",
        "Sempre"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar"):
            previous_page()

    with col2:
        if st.button("Submeter respostas"):
            st.session_state.final_answers.update({
                "final_01_difficulty": final_01,
                "final_02_general_confidence": final_02,
                "final_03_ai_usefulness": final_03,
                "final_04_ai_revision_frequency": final_04,
                "final_05_perceived_correctness": final_05,
                "final_06_willingness_to_use_ai": final_06
            })
            submit_all_answers()


def submit_all_answers():
    scenarios = load_scenarios()
    finished_at = datetime.now().isoformat(timespec="seconds")

    rows = []

    for scenario in scenarios:
        sid = scenario["id"]
        answer = st.session_state.answers.get(sid, {})

        row = {
            "participant_id": st.session_state.participant_id,
            "started_at": st.session_state.started_at,
            "finished_at": finished_at,
            "consentimento": st.session_state.profile.get("consentimento"),
            "perfil_01": st.session_state.profile.get("perfil_01"),
            "perfil_02": st.session_state.profile.get("perfil_02"),
            "perfil_03": st.session_state.profile.get("perfil_03"),
            "perfil_04": st.session_state.profile.get("perfil_04"),
            "perfil_05": st.session_state.profile.get("perfil_05"),

            "scenario_id": answer.get("scenario_id", sid),
            "scenario_label": answer.get("scenario_label", scenario["label"]),

            "hum_decision_initial": answer.get("hum_decision_initial"),
            "hum_confidence_initial": answer.get("hum_confidence_initial"),
            "hum_main_factor": answer.get("hum_main_factor"),
            "hum_risk_perceived": answer.get("hum_risk_perceived"),

            "ai_signal": answer.get("ai_signal", scenario["ai_signal"]),
            "ai_confidence": answer.get("ai_confidence", scenario["ai_confidence"]),
            "ai_factors": answer.get("ai_factors", "; ".join(scenario["ai_factors"])),

            "ia_agreement": answer.get("ia_agreement"),
            "ia_trust": answer.get("ia_trust"),
            "ia_explainability": answer.get("ia_explainability"),

            "hyb_change": answer.get("hyb_change"),
            "hyb_decision_final": answer.get("hyb_decision_final"),
            "hyb_influence": answer.get("hyb_influence"),
            "hyb_confidence_final": answer.get("hyb_confidence_final"),

            "decision_changed": answer.get("decision_changed"),
            "confidence_change": answer.get("confidence_change"),
        }

        row.update(st.session_state.final_answers)
        rows.append(row)

    try:
        save_rows_to_supabase(rows)
        st.session_state.submitted = True
        st.success("Obrigado. As suas respostas foram registadas com sucesso.")
        st.balloons()
    except Exception as error:
        st.error("Ocorreu um erro ao gravar as respostas. Por favor, contacte o investigador responsável.")
        st.exception(error)


def main():
    init_state()

    if st.session_state.submitted:
        st.success("As suas respostas já foram registadas. Obrigado pela participação.")
        return

    scenarios = load_scenarios()

    total_pages = 3 + (len(scenarios) * 3) + 1
    show_progress(total_pages)

    page = st.session_state.page

    if page == 0:
        render_consent()
    elif page == 1:
        render_profile()
    elif page == 2:
        render_instructions()
    else:
        scenario_pages_start = 3
        scenario_pages_total = len(scenarios) * 3
        final_page = scenario_pages_start + scenario_pages_total

        if page == final_page:
            render_final_questions()
        elif page > final_page:
            st.success("Questionário concluído.")
        else:
            relative_page = page - scenario_pages_start
            scenario_index = relative_page // 3
            block_index = relative_page % 3

            scenario = scenarios[scenario_index]

            if block_index == 0:
                render_scenario_block_a(scenario)
            elif block_index == 1:
                render_scenario_block_b(scenario)
            elif block_index == 2:
                render_scenario_block_c(scenario)


if __name__ == "__main__":
    main()