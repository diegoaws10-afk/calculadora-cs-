import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time
import os
import plotly.graph_objects as go
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Strati | CS Intelligence AI", layout="wide", page_icon="🛡️")

# --- CONFIGURAÇÃO GEMINI AI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro ao configurar API do Gemini. Verifique os Secrets.")

# ==================================================
# 🎨 DESIGN SYSTEM (STRATI OFFICIAL PALETTE)
# ==================================================
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        .stApp {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(-45deg, #1A1A1A, #000000, #1A1A1A, #262626);
            background-size: 400% 400%;
            color: #f8fafc;
        }

        [data-testid="stSidebar"] {
            background-color: rgba(11, 13, 25, 0.95);
            border-right: 1px solid #262626;
        }

        /* Títulos Laranja Strati */
        h1, h2, h3 { font-family: 'Montserrat', sans-serif !important; color: #ffffff !important; }
        
        /* Botão Laranja Degradê */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #F6A41A 0%, #ED701B 100%);
            color: white; border: none; padding: 16px 32px; border-radius: 12px;
            font-weight: 700; width: 100%; transition: all 0.3s ease;
        }

        /* Sliders Azul Guardian */
        div[data-baseweb="slider"] div[role="slider"] { background-color: #189CD8 !important; }
        div[data-baseweb="slider"] > div > div > div:first-child { background-color: #189CD8 !important; }

        .stVerticalBlockBorderWrapper {
            border-radius: 16px;
            background-color: rgba(26, 20, 46, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==================================================
# 🔐 SEGURANÇA (LOGIN + MFA)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False): return True
    
    col_vazia_top = st.empty(); col_vazia_top.markdown("<br><br><br>", unsafe_allow_html=True)
    c_esq, c_centro, c_dir = st.columns([1, 1.2, 1])
    
    with c_centro:
        with st.container(border=True):
            if os.path.exists("strati_logo.png"): st.image("strati_logo.png", use_column_width=True)
            else: st.markdown("<h1 style='text-align: center;'>STRATI</h1>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                token_mfa = st.text_input("Token MFA (Admin)")
                submit = st.form_submit_button("ACESSAR")
                
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        if username == "diego_admin":
                            totp = pyotp.TOTP(st.secrets["mfa"]["secret_key"])
                            if totp.verify(token_mfa.replace(" ", "")):
                                st.session_state["authenticated"] = True
                                st.session_state["user_logado"] = username
                                st.rerun()
                            else: st.error("MFA incorreto.")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.rerun()
                    else: st.error("Credenciais inválidas.")
    return False

if not check_authentication(): st.stop()

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
    except: return True

# ==================================================
# 🧠 INTELIGÊNCIA ARTIFICIAL (GEMINI INTEGRATION)
# ==================================================
def gerar_playbook_ia(dados):
    # Anonimização para segurança
    prompt = f"""
    Aja como um Senior Customer Success Manager especialista em empresas MSP (Managed Service Providers).
    Gere um plano de ação tático para um CLIENTE OCULTO com o seguinte cenário:
    
    - Fase da Jornada: {dados['fase']}
    - Score de Risco: {dados['Risco']}/100
    - Score de Potencial: {dados['Potencial']}/100
    - Saúde do Serviço (SLA/Chamados): {dados['Servico']}/100
    - Satisfação (NPS): {dados['NPS']}
    - Engajamento (Reuniões/QBR): {dados['Engajamento']}/100
    
    Contexto Adicional:
    - {dados['gatilho_critico']}
    
    Instruções:
    1. O playbook deve ser dividido em: 'Estratégia Macro' e '3 Ações Prioritárias'.
    2. Linguagem executiva, técnica e direta.
    3. Foque em como reverter o risco ou capturar o potencial de expansão.
    4. Não use o nome real do cliente.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar IA: {str(e)}"

# ==================================================
# 📏 LÓGICA DE CÁLCULO (MATRIZ 3X3 + GATILHOS)
# ==================================================
class CustomerHealthModel:
    def calcular(self, d):
        # Saúde MSP (SLA + Volume)
        score_vol = {"Adequado / Estável": 100, "Muito Baixo (Silêncio/Shadow IT)": 30, "Alto (Instabilidade/Atrito)": 50, "Crítico (Incidentes Graves)": 10}.get(d['cenario_chamados'])
        score_servico = (score_vol * 0.6) + (d['sla_atingido'] * 0.4)
        
        # Engajamento
        score_eng = ((100 if d['qbr'] == 'Sim' else 0) * 0.5) + ((100 if d['book'] == 'Apresentado' else 0) * 0.5)
        
        # Risco e Potencial
        risco_total = ((100 - score_servico) * 0.4) + ((100 - score_eng) * 0.3) + ((100 - (d['nps']*10 if d['nps'] else 50)) * 0.3)
        potencial_total = (d['receita'] * 0.4) + (d['fit'] * 0.3) + (d['expansao'] * 0.3)
        
        # Gatilhos Críticos para a IA
        gatilhos = []
        if d['sla_atingido'] < 90: gatilhos.append("SLA abaixo da meta (Crítico)")
        if d['nps'] and d['nps'] <= 6: gatilhos.append("Cliente é Detrator (Urgência)")
        if d['qbr'] == 'Não' and d['fase'] == 'Retenção': gatilhos.append("QBR atrasada em conta de Retenção")
        if d['expansao'] > 80: gatilhos.append("Alto espaço para Cross-sell identificado")
        
        ctx = " | ".join(gatilhos) if gatilhos else "Operação dentro da normalidade."
        
        return {
            "Risco": round(risco_total, 1), "Potencial": round(potencial_total, 1),
            "Servico": int(score_servico), "Engajamento": int(score_eng),
            "NPS": d['nps'] if d['nps'] else "N/A", "fase": d['fase'],
            "gatilho_critico": ctx
        }

# ==================================================
# 🖥️ INTERFACE
# ==================================================
with st.sidebar:
    st.markdown("<h1>STRATI</h1>", unsafe_allow_html=True)
    st.write("---")
    nome = st.text_input("Nome da Empresa")
    fase = st.selectbox("Fase", ['Onboarding', 'Adoção', 'Retenção'])
    st.write("---")
    st.markdown("### Operacional")
    cenario = st.selectbox("Chamados", ["Adequado / Estável", "Muito Baixo (Silêncio/Shadow IT)", "Alto (Instabilidade/Atrito)", "Crítico (Incidentes Graves)"])
    sla = st.slider("SLA (%)", 50, 100, 98)
    qbr = st.radio("QBR?", ["Sim", "Não"], horizontal=True)
    book = st.radio("Book?", ["Apresentado", "Não realizado"], horizontal=True)
    nps = st.slider("NPS (0-10)", 0, 10, 8)

st.markdown("<h1>🛡️ CS Intelligence <span style='color:#F6A41A'>AI Edition</span></h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: receita = st.slider("Receita (ABC)", 0, 100, 50)
with c2: fit = st.slider("Fit Técnico", 0, 100, 70)
with c3: expansao = st.slider("Expansão (White Space)", 0, 100, 30)

if st.button("GERAR ANÁLISE COM IA"):
    if not nome: st.error("Nome obrigatório.")
    else:
        with st.spinner("IA Strati analisando dados..."):
            calc = CustomerHealthModel()
            res = calc.calcular({'fase': fase, 'cenario_chamados': cenario, 'sla_atingido': sla, 'qbr': qbr, 'book': book, 'nps': nps, 'receita': receita, 'fit': fit, 'expansao': expansao})
            
            # Chama o Gemini
            playbook_ia = gerar_playbook_ia(res)
            
            # Exibe Gráficos
            g1, g2 = st.columns(2)
            with g1: st.markdown("### Risco"); st.write(f"## {res['Risco']}%")
            with g2: st.markdown("### Potencial"); st.write(f"## {res['Potencial']}%")
            
            st.markdown("### 🤖 Playbook Sugerido (IA)")
            st.markdown(f"""<div style="background-color:rgba(255,255,255,0.05); padding:20px; border-radius:10px; border-left: 5px solid #F6A41A;">
                {playbook_ia.replace('\n', '<br>')}
            </div>""", unsafe_allow_html=True)
            
            # Salva
            salvar_no_banco({
                "Data": datetime.now().strftime("%d/%m/%Y"), "Cliente": nome, 
                "Risco": res['Risco'], "Potencial": res['Potencial'], "Playbook": playbook_ia
            })
            st.toast("Análise salva!", icon="✅")
