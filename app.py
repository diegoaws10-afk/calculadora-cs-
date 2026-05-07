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
            # --- RECUPERANDO A IMAGEM DO LOGO ---
            if os.path.exists("strati_logo.png"):
                st.image("strati_logo.png", use_column_width=True)
            elif os.path.exists("logo.png"):
                st.image("logo.png", use_column_width=True)
            else:
                st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>STRATI</h1>", unsafe_allow_html=True)
            # ------------------------------------
            
            st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 25px;'>Intelligence Control Center</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Ex: nome_cs")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                token_mfa = st.text_input("Token MFA", placeholder="6 dígitos (Deixe em branco se não for Admin)") 
                
                submit = st.form_submit_button("ACESSAR SISTEMA")
                
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        
                        # Lembre-se de colocar aqui o seu usuário exato do Secrets
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
    st.stop()# ==================================================
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
            
        return {"Risco": round(risco_total, 1), "Potencial": round(potencial_total, 1), "Cor": cor, "Servico": int(score_servico), "Estrategia": estrategia, "Acoes": acoes}

# ==================================================
# 🖥️ UI PRINCIPAL
# ==================================================
with st.sidebar:
    st.markdown("<h1>STRATI</h1>", unsafe_allow_html=True)
    if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()
    st.write("---")
    st.markdown("### 1. Perfil do Cliente")
    nome = st.text_input("Nome da Empresa", placeholder="Ex: Strati Tecnologia")
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    
    fase = st.selectbox("Fase da Jornada", ['Onboarding', 'Adoção', 'Retenção'])
    if fase == 'Onboarding':
        st.info("🎯 **0-6 meses:** Foco em implementação, treinamento e entrega do primeiro valor.")
    elif fase == 'Adoção':
        st.info("⚙️ **6-24 meses:** Foco em uso recorrente, estabilidade técnica e maturidade.")
    else:
        st.info("🤝 **+24 meses:** Parceria de longo prazo, foco em renovação e novos negócios.")

st.markdown("<h1>🛡️ Calculadora <span style='color:#3b82f6'>Potencial vs. Risco</span></h1>", unsafe_allow_html=True)

# RISCO
st.markdown("### 📉 Avaliação de Risco")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("**Uso do Serviço (Chamados)**")
        cenario_chamados = st.selectbox("Volume de Chamados", ["Adequado / Estável", "Muito Baixo (Silêncio/Shadow IT)", "Alto (Instabilidade/Atrito)", "Crítico (Incidentes Graves)"])
        sla_atingido = st.slider("SLA no Mês (%)", 50, 100, 98)
with r2:
    with st.container(border=True):
        st.markdown("**Engajamento**")
        visitas = st.slider("Visitas Presenciais", 0, 5, 1) if local == "SP (Local)" else 0
        online = st.slider("Calls Online", 0, 10, 2)
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        qbr_realizado = st.radio("QBR Apresentado?", ["Sim", "Não"], horizontal=True)
with r3:
    with st.container(border=True):
        st.markdown("**Satisfação**")
        tem_nps = st.toggle("NPS recente?", value=True)
        nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9) if tem_nps else None

st.write("---")

# POTENCIAL COM DESCRIÇÕES ABAIXO
st.markdown("### 🚀 Avaliação de Potencial")
p1, p2, p3 = st.columns(3)

with p1:
    receita = st.slider("Receita (0-100)", 0, 100, 50)
    st.caption("**Representatividade financeira.** Atribua 100 para o ticket mensal (MRR) ideal ou contas estratégicas da sua carteira.")

with p2:
    fit = st.slider("Fit do Cliente (0-100)", 0, 100, 70)
    st.caption("**Alinhamento operacional.** O quanto o cliente segue nossos padrões técnicos sem exigir exceções excessivas.")

with p3:
    crescimento = st.slider("Expansão (0-100)", 0, 100, 30)
    st.caption("**Oportunidade de novos negócios.** Mapeie se há serviços do portfólio (Segurança, Backup, etc) que ele ainda não contratou.")

st.write("")

if st.button("PROCESSAR RECLASSIFICAÇÃO", type="primary"):
    if not nome: st.toast("Preencha o nome do cliente.", icon="⚠️")
    else:
        modelo = CustomerHealthModel()
        res = modelo.calcular({'fase': fase, 'local': local, 'nps': nps_valor, 'visitas': visitas, 'book': book, 'qbr_realizado': qbr_realizado, 'online': online, 'nome': nome, 'cenario_chamados': cenario_chamados, 'sla_atingido': sla_atingido, 'receita': receita, 'fit': fit, 'crescimento': crescimento})
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.markdown("<h3 style='text-align:center'>Risco</h3>", unsafe_allow_html=True)
            st.plotly_chart(create_gauge_chart(res['Risco']), use_container_width=True)
        with c_res2:
            st.markdown("<h3 style='text-align:center'>Potencial</h3>", unsafe_allow_html=True)
            st.plotly_chart(create_gauge_chart(res['Potencial']), use_container_width=True)

        st.markdown("### 📋 Diagnóstico") 
        if res['Cor'] == 'green': st.success(res['Estrategia'], icon="✅")
        elif res['Cor'] == 'orange': st.warning(res['Estrategia'], icon="⚠️")
        else: st.error(res['Estrategia'], icon="🚨")
        
        for acao in res['Acoes']:
            st.markdown(f"""<div style="background-color:rgba(255,255,255,0.05); padding:10px; border-radius:5px; margin-bottom:5px; border-left: 3px solid #3b82f6;">{acao}</div>""", unsafe_allow_html=True)

        salvar_no_banco({"Data": datetime.now().strftime("%d/%m/%Y"), "Cliente": nome, "Fase": fase, "Risco": res['Risco'], "Potencial": res['Potencial'], "Responsável": st.session_state.get('user_logado', 'Admin')})
        st.toast("Análise salva!", icon="✅")
