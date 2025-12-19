import streamlit as st
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Strati | Customer Success AI",
    layout="wide"
)

# ==================================================
# 🔒 SISTEMA DE LOGIN (AUTH)
# ==================================================
def check_password():
    """Retorna `True` se o usuário tiver a senha correta."""

    def password_entered():
        """Verifica se a senha digitada bate com a do cofre (secrets)."""
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Não armazena a senha na sessão
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Se já estiver logado, retorna True
    if st.session_state.get("password_correct", False):
        return True

    # Interface de Login
    st.markdown(
        """
        <style>
        .stTextInput {max-width: 300px; margin: 0 auto;}
        .stButton {max-width: 300px; margin: 0 auto; display: block;}
        </style>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.header("🔒 Acesso Restrito")
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        if st.button("Entrar"):
            password_entered()

        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Usuário ou senha incorretos")

    return False

# SE O LOGIN NÃO FOR REALIZADO, PARA O CÓDIGO AQUI
if not check_password():
    st.stop()

# ==================================================
# 🚀 APLICAÇÃO PRINCIPAL (SÓ RODA SE LOGADO)
# ==================================================

# --- LÓGICA DO MODELO ---
class CustomerHealthModel:
    def __init__(self):
        # AQUI MUDOU: Regras baseadas no Momento do Cliente (Cohort)
        self.regras_cohort = {
            'Cohort Onboarding (0-6 meses)': {
                'peso_interacao': 0.60, 'peso_tecnico': 0.20,
                'peso_nps': 0.20, 'meta_visitas_mes': 2
            },
            'Cohort Adoção (6-24 meses)': {
                'peso_interacao': 0.30, 'peso_tecnico': 0.40,
                'peso_nps': 0.30, 'meta_visitas_mes': 1
            },
            'Cohort Retenção (+2 anos)': {
                'peso_interacao': 0.20, 'peso_tecnico': 0.50,
                'peso_nps': 0.30, 'meta_visitas_mes': 0.5
            }
        }
        self.sla_target = 98.0

    def calcular_score_tecnico(self, chamados_criados, chamados_encerrados, sla_realizado):
        ratio = 1.0 if chamados_criados == 0 else chamados_encerrados / chamados_criados
        score_backlog = min(ratio, 1.0) * 100
        
        if sla_realizado >= self.sla_target:
            score_sla = 100
        else:
            score_sla = ((sla_realizado / self.sla_target) ** 5) * 100
        
        return (score_sla * 0.70) + (score_backlog * 0.30)

    def calcular_score_interacao(self, cohort, visitas, status_book, qbr_entregue, reunioes_online):
        regras = self.regras_cohort[cohort]
        meta_visitas = regras['meta_visitas_mes']
        
        if meta_visitas > 0:
            atingimento_visitas = visitas / meta_visitas
        else:
            atingimento_visitas = 1.0 if visitas == 0 else 1.2
        
        score_visitas = min(atingimento_visitas * 100, 100.0)

        if status_book == 'Apresentado': pts_book = 100
        elif status_book == 'Enviado': pts_book = 50
        else: pts_book = 0
            
        pts_qbr = 100 if qbr_entregue == 'Sim' else 0 
        
        score_estrategico = (pts_book + pts_qbr) / 2
        bonus_online = min(reunioes_online * 2, 10)

        final_interacao = (score_visitas * 0.50) + (score_estrategico * 0.50) + bonus_online
        return min(final_interacao, 100.0)

    def analisar_cliente(self, dados):
        cohort = dados['cohort']
        regras = self.regras_cohort[cohort]
        score_nps = dados['nps'] * 10
        
        score_interacao = self.calcular_score_interacao(
            cohort, dados['visitas_presenciais'], dados['status_book'],
            dados['qbr_entregue'], dados['reunioes_online']
        )
        score_tecnico = self.calcular_score_tecnico(
            dados['chamados_criados'], dados['chamados_encerrados'], dados['sla_realizado']
        )
        
        final_score = (score_interacao * regras['peso_interacao']) + \
                      (score_tecnico * regras['peso_tecnico']) + \
                      (score_nps * regras['peso_nps'])
        
        cor_status = "green"
        texto_status = "SAUDÁVEL"
        acao = "✅ Manter estratégia da safra."

        if final_score < 60:
            cor_status = "red"
            texto_status = "CRÍTICO"
            motivos = []
            if dados['sla_realizado'] < 98: motivos.append("Quebra de SLA")
            if dados['status_book'] != 'Apresentado': motivos.append("Book não apresentado")
            if 'Onboarding' in cohort and score_interacao < 70: motivos.append("Baixa Adoção Inicial")
            acao = f"🚨 **RISCO DE CHURN NA COHORT**\n\nFoco: {', '.join(motivos)}."
        elif final_score < 75:
            cor_status = "orange"
            texto_status = "ATENÇÃO"
            acao = "⚠️ Agendar call de revisão."

        return {
            "Score": round(final_score, 1),
            "Status": texto_status, "Acao": acao,
            "Tec": int(score_tecnico), "Int": int(score_interacao), "NPS": int(score_nps),
            "Cor": cor_status
        }

# --- SIDEBAR ---
with st.sidebar:
    try:
        if os.path.exists("Logo Strati.png"): st.image("Logo Strati.png", use_column_width=True)
        elif os.path.exists("strati_logo.png"): st.image("strati_logo.png", use_column_width=True)
        else: st.header("STRATI")
    except: st.header("STRATI")
        
    st.write("") 
    st.header("📋 Dados do Cliente")
    nome = st.text_input("Nome da Empresa", placeholder="Digite o nome...")
    
    cohort = st.selectbox("Cohort (Safra/Fase)", [
        "Cohort Onboarding (0-6 meses)", 
        "Cohort Adoção (6-24 meses)", 
        "Cohort Retenção (+2 anos)"
    ])
    
    st.divider()
    st.header("⚙️ Métricas")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0, step=0.1)
    col1, col2 = st.columns(2)
    chamados_in = col1.number_input("Abertos", 0, value=10)
    chamados_out = col2.number_input("Fechados", 0, value=10)
    
    st.markdown("---")
    st.caption("© Strati - CS Intelligence")
    
    # Botão de Logout
    if st.button("Sair / Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ Calculadora CS (Segura)")
st.markdown(f"Análise de Saúde: **{nome if nome else 'Novo Cliente'}** | Fase: **{cohort}**")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("🤝 Interação")
        visitas = st.slider("Visitas Presenciais", 0, 5, 1)
        online = st.slider("Reuniões Online", 0, 10, 2)
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        qbr = st.radio("QBR Entregue?", ["Sim", "Não"], horizontal=True)

with col2:
    with st.container(border=True):
        st.subheader("❤️ NPS")
        st.write("")
        nps = st.slider("Nota (0-10)", 0, 10, 9)
        st.info("Peso do NPS varia conforme a maturidade da Cohort.")

st.write("")
if st.button("CALCULAR HEALTH SCORE", use_container_width=True, type="primary"):
    modelo = CustomerHealthModel()
    dados = {
        'cohort': cohort, 'nps': nps, 'chamados_criados': chamados_in, 
        'chamados_encerrados': chamados_out, 'sla_realizado': sla, 
        'visitas_presenciais': visitas, 'status_book': book,
        'qbr_entregue': qbr, 'reunioes_online': online
    }
    res = modelo.analisar_cliente(dados)
    
    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1: st.metric("Health Score", f"{res['Score']} / 100", delta=res['Status'], delta_color="inverse")
    with c2: 
        if res['Cor'] == 'green': st.success(f"**Recomendação:** {res['Acao']}")
        elif res['Cor'] == 'orange': st.warning(f"**Recomendação:** {res['Acao']}")
        else: st.error(f"**Recomendação:** {res['Acao']}")

    d1, d2, d3 = st.columns(3)
    d1.metric("🔧 Técnico", f"{res['Tec']}%")
    d2.metric("🤝 Interação", f"{res['Int']}%")
    d3.metric("❤️ NPS", res['NPS'])
