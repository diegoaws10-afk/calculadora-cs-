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
# 🎨 DESIGN SYSTEM (CSS GLOBAL + LOGIN)
# ==================================================
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        @keyframes gradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        .stApp {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #334155);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            color: #f8fafc;
        }

        [data-testid="stSidebar"] {
            background-color: rgba(11, 17, 32, 0.95);
            border-right: 1px solid #334155;
            backdrop-filter: blur(10px);
        }

        h1, h2, h3 { font-family: 'Montserrat', sans-serif !important; color: #ffffff !important; }

        div.stButton > button:first-child {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 16px;
            letter-spacing: 0.5px;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            background-color: rgba(30, 41, 59, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==================================================
# 🔐 SEGURANÇA (LOGIN MULTI-PERFIL)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False):
        return True

    col_vazia_top = st.empty()
    col_vazia_top.markdown("<br><br><br>", unsafe_allow_html=True) 

    c_esq, c_centro, c_dir = st.columns([1, 1.2, 1])

    with c_centro:
        with st.container(border=True):
            # Recuperando a Imagem do Logo
            if os.path.exists("strati_logo.png"):
                st.image("strati_logo.png", use_column_width=True)
            elif os.path.exists("logo.png"):
                st.image("logo.png", use_column_width=True)
            else:
                st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>STRATI</h1>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 25px;'>Intelligence Control Center</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Ex: nome_cs")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                token_mfa = st.text_input("Token MFA", placeholder="6 dígitos (Deixe em branco se não for Admin)") 
                
                submit = st.form_submit_button("ACESSAR SISTEMA")
                
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        
                        USUARIO_ADMIN = "diego_admin" 
                        
                        if username == USUARIO_ADMIN:
                            secret_key = st.secrets["mfa"]["secret_key"]
                            totp = pyotp.TOTP(secret_key)
                            if totp.verify(token_mfa.replace(" ", "")):
                                st.session_state["authenticated"] = True
                                st.session_state["user_logado"] = username
                                st.toast("Acesso Autorizado (Admin)!", icon="🛡️")
                                time.sleep(0.5)
                                st.rerun()
                            else: 
                                st.error("MFA incorreto. Acesso negado.")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.toast(f"Bem-vindo(a), {username}!", icon="🚀")
                            time.sleep(0.5)
                            st.rerun()
                            
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
# 📊 GRÁFICOS
# ==================================================
def create_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        number = {'font': {'size': 40, 'color': "white"}, 'suffix': "%"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "rgba(255,255,255,0.3)"},
            'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
            'steps': [{'range': [0, 60], 'color': "#ef4444"}, {'range': [60, 75], 'color': "#f97316"}, {'range': [75, 100], 'color': "#22c55e"}],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)", font = {'color': "white", 'family': "Inter"}, height=200, margin=dict(l=20, r=20, t=10, b=10))
    return fig

# ==================================================
# 🧠 LÓGICA CS (MATRIZ POTENCIAL X RISCO - MSP)
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_fase = {
            'Onboarding': {'peso_interacao': 0.60, 'meta_visitas': 2},
            'Adoção':    {'peso_interacao': 0.30, 'meta_visitas': 1},
            'Retenção':  {'peso_interacao': 0.20, 'meta_visitas': 0.5}
        }

    def gerar_playbook_matriz(self, nivel_risco, nivel_potencial, nome_cliente):
        estrategia = ""
        acoes_taticas = []
        if nivel_risco > 60 and nivel_potencial > 60:
            estrategia = f"🔥 ALTO POTENCIAL EM RISCO: {nome_cliente} é estratégico mas instável."
            acoes_taticas.extend(["Envolver liderança", "Plano de estabilização imediata", "Pausar Upsell"])
        elif nivel_risco > 60 and nivel_potencial <= 60:
            estrategia = f"⚠️ RISCO COM BAIXO POTENCIAL: Alto custo de servir para baixo retorno."
            acoes_taticas.extend(["Revisar fit do cliente", "Automatizar suporte", "Ajustar precificação"])
        elif nivel_risco <= 60 and nivel_potencial > 60:
            estrategia = f"🚀 OPORTUNIDADE CLARA: Cliente estável e pronto para expandir."
            acoes_taticas.extend(["Cross-sell de serviços", "Mapear expansão de infra", "Pedir Indicação"])
        else:
            estrategia = f"🛡️ MANUTENÇÃO ESTÁVEL: Operação saudável, foco em retenção."
            acoes_taticas.extend(["Manter QBRs", "Garantir renovação", "Entrega de valor contínua"])
        return estrategia, acoes_taticas

    def calcular(self, dados):
        regras = self.regras_fase[dados['fase']]
        
        if dados['local'] == "SP (Local)":
            meta = regras['meta_visitas']
            score_presenca = 100 if meta == 0 else min((dados['visitas']/meta)*100, 100.0)
            bonus_online = min(dados['online']*2, 10)
        else:
            score_presenca = min((dados['online']/2)*100, 100.0)
            bonus_online = 0 if dados['visitas'] == 0 else 10 

        score_engajamento = min((score_presenca*0.5) + ((100 if dados['qbr_realizado'] == 'Sim' else 0)*0.25) + ((100 if dados['book']=='Apresentado' else 0)*0.25) + bonus_online, 100.0)
        score_satisfacao = (dados['nps'] * 10) if dados['nps'] is not None else 50
        score_volume = {"Adequado / Estável": 100, "Alto (Instabilidade/Atrito)": 50, "Muito Baixo (Silêncio/Shadow IT)": 30}.get(dados['cenario_chamados'], 10)
        score_servico = (score_volume * 0.60) + (dados['sla_atingido'] * 0.40)

        risco_total = ((100 - score_servico) * 0.40) + ((100 - score_engajamento) * 0.30) + ((100 - score_satisfacao) * 0.30)
        potencial_total = (dados['receita'] * 0.40) + (dados['fit'] * 0.30) + (dados['crescimento'] * 0.30)

        cor = "red" if risco_total > 60 else ("orange" if risco_total > 40 else "green")
        estrategia, acoes = self.gerar_playbook_matriz(risco_total, potencial_total, dados['nome'])
            
        return {"Risco": round(risco_total, 1), "Potencial": round(potencial_total, 1), "Cor": cor, "Servico": int(score_servico), "Estrategia": estrategia, "Acoes
