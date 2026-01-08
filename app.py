import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time
import os
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Strati | CS Intelligence", layout="wide", page_icon="🛡️")

# ==================================================
# 🎨 DESIGN SYSTEM (CSS)
# ==================================================
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0b1120;
            border-right: 1px solid #334155;
        }

        h1, h2, h3 {
            font-family: 'Montserrat', sans-serif !important;
            color: #ffffff !important;
        }

        /* Glassmorphism Cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(8px);
            padding: 20px;
        }

        div.stButton > button:first-child {
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3);
        }

        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        [data-testid="stMetricLabel"] { font-size: 0.8rem; color: #94a3b8; }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: white; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ==================================================
# 🔐 SEGURANÇA
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False):
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🔐 Strati | Secure Access</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                token_mfa = st.text_input("Código Authenticator") 
                st.write("")
                submit = st.form_submit_button("ACESSAR SISTEMA")
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        secret_key = st.secrets["mfa"]["secret_key"]
                        totp = pyotp.TOTP(secret_key)
                        if totp.verify(token_mfa.replace(" ", "")):
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.rerun()
                        else:
                            st.error("Código MFA Inválido.")
                    else:
                        st.error("Credenciais inválidas.")
    return False

if not check_authentication():
    st.stop()

# ==================================================
# 💾 BANCO DE DADOS
# ==================================================
def salvar_no_banco(dados):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_atual = conn.read(worksheet="Página1", ttl=0)
        nova_linha = pd.DataFrame([dados])
        df_atualizado = pd.concat([df_atual, nova_linha], ignore_index=True)
        conn.update(worksheet="Página1", data=df_atualizado)
        return True
    except Exception as e:
        if "200" in str(e) or "Response" in str(e): return True
        else: st.error(f"Erro ao salvar: {str(e)}"); return False

# ==================================================
# 📊 GRÁFICOS AVANÇADOS (RADAR + GAUGE)
# ==================================================
def create_radar_chart(tec, interaction, nps):
    val_nps = nps if isinstance(nps, (int, float)) else (tec + interaction)/2
    categories = ['Técnico', 'Relacionamento', 'Satisfação (NPS)']
    values = [tec, interaction, val_nps]
    values += [values[0]]
    categories += [categories[0]]

    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(37, 99, 235, 0.3)',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=6, color='white')
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='#94a3b8', showline=False),
            bgcolor='rgba(0,0,0,0)', gridshape='circular'
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=220
    )
    return fig

def create_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {'font': {'size': 40, 'color': "white"}, 'suffix': "%"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "rgba(255,255,255,0.3)"}, # Ponteiro translúcido
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 60], 'color': "#ef4444"},  # Vermelho
                {'range': [60, 75], 'color': "#f97316"}, # Laranja
                {'range': [75, 100], 'color': "#22c55e"} # Verde
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)", font = {'color': "white", 'family': "Inter"}, height=200, margin=dict(l=20, r=20, t=10, b=10))
    return fig

# ==================================================
# 🧠 LÓGICA CS
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_fase = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'peso_tecnico': 0.20, 'peso_nps': 0.20, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'peso_tecnico': 0.50, 'peso_nps': 0.30, 'meta_visitas': 0.5}
        }
        self.sla_targets = {'Ouro': 99.0, 'Prata': 98.0, 'Bronze': 95.0}

    def gerar_playbook(self, status, score_tec, score_int, score_nps, localizacao):
        acoes = []
        if status in ["CRÍTICO", "ATENÇÃO"]:
            acoes.append("⚠️ **Ação Imediata:** Registrar risco no CRM.")
            if score_tec < 70:
                acoes.append("🔧 **Técnico:** Agendar War Room com suporte.")
            
            if score_int < 60:
                if localizacao == "SP (Local)":
                    acoes.append("🤝 **Relacionamento:** Agendar visita presencial urgente.")
                else:
                    acoes.append("🤝 **Relacionamento:** Agendar Call Executiva com câmera aberta.")
            
            if score_nps != "N/A" and score_nps < 70:
                acoes.append("❤️ **NPS:** Entrevista de profundidade sobre a nota.")
        else:
            acoes.append("✅ **Manutenção:** Elogiar o time do cliente.")
            if score_nps != "N/A" and score_nps >= 90:
                acoes.append("⭐ **Advocacia:** Solicitar indicação (Referral).")
            if score_int > 90:
                acoes.append("💰 **Expansão:** Avaliar oportunidade de Upsell.")
        return acoes

    def calcular(self, dados):
        regras = self.regras_fase[dados['fase']]
        sla_alvo = self.sla_targets.get(dados['tier'], 98.0)
        
        # Técnico
        ratio = 1.0 if dados['criados'] == 0 else dados['encerrados'] / dados['criados']
        score_backlog = min(ratio, 1.0) * 100
        score_sla = 100 if dados['sla'] >= sla_alvo else ((dados['sla'] / sla_alvo) ** 5) * 100
        score_tecnico = (score_sla * 0.70) + (score_backlog * 0.30)
        
        # Interação
        if dados['local'] == "SP (Local)":
            meta = regras['meta_visitas']
            score_presenca = 100 if meta == 0 else min((dados['visitas']/meta)*100, 100.0)
            bonus_online = min(dados['online']*2, 10)
        else:
            meta_online_remoto = 2 
            score_presenca = min((dados['online']/meta_online_remoto)*100, 100.0)
            bonus_online = 0 if dados['visitas'] == 0 else 10 

        qbr_pts = 100 if dados['qbr_realizado'] == 'Sim' else 0
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        score_interacao = (score_presenca*0.5) + ((book_pts + qbr_pts)/2*0.5) + bonus_online
        score_interacao = min(score_interacao, 100.0)

        # Final
        peso_nps = regras['peso_nps']
        peso_tec = regras['peso_tecnico']
        peso_int = regras['peso_interacao']
        
        if dados['nps'] is None:
            score_nps = 0
            total_peso = peso_tec + peso_int
            final = (score_interacao * (peso_int/total_peso)) + (score_tecnico * (peso_tec/total_peso))
            msg_nps = "N/A"
        else:
            score_nps = dados['nps'] * 10
            final = (score_interacao * peso_int) + (score_tecnico * peso_tec) + (score_nps * peso_nps)
            msg_nps = score_nps

        if final < 60: status, cor, icone = "CRÍTICO", "red", "🚨"
        elif final < 75: status, cor, icone = "ATENÇÃO", "orange", "⚠️"
        else: status, cor, icone = "SAUDÁVEL", "green", "✅"
        
        playbook = self.gerar_playbook(status, score_tecnico, score_interacao, msg_nps, dados['local'])
            
        return {
            "Score": round(final, 1), "Status": status, "Cor": cor, "Icone": icone,
            "Tec": int(score_tecnico), "Int": int(score_interacao), 
            "NPS": msg_nps, "Acoes": playbook
        }

# ==================================================
# 🖥️ UI PRINCIPAL
# ==================================================
with st.sidebar:
    logo_carregado = False
    possible_names = ["strati_logo.png", "Logo Strati.png", "logo.png"]
    for nome_arquivo in possible_names:
        if os.path.exists(nome_arquivo):
            st.image(nome_arquivo, use_column_width=True)
            logo_carregado = True; break
    if not logo_carregado: st.markdown("<h1>STRATI</h1>", unsafe_allow_html=True)
        
    st.write("---")
    if st.button("🚪 Encerrar Sessão"): st.session_state.clear(); st.rerun()
    
    st.markdown("### 1. Perfil")
    nome = st.text_input("Nome da Empresa", placeholder="Ex: Strati Tecnologia")
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    c1, c2 = st.columns(2)
    tier = c1.selectbox("Tier", ["Ouro", "Prata", "Bronze"])
    fase = c2.selectbox("Fase", ['Onboarding', 'Adoção', 'Retenção'])
    
    st.write("---")
    st.markdown("### 2. Métricas")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0)
    c1, c2 = st.columns(2)
    c_in = c1.number_input("Abertos", value=5)
    c_out = c2.number_input("Fechados", value=5)

st.markdown("<h1>🛡️ Calculadora CS <span style='color:#3b82f6'>Intelligence</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#94a3b8; font-size:1.1rem'>Análise de Saúde: <b>{nome if nome else 'Novo Cliente'}</b></p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("### 🤝 Relacionamento")
        if local == "SP (Local)":
            visitas = st.slider("Visitas Presenciais", 0, 5, 1)
            online = st.slider("Calls Online (Bônus)", 0, 10, 2)
        else:
            st.info("✈️ Cliente Remoto: Foco em Calls Online")
            online = st.slider("Calls Online (Meta: 2)", 0, 10, 2)
            visitas = st.slider("Visitas Presenciais", 0, 5, 0)
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        
        # --- QBR CORRIGIDA AQUI ---
        st.markdown("**QBR (Resultados)**")
        qbr_realizado = st.radio("QBR Apresentado?", ["Sim", "Não"], horizontal=True)
        if qbr_realizado == "Sim":
            qbr_freq = st.selectbox("Frequência", ["Trimestral", "Semestral", "Anual"])
        else:
            qbr_freq = "N/A"

with col2:
    with st.container(border=True):
        st.markdown("### ❤️ Satisfação (NPS)")
        tem_nps = st.toggle("Cliente respondeu NPS recente?", value=True)
        if tem_nps:
            nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
        else:
            nps_valor = None
            st.warning("⚖️ Peso redistribuído.")

st.write("")

if st.button("PROCESSAR ANÁLISE", type="primary"):
    if not nome:
        st.toast("Preencha o nome do cliente.", icon="⚠️")
    else:
        progress_text = "Analisando métricas..."
        my_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.005)
            my_bar.progress(percent_complete + 1, text=progress_text)
        my_bar.empty()

        fase_map = {'Onboarding': 'Onboarding (0-6m)', 'Adoção': 'Adoção (6-24m)', 'Retenção': 'Retenção (+2 anos)'}
        modelo = CustomerHealthModel()
        inputs = {'tier': tier, 'fase': fase_map[fase], 'local': local, 'nps': nps_valor, 'criados': c_in, 'encerrados': c_out, 'sla': sla, 'visitas': visitas, 'book': book, 'qbr_realizado': qbr_realizado, 'online': online}
        res = modelo.calcular(inputs)
        
        st.markdown("---")
        
        # --- DASHBOARD VISUAL ---
        c_radar, c_gauge = st.columns([1, 1.3])
        
        with c_radar:
            with st.container(border=True):
                st.markdown("<p style='text-align:center; color:#94a3b8'>Radar de Equilíbrio</p>", unsafe_allow_html=True)
                fig_radar = create_radar_chart(res['Tec'], res['Int'], res['NPS'])
                st.plotly_chart(fig_radar, use_container_width=True)

        with c_gauge:
            # Velocímetro (Gauge) substitui o número estático
            with st.container(border=True):
                st.markdown(f"<p style='text-align:center; margin-bottom:0'>Health Score Global</p>", unsafe_allow_html=True)
                fig_gauge = create_gauge_chart(res['Score'])
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Métricas em linha abaixo do velocímetro
                m1, m2, m3 = st.columns(3)
                m1.metric("Técnico", f"{res['Tec']}%")
                m2.metric("Relacion.", f"{res['Int']}%")
                nps_display = str(res['NPS']) if res['NPS'] != "N/A" else "N/A"
                m3.metric("NPS", nps_display)

        # Plano de Ação
        st.write("")
        with st.container(border=True):
            st.markdown(f"### 📝 Diagnóstico: {res['Status']}")
            texto_acoes = ""
            for acao in res['Acoes']:
                texto_acoes += f"{acao}\n\n"
            
            if res['Cor'] == 'green': st.success(texto_acoes, icon="✅")
            elif res['Cor'] == 'orange': st.warning(texto_acoes, icon="⚠️")
            else: st.error(texto_acoes, icon="🚩")

        nps_banco = res['NPS'] if res['NPS'] != "N/A" else ""
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Cliente": nome, "Tier": tier, "Fase": fase,
            "Local": local, "Score": res['Score'], "Status": res['Status'], 
            "Técnico": res['Tec'], "Interação": res['Int'], "NPS": nps_banco, 
            "Responsável": st.session_state.get('user_logado', 'Admin')
        }
        
        salvar_no_banco(dados_db)
