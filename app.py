import json
import uuid
from datetime import datetime
from pathlib import Path
import streamlit.components.v1 as components

import streamlit as st
from supabase import create_client, Client


st.set_page_config(
    page_title="Questionário — Decisão Humana, IA e Modelo Híbrido",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SCENARIOS_FILE = "scenarios.json"
ASSETS_DIR = Path("assets/scenarios")
SUPABASE_TABLE = "responses"

DECISIONS = ["Long", "Neutro", "Short"]
SCALE_MIN = 1
SCALE_MAX = 7
SCALE_DEFAULT = 4

PROFILE_EXPERIENCE = [
    "Sem experiência relevante",
    "Conhecimento académico",
    "Investidor particular",
    "Experiência profissional em investimento",
    "Experiência profissional em corretagem",
    "Experiência profissional em gestão de risco",
    "Outro",
]

MARKET_FREQUENCY = [
    "Raramente",
    "Mensalmente",
    "Semanalmente",
    "Diariamente",
    "Várias vezes por dia",
]

FAMILIARITY_5 = ["Nenhuma", "Baixa", "Moderada", "Elevada", "Muito elevada"]
FAMILIARITY_SHORT = ["Nenhuma", "Baixa", "Moderada", "Elevada"]

MAIN_FACTORS = [
    "Evolução recente do preço",
    "Médias móveis",
    "RSI",
    "Volume",
    "Volatilidade",
    "Combinação de fatores",
    "Intuição / Experiência pessoal",
]

REVISION_FREQUENCY = ["Nunca", "Poucas vezes", "Algumas vezes", "Muitas vezes", "Sempre"]
PERCEIVED_CORRECTNESS = ["0–25%", "26–50%", "51–75%", "76–100%"]

AI_USEFULNESS_OPTIONS = [
    "Muito úteis para melhorar a decisão",
    "Úteis como complemento analítico",
    "Moderadamente úteis",
    "Pouco úteis",
    "Não úteis",
]

AI_USEFULNESS_REASONS = [
    "Confirmaram a sua análise",
    "Apresentaram nova informação",
    "Melhoraram a avaliação de risco",
    "Ajudaram a estruturar a decisão",
    "Não acrescentaram valor relevante",
]

ADJUST_FREQUENCY = ["Frequentemente", "Algumas vezes", "Raramente", "Nunca"]
ADJUST_REASONS = [
    "Contexto de mercado não captado pelo modelo",
    "Informação qualitativa não considerada",
    "Discordância com os indicadores",
    "Gestão de risco pessoal",
    "Intuição ou experiência",
]

EXPLANATION_LIMITATIONS = [
    "Falta de detalhe técnico",
    "Complexidade excessiva",
    "Falta de ligação ao contexto",
    "Explicações demasiado abstratas",
    "Não identifiquei limitações",
]

BIAS_TYPES = [
    "Excesso de confiança",
    "Aversão à perda",
    "Ancoragem",
    "Comportamento de manada",
    "Viés de confirmação",
]

REJECTION_REASONS = [
    "Falta de confiança",
    "Falta de transparência",
    "Discordância",
    "Contexto de mercado",
    "Gestão de risco",
]

SELF_CONFIDENCE_CHANGE = [
    "Aumentou",
    "Tornou mais crítico",
    "Não alterou",
    "Gerou dependência",
    "Reduziu",
]

NEEDED_IMPROVEMENTS = [
    "Melhoria da usabilidade e clareza das explicações",
    "Aumento da capacidade analítica e adaptabilidade ao mercado",
    "Maior transparência e robustez do modelo",
]

ADOPTION_BARRIERS = [
    "Fatores psicológicos (confiança, controlo, responsabilidade)",
    "Fatores organizacionais (cultura, conhecimento, regulação)",
    "Ambos",
]

HYBRID_VALUE = [
    "Melhoria da qualidade e robustez das decisões",
    "Complemento eficaz ao julgamento humano",
    "Redução de enviesamentos e melhoria do controlo de risco",
]

HYBRID_RISKS = [
    "Dependência excessiva da IA e redução da autonomia do decisor",
    "Limitações do modelo em contextos de mercado complexos",
    "Falta de transparência ou dificuldades na interpretação das recomendações",
]

RECOMMENDATION_OPTIONS = ["Sim", "Sim, com reservas", "Talvez", "Não"]


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

def scroll_to_top():
    components.html(
        """
        <script>
        setTimeout(function() {
            try {
                const doc = window.parent.document;
                const scrollingElement = doc.scrollingElement || doc.documentElement || doc.body;

                if (scrollingElement) {
                    scrollingElement.scrollTo({ top: 0, behavior: "smooth" });
                }

                const main = doc.querySelector("section.main");
                if (main) {
                    main.scrollTo({ top: 0, behavior: "smooth" });
                }

                const app = doc.querySelector(".stApp");
                if (app) {
                    app.scrollTo({ top: 0, behavior: "smooth" });
                }

                const viewContainer = doc.querySelector("[data-testid='stAppViewContainer']");
                if (viewContainer) {
                    viewContainer.scrollTo({ top: 0, behavior: "smooth" });
                }

                const scrollableContainers = doc.querySelectorAll("[data-testid='stVerticalBlock'], [data-testid='stAppViewBlockContainer']");
                scrollableContainers.forEach(function(el) {
                    if (el && el.scrollTo) {
                        el.scrollTo({ top: 0, behavior: "smooth" });
                    }
                });
            } catch (e) {
                window.parent.scrollTo(0, 0);
            }
        }, 150);
        </script>
        """,
        height=0,
    )
@st.cache_data
def load_scenarios():
    with open(SCENARIOS_FILE, "r", encoding="utf-8") as file:
        scenarios = json.load(file)

    required_fields = [
        "id",
        "label",
        "image",
        "market_context",
        "ai_signal",
        "ai_confidence",
        "ai_summary",
        "ai_factors",
    ]

    valid_signals = {"Long", "Neutro", "Short"}
    valid_confidence = {"Baixa", "Moderada", "Elevada"}

    if not isinstance(scenarios, list):
        raise ValueError("O ficheiro scenarios.json deve conter uma lista de cenários.")

    seen_ids = set()
    for idx, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise ValueError(f"O cenário na posição {idx} não é um objeto JSON válido.")

        for field in required_fields:
            if field not in scenario:
                raise ValueError(
                    f"O cenário {scenario.get('id', idx)} não contém o campo obrigatório '{field}'."
                )

        sid = scenario.get("id")
        if sid in seen_ids:
            raise ValueError(f"ID de cenário duplicado: {sid}")
        seen_ids.add(sid)

        if scenario.get("ai_signal") not in valid_signals:
            raise ValueError(
                f"O cenário {sid} tem ai_signal inválido: {scenario.get('ai_signal')}. "
                f"Use apenas: Long, Neutro ou Short."
            )

        if scenario.get("ai_confidence") not in valid_confidence:
            raise ValueError(
                f"O cenário {sid} tem ai_confidence inválida: {scenario.get('ai_confidence')}. "
                f"Use apenas: Baixa, Moderada ou Elevada."
            )

        ai_factors = scenario.get("ai_factors")
        if not isinstance(ai_factors, list) or len(ai_factors) == 0:
            raise ValueError(f"O cenário {sid} deve ter ai_factors como lista não vazia.")

    return scenarios


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def now_dt():
    return datetime.now()


def seconds_since(start_dt):
    if not start_dt:
        return None
    return round((now_dt() - start_dt).total_seconds(), 2)


def init_state():
    defaults = {
        "participant_id": str(uuid.uuid4()),
        "started_at": now_iso(),
        "page": 0,
        "submitted": False,
        "profile": {},
        "answers": {},
        "final_answers": {},
        "scenario_stage": {},
        "scenario_timers": {},
        "block_started_at": {},
        "force_scroll_top": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def next_page():
    st.session_state.page += 1
    st.session_state.force_scroll_top = True
    st.rerun()


def previous_page():
    if st.session_state.page > 0:
        st.session_state.page -= 1
        st.session_state.force_scroll_top = True
        st.rerun()


def save_rows_to_supabase(rows):
    supabase = get_supabase_client()
    return supabase.table(SUPABASE_TABLE).insert(rows).execute()


def scale_question(label, key, low_label=None, high_label=None):
    help_text = None
    if low_label and high_label:
        help_text = f"1 = {low_label} | 7 = {high_label}"
    return st.slider(
        label,
        min_value=SCALE_MIN,
        max_value=SCALE_MAX,
        value=SCALE_DEFAULT,
        step=1,
        key=key,
        help=help_text,
    )


def radio_question(label, options, key, horizontal=False, index=None):
    return st.radio(label, options, key=key, horizontal=horizontal, index=index)


def show_progress(total_pages, scenarios_count):
    current = st.session_state.page + 1
    st.progress(min(current / total_pages, 1.0))

    page = st.session_state.page
    if 1 <= page <= scenarios_count:
        st.caption(f"Cenário {page} de {scenarios_count} · Etapa {current} de {total_pages}")
    else:
        st.caption(f"Etapa {current} de {total_pages}")


def ensure_scenario_state(scenario):
    sid = scenario["id"]
    if sid not in st.session_state.answers:
        st.session_state.answers[sid] = {}
    if sid not in st.session_state.scenario_stage:
        st.session_state.scenario_stage[sid] = "A"
    if sid not in st.session_state.scenario_timers:
        st.session_state.scenario_timers[sid] = {
            "scenario_started_at": now_iso(),
            "scenario_total_time_seconds": None,
            "block_a_time_seconds": None,
            "block_b_time_seconds": None,
            "block_c_time_seconds": None,
        }
    stage_key = f"{sid}_{st.session_state.scenario_stage[sid]}"
    if stage_key not in st.session_state.block_started_at:
        st.session_state.block_started_at[stage_key] = now_dt()


def register_block_time(sid, stage):
    stage_key = f"{sid}_{stage}"
    elapsed = seconds_since(st.session_state.block_started_at.get(stage_key))
    if stage == "A":
        st.session_state.scenario_timers[sid]["block_a_time_seconds"] = elapsed
    elif stage == "B":
        st.session_state.scenario_timers[sid]["block_b_time_seconds"] = elapsed
    elif stage == "C":
        st.session_state.scenario_timers[sid]["block_c_time_seconds"] = elapsed


def finish_scenario_timer(sid):
    start_iso = st.session_state.scenario_timers[sid].get("scenario_started_at")
    if not start_iso:
        return
    try:
        start_dt = datetime.fromisoformat(start_iso)
        st.session_state.scenario_timers[sid]["scenario_total_time_seconds"] = round(
            (now_dt() - start_dt).total_seconds(), 2
        )
    except Exception:
        st.session_state.scenario_timers[sid]["scenario_total_time_seconds"] = None


def render_dashboard(scenario):
    image_name = scenario.get("image", "")
    image_name = Path(image_name).name
    image_path = ASSETS_DIR / image_name

    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.error(f"Imagem não encontrada: {image_path}")

def render_summary_box(title, rows):
    st.markdown(f"### {title}")
    with st.container(border=True):
        for label, value in rows:
            st.markdown(f"**{label}:** {value}")


def render_ai_card(scenario):
    ai_signal = scenario.get("ai_signal", "Não definido")
    ai_confidence = scenario.get("ai_confidence", "Não definida")
    ai_summary = scenario.get("ai_summary", "")
    ai_factors = scenario.get("ai_factors", [])

    if isinstance(ai_factors, list):
        factors_text = "\n".join([f"- {factor}" for factor in ai_factors])
        factors_joined = "; ".join(ai_factors)
    else:
        factors_text = str(ai_factors)
        factors_joined = str(ai_factors)

    with st.container(border=True):
        st.markdown("### 🤖 Recomendação da Inteligência Artificial")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sinal", ai_signal)
        with col2:
            st.metric("Confiança do modelo", ai_confidence)

        if ai_summary:
            st.markdown("**Resumo da recomendação da IA**")
            st.write(ai_summary)

        st.markdown("**Principais fatores explicativos**")
        st.markdown(factors_text)

    return ai_signal, ai_confidence, ai_summary, factors_joined


def render_initial_page():
    st.title("Questionário — Decisão Humana, Inteligência Artificial e Modelo Híbrido")

    st.info(
        "Responda de forma rápida e intuitiva, sem necessidade de analisar todos os detalhes. "
        "Não existem respostas certas ou erradas; o objetivo é compreender o processo de decisão."
    )

    st.header("Parte 1 — Consentimento informado")
    st.write(
        "A sua participação é totalmente voluntária e os dados recolhidos serão utilizados exclusivamente "
        "para fins científicos e académicos. Não serão recolhidos dados de identificação pessoal."
    )

    consentimento = radio_question(
        "Declara que leu e compreendeu a informação apresentada e aceita participar voluntariamente neste estudo?",
        ["Sim, aceito participar", "Não aceito participar"],
        key="consentimento",
        index=None,
    )

    if consentimento == "Não aceito participar":
        st.title("Participação não autorizada")
        st.success(
            "Obrigado pelo seu tempo. Como não aceitou participar, o questionário foi encerrado."
        )
        st.stop()

    st.header("Parte 2 — Caracterização do participante")
    st.caption("Para efeitos estatísticos, pedimos que indique algumas informações sobre o seu perfil.")

    perfil_01 = radio_question(
        "1. Qual é o seu nível de experiência em mercados financeiros?",
        PROFILE_EXPERIENCE,
        key="perfil_01",
        index=None,
    )

    perfil_02 = radio_question(
        "2. Com que frequência acompanha os mercados financeiros?",
        MARKET_FREQUENCY,
        key="perfil_02",
        index=None,
    )

    perfil_03 = radio_question(
        "3. Como classifica a sua familiaridade com análise técnica?",
        FAMILIARITY_5,
        key="perfil_03",
        index=None,
    )

    perfil_04 = radio_question(
        "4. Qual o seu nível de familiaridade com aplicações de Inteligência Artificial em finanças?",
        FAMILIARITY_5,
        key="perfil_04",
        index=None,
    )

    perfil_05 = radio_question(
        "5. Qual o seu nível de familiaridade com estratégias de investimento em posições short?",
        FAMILIARITY_SHORT,
        key="perfil_05",
        index=None,
    )

    st.header("Parte 3 — Análise de cenários")
    st.markdown(
        """
        Ser-lhe-ão apresentados **16 cenários financeiros**, cada um representado por um dashboard com informação de mercado: preço, tendência, RSI, volume e volatilidade.

        O objetivo é tomar uma decisão para a **próxima sessão de mercado**, com base exclusivamente na informação disponível.

        Cada cenário será avaliado em três fases:

        1. **Decisão inicial** — modelo humano  
        2. **Avaliação da IA** — recomendação e fatores explicativos  
        3. **Decisão final** — modelo híbrido
        """
    )

    required = [consentimento, perfil_01, perfil_02, perfil_03, perfil_04, perfil_05]
    if st.button("Começar cenários", type="primary", use_container_width=True):
        if not all(required):
            st.warning("Por favor, responda a todas as questões de caracterização antes de avançar.")
            st.stop()
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
        "Bloco A — Decisão inicial registada",
        [
            ("Decisão inicial", ans.get("hum_decision_initial", "Não registada")),
            ("Confiança inicial", f"{ans.get('hum_confidence_initial', 'Não registada')}/7"),
            ("Fator principal", ans.get("hum_main_factor", "Não registado")),
            ("Risco percebido", f"{ans.get('hum_risk_perceived', 'Não registado')}/7"),
        ],
    )
    st.caption("Este bloco foi registado e permanece bloqueado para preservar a validade experimental.")


def render_locked_block_b(ans, scenario):
    render_summary_box(
        "Bloco B — Avaliação da IA registada",
        [
            ("Sinal da IA", ans.get("ai_signal", scenario.get("ai_signal", "Não definido"))),
            ("Confiança do modelo", ans.get("ai_confidence", scenario.get("ai_confidence", "Não definida"))),
            ("Resumo da IA", ans.get("ai_summary", scenario.get("ai_summary", "Não registado"))),
            ("Principais fatores", ans.get("ai_factors", "; ".join(scenario.get("ai_factors", [])))),
            ("Concordância com a IA", f"{ans.get('ia_agreement', 'Não registada')}/7"),
            ("Confiança na IA", f"{ans.get('ia_trust', 'Não registada')}/7"),
            ("Compreensão dos fatores", f"{ans.get('ia_explainability', 'Não registada')}/7"),
        ],
    )
    st.caption("Este bloco foi registado e permanece bloqueado para preservar a validade experimental.")


def render_block_a_editable(scenario):
    sid = scenario["id"]
    ans = st.session_state.answers[sid]

    st.subheader("Bloco A — Decisão Inicial (Modelo Humano)")
    st.warning(
        "Nesta fase, responda apenas com base no dashboard. A recomendação da IA ainda não está visível."
    )

    hum_decision_initial = radio_question(
        "1. Qual seria a sua decisão para a próxima sessão de mercado?",
        DECISIONS,
        key=f"{sid}_hum_decision_initial",
        horizontal=True,
        index=None,
    )

    hum_confidence_initial = scale_question(
        "2. Qual o grau de confiança na sua decisão inicial?",
        f"{sid}_hum_confidence_initial",
        "muito baixa",
        "muito elevada",
    )

    hum_main_factor = radio_question(
        "3. Qual o principal fator que influenciou a sua decisão?",
        MAIN_FACTORS,
        key=f"{sid}_hum_main_factor",
        index=None,
    )

    hum_risk_perceived = scale_question(
        "4. Como classifica o risco deste cenário?",
        f"{sid}_hum_risk_perceived",
        "muito baixo",
        "muito elevado",
    )

    can_advance = hum_decision_initial is not None and hum_main_factor is not None
    if st.button("Avançar para avaliação da IA", type="primary", use_container_width=True, disabled=not can_advance):
        register_block_time(sid, "A")
        ans.update(
            {
                "scenario_id": sid,
                "scenario_label": scenario.get("label"),
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

    st.subheader("Bloco B — Avaliação da IA")
    ai_signal, ai_confidence, ai_summary, ai_factors = render_ai_card(scenario)

    ia_agreement = scale_question(
        "1. Qual o grau de concordância com a recomendação da IA?",
        f"{sid}_ia_agreement",
        "discordância total",
        "concordância total",
    )

    ia_trust = scale_question(
        "2. Qual o nível de confiança na recomendação da IA?",
        f"{sid}_ia_trust",
        "nenhuma confiança",
        "confiança muito elevada",
    )

    ia_explainability = scale_question(
        "3. Os fatores apresentados pela IA ajudaram a compreender a recomendação?",
        f"{sid}_ia_explainability",
        "não ajudou nada a compreender",
        "ajudou totalmente a compreender",
    )

    if st.button("Avançar para decisão final", type="primary", use_container_width=True):
        register_block_time(sid, "B")
        ans.update(
            {
                "ai_signal": ai_signal,
                "ai_confidence": ai_confidence,
                "ai_summary": ai_summary,
                "ai_factors": ai_factors,
                "market_context": scenario.get("market_context"),
                "ia_agreement": ia_agreement,
                "ia_trust": ia_trust,
                "ia_explainability": ia_explainability,
            }
        )
        st.session_state.scenario_stage[sid] = "C"
        st.rerun()


def transition_code(initial_decision, final_decision):
    if not initial_decision or not final_decision:
        return None
    return f"{initial_decision.lower()}_to_{final_decision.lower()}".replace(" ", "_")


def render_block_c_editable(scenario):
    sid = scenario["id"]
    ans = st.session_state.answers[sid]

    st.subheader("Bloco C — Decisão final (Modelo Híbrido)")

    hyb_change = radio_question(
        "1. Após observar a IA pretende:",
        ["Manter a decisão inicial", "Alterar a decisão inicial"],
        key=f"{sid}_hyb_change",
        index=None,
    )

    hyb_decision_final = radio_question(
        "2. Qual é a sua decisão final?",
        DECISIONS,
        key=f"{sid}_hyb_decision_final",
        horizontal=True,
        index=None,
    )

    hyb_influence = scale_question(
        "3. Em que medida a IA influenciou a sua decisão final?",
        f"{sid}_hyb_influence",
        "nenhuma influência",
        "influência muito elevada",
    )

    hyb_confidence_final = scale_question(
        "4. Qual o grau de confiança na sua decisão final?",
        f"{sid}_hyb_confidence_final",
        "muito baixa confiança",
        "muito elevada confiança",
    )

    can_advance = hyb_change is not None and hyb_decision_final is not None
    if st.button("Concluir cenário", type="primary", use_container_width=True, disabled=not can_advance):
        register_block_time(sid, "C")
        finish_scenario_timer(sid)

        initial_decision = ans.get("hum_decision_initial")
        initial_confidence = ans.get("hum_confidence_initial")
        ai_signal = ans.get("ai_signal")

        decision_changed = int(initial_decision != hyb_decision_final)
        ai_agreed_with_human = int(ai_signal == initial_decision) if ai_signal and initial_decision else None
        human_followed_ai_final = int(ai_signal == hyb_decision_final) if ai_signal and hyb_decision_final else None

        ans.update(
            {
                "hyb_change": hyb_change,
                "hyb_decision_final": hyb_decision_final,
                "hyb_influence": hyb_influence,
                "hyb_confidence_final": hyb_confidence_final,
                "decision_changed": decision_changed,
                "confidence_change": hyb_confidence_final - initial_confidence if initial_confidence is not None else None,
                "decision_transition": transition_code(initial_decision, hyb_decision_final),
                "ai_agreed_with_human": ai_agreed_with_human,
                "human_followed_ai_final": human_followed_ai_final,
            }
        )
        st.session_state.scenario_stage[sid] = "DONE"
        next_page()


def render_scenario_page(scenario):
    scroll_to_top()
    ensure_scenario_state(scenario)
    sid = scenario["id"]
    stage = st.session_state.scenario_stage[sid]
    ans = st.session_state.answers[sid]

    st.header(scenario.get("label", f"Cenário {sid}"))
    st.caption("Horizonte de decisão: próxima sessão de mercado.")

    market_context = scenario.get("market_context")
    if market_context:
        with st.container(border=True):
            st.markdown("### Contexto de mercado")
            st.write(market_context)

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
        if st.button("Continuar", type="primary", use_container_width=True):
            next_page()

    if st.session_state.page > 1:
        with st.expander("Navegação"):
            if st.button("Voltar ao cenário anterior", key=f"{sid}_prev"):
                previous_page()


def save_final_answers(updates):
    st.session_state.final_answers.update(updates)
    next_page()


def render_part_4_general():
    st.header("Parte 4 — Avaliação geral")

    general_difficulty = scale_question(
        "1. Como classifica a dificuldade geral dos cenários apresentados?",
        "general_difficulty",
        "muito baixa dificuldade",
        "muito elevada dificuldade",
    )

    ai_revision_frequency = radio_question(
        "2. Frequência com que a IA levou à revisão de decisões:",
        REVISION_FREQUENCY,
        key="ai_revision_frequency",
        index=None,
    )

    perceived_correctness = radio_question(
        "3. Em quantos cenários acredita ter tomado a decisão correta?",
        PERCEIVED_CORRECTNESS,
        key="perceived_correctness",
        index=None,
    )

    real_use_willingness = scale_question(
        "4. Disponibilidade para utilização de IA em contexto real:",
        "real_use_willingness",
        "nunca utilizaria",
        "utilizaria sempre",
    )

    can_advance = ai_revision_frequency is not None and perceived_correctness is not None
    if st.button("Avançar", type="primary", use_container_width=True, disabled=not can_advance):
        save_final_answers(
            {
                "general_difficulty": general_difficulty,
                "ai_revision_frequency": ai_revision_frequency,
                "perceived_correctness": perceived_correctness,
                "real_use_willingness": real_use_willingness,
            }
        )


def render_part_5_utility():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Utilidade e Interação com a IA")

    ai_usefulness = radio_question(
        "1. De forma geral, como avalia a utilidade das recomendações da IA?",
        AI_USEFULNESS_OPTIONS,
        key="ai_usefulness",
        index=None,
    )

    ai_usefulness_reason = radio_question(
        "2. Qual o principal motivo dessa avaliação?",
        AI_USEFULNESS_REASONS,
        key="ai_usefulness_reason",
        index=None,
    )

    adjust_ai_frequency = radio_question(
        "3. Sentiu necessidade de ajustar as recomendações da IA?",
        ADJUST_FREQUENCY,
        key="adjust_ai_frequency",
        index=None,
    )

    adjust_ai_reason = None
    if adjust_ai_frequency and adjust_ai_frequency != "Nunca":
        adjust_ai_reason = radio_question(
            "Se sim, qual foi o principal motivo?",
            ADJUST_REASONS,
            key="adjust_ai_reason",
            index=None,
        )

    can_advance = ai_usefulness and ai_usefulness_reason and adjust_ai_frequency
    if adjust_ai_frequency != "Nunca":
        can_advance = can_advance and adjust_ai_reason

    if st.button("Avançar", type="primary", use_container_width=True, disabled=not can_advance):
        save_final_answers(
            {
                "ai_usefulness": ai_usefulness,
                "ai_usefulness_reason": ai_usefulness_reason,
                "adjust_ai_frequency": adjust_ai_frequency,
                "adjust_ai_reason": adjust_ai_reason,
            }
        )


def render_part_5_explainability():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Explicabilidade da IA")

    explanation_clarity = scale_question(
        "1. Como avalia a clareza das explicações fornecidas pela IA?",
        "explanation_clarity",
        "muito difícil de compreender",
        "muito clara e intuitiva",
    )

    explanation_understanding = scale_question(
        "2. Em que medida essas explicações ajudaram a compreender a recomendação?",
        "explanation_understanding",
        "não ajudou nada",
        "permitiu compreender totalmente",
    )

    explanation_confidence_effect = scale_question(
        "3. As explicações aumentaram a sua confiança no modelo?",
        "explanation_confidence_effect",
        "reduziu significativamente a confiança",
        "aumentou significativamente a confiança",
    )

    explanation_limitations = radio_question(
        "4. Identificou limitações nas explicações?",
        EXPLANATION_LIMITATIONS,
        key="explanation_limitations",
        index=None,
    )

    if st.button("Avançar", type="primary", use_container_width=True, disabled=not explanation_limitations):
        save_final_answers(
            {
                "explanation_clarity": explanation_clarity,
                "explanation_understanding": explanation_understanding,
                "explanation_confidence_effect": explanation_confidence_effect,
                "explanation_limitations": explanation_limitations,
            }
        )


def render_part_5_biases():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Mitigação de Vieses")

    bias_identification = radio_question(
        "1. A interação com a IA ajudou-o(a) a identificar possíveis enviesamentos nas suas decisões?",
        ["Sim", "Não"],
        key="bias_identification",
        horizontal=True,
        index=None,
    )

    bias_types_identified = []
    if bias_identification == "Sim":
        bias_types_identified = st.multiselect(
            "Principais vieses identificados:",
            BIAS_TYPES,
            key="bias_types_identified",
        )

    bias_reduction = scale_question(
        "2. O modelo híbrido contribuiu para reduzir enviesamentos?",
        "bias_reduction",
        "nenhuma redução",
        "redução muito significativa",
    )

    can_advance = bias_identification is not None
    if bias_identification == "Sim":
        can_advance = len(bias_types_identified) > 0

    if st.button("Avançar", type="primary", use_container_width=True, disabled=not can_advance):
        save_final_answers(
            {
                "bias_identification": bias_identification,
                "bias_types_identified": "; ".join(bias_types_identified),
                "bias_reduction": bias_reduction,
            }
        )


def render_part_5_trust():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Confiança e Aceitação")

    rejected_ai = radio_question(
        "1. Houve situações em que rejeitou a IA?",
        ["Sim", "Não"],
        key="rejected_ai",
        horizontal=True,
        index=None,
    )

    rejection_reason = None
    if rejected_ai == "Sim":
        rejection_reason = radio_question(
            "Se sim, porquê?",
            REJECTION_REASONS,
            key="rejection_reason",
            index=None,
        )

    self_confidence_change = radio_question(
        "2. O modelo híbrido alterou o seu nível de confiança no próprio julgamento?",
        SELF_CONFIDENCE_CHANGE,
        key="self_confidence_change",
        index=None,
    )

    can_advance = rejected_ai is not None and self_confidence_change is not None
    if rejected_ai == "Sim":
        can_advance = can_advance and rejection_reason is not None

    if st.button("Avançar", type="primary", use_container_width=True, disabled=not can_advance):
        save_final_answers(
            {
                "rejected_ai": rejected_ai,
                "rejection_reason": rejection_reason,
                "self_confidence_change": self_confidence_change,
            }
        )


def render_part_5_viability():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Viabilidade e Barreiras")

    hybrid_viability = scale_question(
        "1. Considera o modelo híbrido viável em contexto real?",
        "hybrid_viability",
        "totalmente inviável",
        "totalmente viável",
    )

    needed_improvements = st.multiselect(
        "2. Que melhorias considera necessárias?",
        NEEDED_IMPROVEMENTS,
        key="needed_improvements",
    )

    adoption_barriers = radio_question(
        "3. Que fatores podem constituir barreiras à adoção?",
        ADOPTION_BARRIERS,
        key="adoption_barriers",
        index=None,
    )

    can_advance = len(needed_improvements) > 0 and adoption_barriers is not None
    if st.button("Avançar", type="primary", use_container_width=True, disabled=not can_advance):
        save_final_answers(
            {
                "hybrid_viability": hybrid_viability,
                "needed_improvements": "; ".join(needed_improvements),
                "adoption_barriers": adoption_barriers,
            }
        )


def render_part_5_final():
    st.header("Parte 5 — Avaliação complementar")
    st.subheader("Avaliação Final")

    hybrid_value = radio_question(
        "1. Qual o principal valor do modelo híbrido?",
        HYBRID_VALUE,
        key="hybrid_value",
        index=None,
    )

    hybrid_risk = radio_question(
        "2. Quais os principais riscos associados?",
        HYBRID_RISKS,
        key="hybrid_risk",
        index=None,
    )

    recommendation = radio_question(
        "3. Recomendaria este sistema a outros analistas?",
        RECOMMENDATION_OPTIONS,
        key="recommendation",
        index=None,
    )

    final_comment = st.text_area(
        "4. Comentário adicional (opcional)",
        key="final_comment",
        placeholder="Poderá partilhar a sua opinião sobre utilidade, limitações, influência na decisão ou sugestões de melhoria.",
    )

    can_submit = hybrid_value is not None and hybrid_risk is not None and recommendation is not None
    if st.button("Submeter respostas", type="primary", use_container_width=True, disabled=not can_submit):
        st.session_state.final_answers.update(
            {
                "hybrid_value": hybrid_value,
                "hybrid_risk": hybrid_risk,
                "recommendation": recommendation,
                "final_comment": final_comment,
            }
        )
        submit_all_answers()


def submit_all_answers():
    scenarios = load_scenarios()
    finished_at = now_iso()
    rows = []

    for scenario in scenarios:
        sid = scenario["id"]
        answer = st.session_state.answers.get(sid, {})
        timers = st.session_state.scenario_timers.get(sid, {})

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
            "scenario_label": answer.get("scenario_label", scenario.get("label")),
            "hum_decision_initial": answer.get("hum_decision_initial"),
            "hum_confidence_initial": answer.get("hum_confidence_initial"),
            "hum_main_factor": answer.get("hum_main_factor"),
            "hum_risk_perceived": answer.get("hum_risk_perceived"),
            "ai_signal": answer.get("ai_signal", scenario.get("ai_signal")),
            "ai_confidence": answer.get("ai_confidence", scenario.get("ai_confidence")),
            "ai_summary": answer.get("ai_summary", scenario.get("ai_summary")),
            "ai_factors": answer.get("ai_factors", "; ".join(scenario.get("ai_factors", []))),
            "market_context": answer.get("market_context", scenario.get("market_context")),
            "ia_agreement": answer.get("ia_agreement"),
            "ia_trust": answer.get("ia_trust"),
            "ia_explainability": answer.get("ia_explainability"),
            "hyb_change": answer.get("hyb_change"),
            "hyb_decision_final": answer.get("hyb_decision_final"),
            "hyb_influence": answer.get("hyb_influence"),
            "hyb_confidence_final": answer.get("hyb_confidence_final"),
            "decision_changed": answer.get("decision_changed"),
            "confidence_change": answer.get("confidence_change"),
            "decision_transition": answer.get("decision_transition"),
            "ai_agreed_with_human": answer.get("ai_agreed_with_human"),
            "human_followed_ai_final": answer.get("human_followed_ai_final"),
            "scenario_started_at": timers.get("scenario_started_at"),
            "scenario_total_time_seconds": timers.get("scenario_total_time_seconds"),
            "block_a_time_seconds": timers.get("block_a_time_seconds"),
            "block_b_time_seconds": timers.get("block_b_time_seconds"),
            "block_c_time_seconds": timers.get("block_c_time_seconds"),
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

    if st.session_state.get("force_scroll_top"):
        scroll_to_top()
        st.session_state.force_scroll_top = False

    if st.session_state.submitted:
        st.success("As suas respostas já foram registadas. Obrigado pela participação.")
        return

    scenarios = load_scenarios()
    scenarios_count = len(scenarios)
    final_sections = 7
    total_pages = 1 + scenarios_count + final_sections
    show_progress(total_pages, scenarios_count)

    page = st.session_state.page

    if page == 0:
        render_initial_page()
    elif 1 <= page <= scenarios_count:
        scenario = scenarios[page - 1]
        render_scenario_page(scenario)
    else:
        final_page = page - scenarios_count
        if final_page == 1:
            render_part_4_general()
        elif final_page == 2:
            render_part_5_utility()
        elif final_page == 3:
            render_part_5_explainability()
        elif final_page == 4:
            render_part_5_biases()
        elif final_page == 5:
            render_part_5_trust()
        elif final_page == 6:
            render_part_5_viability()
        elif final_page == 7:
            render_part_5_final()
        else:
            st.success("Questionário concluído.")


if __name__ == "__main__":
    main()
