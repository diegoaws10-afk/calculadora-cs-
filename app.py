import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA E TEMA VISUAL ---
st.set_page_config(
    page_title="Strati | Customer Success AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA DE CORES STRATI ---
COLOR_BLACK = "#000000"
COLOR_BLUE_DARK = "#14213d"
COLOR_YELLOW = "#ffc20e"
COLOR_GRAY_MED = "#bcbec0"
COLOR_GRAY_LIGHT = "#e6e7e8"

# Injeção de CSS para identidade visual da Strati
st.markdown(f"""
    <style>
    /* --- Sidebar --- */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_GRAY_LIGHT};
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: {COLOR_BLUE_DARK} !important;
    }}
    
    /* --- Títulos Principais --- */
    h1, h2, h3, .st-emotion-cache-10trblm {{
        color: {COLOR_BLUE_DARK} !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }}

    /* --- Botões Principais --- */
    div.stButton > button:first-child {{
        background-color: {COLOR_BLUE_DARK};
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    div.stButton > button:first-child:hover {{
        background-color: {COLOR_YELLOW};
        color: {COLOR_BLACK};
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    
    /* --- Sliders e Widgets de Input --- */
    div.stSlider > div > div > div > div {{
        background-color: {COLOR_BLUE_DARK};
    }}
    [data-testid="stTickBar"] > div {{
        background-color: {COLOR_BLUE_DARK} !important;
    }}
    [data-baseweb="radio"] > div {{
        background-color: {COLOR_BLUE_DARK} !important;
    }}

    /* --- Containers --- */
    [data-testid="stinfo-container"], [data-testid="stsuccess-container"], [data-testid="stwarning-container"], [data-testid="sterror-container"] {{
        border-radius: 8px;
        border-left-width: 6px;
    }}

    /* --- Divisórias --- */
    hr {{
        border-color: {COLOR_GRAY_MED};
    }}
    
    /* --- Estilo do Card de Resultado --- */
    .metric-container {{
        background-color: {COLOR_GRAY_LIGHT};
        border-radius: 8px;
        padding: 15px;
        border: 1px solid {COLOR_GRAY_MED};
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DO MODELO (Mantida) ---
class CustomerHealthModel:
    def __init__(self):
        self.regras_tier = {
            'Ouro': {'peso_interacao': 0.40, 'peso_tecnico': 0.40, 'peso_nps': 0.20, 'meta_visitas_mes': 1},
            'Prata': {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas_mes': 0.5},
            'Bronze': {'peso_interacao': 0.10, 'peso_tecnico': 0.60, 'peso_nps': 0.30, 'meta_visitas_mes': 0}
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

    def calcular_score_interacao(self, tier, visitas, status_book, qbr_entregue, reunioes_online):
        regras = self.regras_tier[tier]
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
        tier = dados['tier']
        regras = self.regras_tier[tier]
        score_nps = dados['nps'] * 10
        
        score_interacao = self.calcular_score_interacao(
            tier, dados['visitas_presenciais'], dados['status_book'],
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
        acao = "✅ Manter rotina de sucesso."

        if final_score < 60:
            cor_status = "red"
            texto_status = "CRÍTICO"
            motivos = []
            if dados['sla_realizado'] < 98: motivos.append("Quebra de SLA")
            if dados['status_book'] != 'Apresentado': motivos.append("Book não apresentado")
            if dados['qbr_entregue'] == 'Não' and tier == 'Ouro': motivos.append("QBR Pendente")
            acao = f"🚨 **ACIONAR PLANO DE RECUPERAÇÃO**\n\nFoco: {', '.join(motivos)}."
        elif final_score < 75:
            cor_status = "orange"
            texto_status = "ATENÇÃO"
            acao = "⚠️ Agendar call de alinhamento."

        return {
            "Score": round(final_score, 1),
            "Status": texto_status, "Acao": acao,
            "Tec": int(score_tecnico), "Int": int(score_interacao), "NPS": int(score_nps),
            "Cor": cor_status
        }

# --- SIDEBAR (LOGO E INPUTS) ---
with st.sidebar:
    # Carrega o logo da Strati
    try:
        st.image("strati_logo.png", use_column_width=True)
    except:
        st.markdown(f"<h1 style='color:{COLOR_BLUE_DARK};'>STRATI</h1>", unsafe_allow_html=True)
        st.warning("Logo 'strati_logo.png' não encontrado.")

    st.write("") # Espaçamento
    st.header("📋 Dados do Cliente")
    nome = st.text_input("Nome da Empresa", placeholder="Digite o nome...")
    tier = st.selectbox("Classificação (Tier)", ["Ouro", "Prata", "Bronze"])
    
    st.divider()
    st.header("⚙️ SLA e Chamados")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0, step=0.1)
    col1, col2 = st.columns(2)
    chamados_in = col1.number_input("Abertos", min_value=0, value=10)
    chamados_out = col2.number_input("Fechados", min_value=0, value=10)
    
    st.divider()
    st.markdown(f"<div style='text-align: center; color: {COLOR_GRAY_MED}; font-size: 12px;'>Full Service Provider<br>© Strati 2025</div>", unsafe_allow_html=True)

# --- ÁREA PRINCIPAL ---
st.title("🛡️ Calculadora Customer Success")
st.markdown(f"Diagnóstico de Saúde do Cliente **{nome if nome else ''}**")

col_form1, col_form2 = st.columns(2)

with col_form1:
    with st.container(border=True):
        st.subheader("🤝 Relacionamento")
        visitas = st.slider("Visitas Presenciais", 0, 5, 1)
        online = st.slider("Reuniões Online / Calls", 0, 10, 2)
        book = st.selectbox("Status do Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        qbr = st.radio("QBR Entregue no Trimestre?", ["Sim", "Não"], horizontal=True)

with col_form2:
    with st.container(border=True):
        st.subheader("❤️ Sentimento (NPS)")
        st.write("")
        nps = st.slider("Nota NPS (0 a 10)", 0, 10, 9)
        st.write("")
        st.info("Peso do NPS ajustado pelo Tier.")
        
    st.write("")
    calcular = st.button("CALCULAR HEALTH SCORE", use_container_width=True, type="primary")

# --- RESULTADO ---
if calcular:
    modelo = CustomerHealthModel()
    dados = {
        'tier': tier, 'nps': nps, 'chamados_criados': chamados_in, 'chamados_encerrados': chamados_out,
        'sla_realizado': sla, 'visitas_presenciais': visitas, 'status_book': book,
        'qbr_entregue': qbr, 'reunioes_online': online
    }
    res = modelo.analisar_cliente(dados)
    
    st.divider()
    
    # Cabeçalho de Resultado
    c1, c2 = st.columns([1.2, 2])
    with c1:
        st.markdown(f"""
        <div style="background-color: {COLOR_BLUE_DARK}; padding: 15px; border-radius: 8px; color: white; text-align: center;">
            <h3 style="color: white !important; margin: 0;">Health Score Final</h3>
            <h1 style="color: {COLOR_YELLOW} !important; font-size: 64px; margin: 0;">{res['Score']}</h1>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # Mostra a recomendação com a cor correspondente ao status
        if res['Cor'] == 'green':
            st.success(f"#### Status: {res['Status']}\n**Recomendação:** {res['Acao']}")
        elif res['Cor'] == 'orange':
            st.warning(f"#### Status: {res['Status']}\n**Recomendação:** {res['Acao']}")
        else:
            st.error(f"#### Status: {res['Status']}\n**Recomendação:** {res['Acao']}")

    # Cards de Detalhes
    st.write("")
    d1, d2, d3 = st.columns(3)
    with d1: st.markdown(f"<div class='metric-container'><div style='color:{COLOR_GRAY_MED};'>🔧 Score Técnico</div><h3 style='margin:0; color:{COLOR_BLUE_DARK};'>{res['Tec']}%</h3></div>", unsafe_allow_html=True)
    with d2: st.markdown(f"<div class='metric-container'><div style='color:{COLOR_GRAY_MED};'>🤝 Score Interação</div><h3 style='margin:0; color:{COLOR_BLUE_DARK};'>{res['Int']}%</h3></div>", unsafe_allow_html=True)
    with d3: st.markdown(f"<div class='metric-container'><div style='color:{COLOR_GRAY_MED};'>❤️ Score NPS</div><h3 style='margin:0; color:{COLOR_BLUE_DARK};'>{res['NPS']}</h3></div>", unsafe_allow_html=True)
