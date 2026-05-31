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
    "Intuição/Experiência",
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
    defaults = {
        "participant_id": str(uuid.uuid4()),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "page": 0,
        "submitted": False,
        "profile": {},
        "answers": {},
        "final_answers": {},
        "scenario_stage": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
        help=help_text,
    )


def show_progress(total_pages):
    current = st.session_state.page + 1
    st.progress(current / total_pages)
    st.caption(f"Etapa {current} de {total_pages}")


def ensure_scenario_state(sid):
    if sid not in st.session_state.answers:
        st.session_state.answers[sid] = {}

    if sid not in st.session_state.scenario_stage:
        st.session_state.scenario_stage[sid] = "A"


def render_dashboard(scenario):
    image_path = Path(scenario["image"])
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.info(f"[INSERIR DASHBOARD: {scenario['image']}]")


def render_summary_box(title, rows):
    st.markdown(f"### {title}")
    with st.container(border=True):
        for label, value in rows:
            st.markdown(f"**{label}:** {value}")


def render_initial_page():
    st.title("Questionário — Decisão Humana, IA e Modelo Híbrido")

    st.write(
        "Este estudo analisa decisões de investimento em cenários financeiros anonimizados, "
        "comparando decisão humana, recomendação de Inteligência Artificial e decisão final híbrida."
    )

    st.header("Parte 1 — Consentimento informado")

    st.info(
        "O presente estudo integra uma dissertação de mestrado. "
        "A participação é voluntária e os dados recolhidos serão utilizados exclusivamente "
        "para fins académicos e científicos. Não serão recolhidos dados de identificação direta, "
        "tais como nome, email, telefone, morada ou NIF. Pode interromper a participação a qualquer momento."
    )

    consentimento = st.radio(
        "Declaro que li e compreendi a informação apresentada e aceito participar voluntariamente.",
        ["Sim, aceito participar", "Não aceito participar"],
        key="consentimento",
    )

    if consentimento == "Não aceito participar":
        st.title("Participação não autorizada")
        st.success(
            "Obrigado pelo seu tempo.\n\n"
            "Como não aceitou participar, o questionário foi encerrado.\n\n"
            "Pode fechar esta janela."
        )
        st.stop()

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
            "Outro",
        ],
        key="perfil_01",
    )

    perfil_02 = st.radio(
        "Frequência com que acompanha mercados financeiros",
        ["Raramente", "Mensalmente", "Semanalmente", "Diariamente", "Várias vezes por dia"],
        key="perfil_02",
    )

    perfil_03 = st.radio(
        "Familiaridade com análise técnica",
        ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"],
        key="perfil_03",
    )

    perfil_04 = st.radio(
        "Familiaridade com Inteligência Artificial aplicada a finanças",
        ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"],
        key="perfil_04",
    )

    perfil_05 = st.radio(
        "Familiaridade com estratégias Short",
        ["Nenhuma", "Baixa", "Moderada", "Elevada"],
        key="perfil_05",
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

    if st.button("Começar cenários"):
        if consentimento != "Sim, aceito participar":
            st.warning("Para avançar é necessário aceitar participar voluntariamente no estudo.")
            st.stop()

        st.session_state.profile.update(
            {
                "consentimento": consentimento,
                "perfil_01": perfil_01,
                "perfil_02": perfil_02,
                "perfil_03": perfil_03,
                "perfil_04": perfil_04,
                "perfil_05": perfil_05,
            }
        )

        next_page()


def render_locked_block_a(ans):
    render_summary_box(
        "Bloco A — Decisão humana inicial registada",
        [
            ("Decisão inicial", ans.get("hum_decision_initial", "Não registada")),
            ("Confiança inicial", f"{ans.get('hum_confidence_initial', 'Não registada')}/7"),
            ("Fator principal", ans.get("hum_main_factor", "Não registado")),
            ("Risco percebido", f"{ans.get('hum_risk_perceived', 'Não registado')}/7"),
        ],
    )
    st.caption("O Bloco A já foi guardado e não pode ser alterado.")


def render_locked_block_b(ans, scenario):
    render_summary_box(
        "Bloco B — Recomendação da IA e avaliação registada",
        [
            ("Sinal da IA", ans.get("ai_signal", scenario["ai_signal"])),
            ("Confiança do modelo", ans.get("ai_confidence", scenario["ai_confidence"])),
            ("Principais fatores", ans.get("ai_factors", "; ".join(scenario["ai_factors"]))),
            ("Concordância com a IA", f"{ans.get('ia_agreement', 'Não registada')}/7"),
            ("Confiança na IA", f"{ans.get('ia_trust', 'Não registada')}/7"),
            ("Explicabilidade", f"{ans.get('ia_explainability', 'Não registada')}/7"),
        ],
    )
    st.caption("O Bloco B já foi guardado e não pode ser alterado.")


def render_block_a_editable(scenario):
    sid = scenario["id"]
    ans = st.session_state.answers[sid]

    st.subheader("Bloco A — Modelo Humano")
    st.warning(
        "Nesta etapa deve decidir apenas com base no dashboard apresentado. "
        "A recomendação da IA ainda não está visível."
    )

    hum_decision_initial = st.radio(
        "Qual seria a sua decisão para a próxima sessão de mercado?",
        DECISIONS,
        horizontal=True,
        key=f"{sid}_hum_decision_initial",
    )

    hum_confidence_initial = scale_question(
        "Qual o grau de confiança na sua decisão inicial?",
        f"{sid}_hum_confidence_initial",
        "Muito baixa",
        "Muito elevada",
    )

    hum_main_factor = st.radio(
        "Qual o principal fator que influenciou a sua decisão?",
        MAIN_FACTORS,
        key=f"{sid}_hum_main_factor",
    )

    hum_risk_perceived = scale_question(
        "Como classifica o risco deste cenário?",
        f"{sid}_hum_risk_perceived",
        "Muito baixo",
        "Muito elevado",
    )

    if st.button("Guardar Bloco A e mostrar Bloco B", key=f"{sid}_save_a"):
        ans.update(
            {
                "scenario_id": sid,
                "scenario_label": scenario["label"],
                "hum_decision_initial": hum_decision_initial,
                "hum_confidence_initial": hum_confidence_initial,
                "hum_main_factor": hum_main_factor,
                "hum_risk_perceived": hum_risk_perceived,
            }
        )
        st.session_state.scenario_stage[sid] = "B"
        st.rerun()


def render_block_b_editable(scenario):
    sid = scenario["id"]
    ans = st.session_state.answers[sid]

    st.subheader("Bloco B — Modelo IA")

    render_summary_box(
        "Recomendação da Inteligência Artificial",
        [
            ("Sinal da IA", scenario["ai_signal"]),
            ("Confiança do modelo", scenario["ai_confidence"]),
            ("Principais fatores", ", ".join(scenario["ai_factors"])),
        ],
    )

    ia_agreement = scale_question(
        "Antes de observar a explicação da IA, qual o grau de concordância com a recomendação apresentada?",
        f"{sid}_ia_agreement",
        "Discordância total",
        "Concordância total",
    )

    ia_trust = scale_question(
        "Qual o grau de confiança que deposita nesta recomendação da IA?",
        f"{sid}_ia_trust",
        "Nenhuma confiança",
        "Confiança muito elevada",
    )

    ia_explainability = scale_question(
        "Os fatores apresentados pela IA ajudaram a compreender a recomendação?",
        f"{sid}_ia_explainability",
        "Nada",
        "Muito",
    )

    if st.button("Guardar Bloco B e mostrar Bloco C", key=f"{sid}_save_b"):
        ans.update(
            {
                "ai_signal": scenario["ai_signal"],
                "ai_confidence": scenario["ai_confidence"],
                "ai_factors": "; ".join(scenario["ai_factors"]),
                "ia_agreement": ia_agreement,
                "ia_trust": ia_trust,
                "ia_explainability": ia_explainability,
            }
        )
        st.session_state.scenario_stage[sid] = "C"
        st.rerun()


def render_block_c_editable(scenario):
    sid = scenario["id"]
    ans = st.session_state.answers[sid]

    st.subheader("Bloco C — Modelo Híbrido")

    hyb_change = st.radio(
        "Após observar a recomendação da IA pretende:",
        ["Manter a decisão inicial", "Alterar a decisão inicial"],
        key=f"{sid}_hyb_change",
    )

    hyb_decision_final = st.radio(
        "Qual é a sua decisão final?",
        DECISIONS,
        horizontal=True,
        key=f"{sid}_hyb_decision_final",
    )

    hyb_influence = scale_question(
        "Em que medida a IA influenciou a sua decisão final?",
        f"{sid}_hyb_influence",
        "Nenhuma influência",
        "Influência muito elevada",
    )

    hyb_confidence_final = scale_question(
        "Qual o grau de confiança na sua decisão final?",
        f"{sid}_hyb_confidence_final",
        "Muito baixa",
        "Muito elevada",
    )

    if st.button("Guardar cenário e continuar", key=f"{sid}_save_c"):
        initial_decision = ans.get("hum_decision_initial")
        initial_confidence = ans.get("hum_confidence_initial")

        ans.update(
            {
                "hyb_change": hyb_change,
                "hyb_decision_final": hyb_decision_final,
                "hyb_influence": hyb_influence,
                "hyb_confidence_final": hyb_confidence_final,
                "decision_changed": int(initial_decision != hyb_decision_final),
                "confidence_change": hyb_confidence_final - initial_confidence,
            }
        )
        st.session_state.scenario_stage[sid] = "DONE"
        next_page()


def render_scenario_page(scenario):
    sid = scenario["id"]
    ensure_scenario_state(sid)

    stage = st.session_state.scenario_stage[sid]
    ans = st.session_state.answers[sid]

    st.header(scenario["label"])
    render_dashboard(scenario)

    if stage == "A":
        render_block_a_editable(scenario)

    elif stage == "B":
        render_locked_block_a(ans)
        st.divider()
        render_block_b_editable(scenario)

    elif stage == "C":
        render_locked_block_a(ans)
        st.divider()
        render_locked_block_b(ans, scenario)
        st.divider()
        render_block_c_editable(scenario)

    elif stage == "DONE":
        render_locked_block_a(ans)
        st.divider()
        render_locked_block_b(ans, scenario)
        st.divider()
        render_summary_box(
            "Bloco C — Decisão final registada",
            [
                ("Manter/Alterar", ans.get("hyb_change", "Não registado")),
                ("Decisão final", ans.get("hyb_decision_final", "Não registada")),
                ("Influência da IA", f"{ans.get('hyb_influence', 'Não registada')}/7"),
                ("Confiança final", f"{ans.get('hyb_confidence_final', 'Não registada')}/7"),
            ],
        )

        if st.button("Continuar", key=f"{sid}_continue_done"):
            next_page()

    if st.session_state.page > 1:
        if st.button("Voltar ao cenário anterior", key=f"{sid}_prev"):
            previous_page()


def render_final_questions():
    st.header("Parte 5 — Questões finais")

    final_01 = scale_question(
        "FINAL_01 — Dificuldade geral dos cenários",
        "final_01",
        "Muito baixa",
        "Muito elevada",
    )

    final_02 = scale_question(
        "FINAL_02 — Confiança geral nas suas decisões",
        "final_02",
        "Muito baixa",
        "Muito elevada",
    )

    final_03 = scale_question(
        "FINAL_03 — Utilidade percebida da IA",
        "final_03",
        "Muito baixa",
        "Muito elevada",
    )

    final_04 = st.radio(
        "FINAL_04 — Com que frequência a IA levou-o(a) a rever decisões?",
        ["Nunca", "Poucas vezes", "Algumas vezes", "Muitas vezes", "Sempre"],
        key="final_04",
    )

    final_05 = st.radio(
        "FINAL_05 — Em quantos cenários acredita ter tomado a decisão correta?",
        ["0–25%", "26–50%", "51–75%", "76–100%"],
        key="final_05",
    )

    final_06 = scale_question(
        "FINAL_06 — Em contexto real de investimento, estaria disposto a utilizar recomendações geradas por IA?",
        "final_06",
        "Nunca",
        "Sempre",
    )

    if st.button("Submeter respostas"):
        st.session_state.final_answers.update(
            {
                "final_01_difficulty": final_01,
                "final_02_general_confidence": final_02,
                "final_03_ai_usefulness": final_03,
                "final_04_ai_revision_frequency": final_04,
                "final_05_perceived_correctness": final_05,
                "final_06_willingness_to_use_ai": final_06,
            }
        )
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

    total_pages = 1 + len(scenarios) + 1
    show_progress(total_pages)

    page = st.session_state.page

    if page == 0:
        render_initial_page()

    elif 1 <= page <= len(scenarios):
        scenario = scenarios[page - 1]
        render_scenario_page(scenario)

    elif page == len(scenarios) + 1:
        render_final_questions()

    else:
        st.success("Questionário concluído.")


if __name__ == "__main__":
    main()
