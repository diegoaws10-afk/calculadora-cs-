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
        /* Importando Fontes */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        /* ANIMAÇÃO DE FUNDO (AURORA) */
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

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(11, 17, 32, 0.95);
            border-right: 1px solid #334155;
            backdrop-filter: blur(10px);
        }

        h1, h2, h3 { font-family: 'Montserrat', sans-serif !important; color: #ffffff !important; }

        /* ESTILO ESPECÍFICO DO LOGIN (CARD FLUTUANTE) */
        .login-card {
            background: rgba(30, 41, 59, 0.75);
            border-radius: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            text-align: center;
        }

        /* Inputs Modernos */
        .stTextInput input {
            background-color: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }

        /* Botão Principal */
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
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.5);
        }

        /* Esconde elementos padrão do Streamlit na tela de login */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Ajuste de Cards internos */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            background-color: rgba(30, 41, 59, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==================================================
# 🔐 SEGURANÇA (LOGIN DE ALTO IMPACTO)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False):
        return True

    col_vazia_top = st.empty()
    col_vazia_top.markdown("<br><br><br>", unsafe_allow_html=True) 

    c_esq, c_centro, c_dir = st.columns([1, 1.2, 1])

    with c_centro:
        with st.container(border=True):
            if os.path.exists("strati_logo.png"):
                st.image("strati_logo.png", use_column_width=True)
            elif os.path.exists("logo.png"):
                st.image("logo.png", use_column_width=True)
            else:
                st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>STRATI</h1>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 25px;'>Intelligence Control Center</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Digite seu usuário corporativo")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                token_mfa = st.text_input("Token MFA", placeholder="Código do App (6 dígitos)") 
                
                st.write("")
                submit = st.form_submit_button("ACESSAR SISTEMA")
                
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        secret_key = st.secrets["mfa"]["secret_key"]
                        totp = pyotp.TOTP(secret_key)
                        if totp.verify(token_mfa.replace(" ", "")):
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.toast("Acesso Autorizado! Carregando...", icon="🚀")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Código MFA incorreto.")
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
# 🧠 LÓGICA CS (MATRIZ POTENCIAL X RISCO)
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_fase = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'meta_visitas': 0.5}
        }

    def gerar_playbook_matriz(self, nivel_risco, nivel_potencial, nome_cliente):
        estrategia = ""
        acoes_taticas = []
        
        # Cruzamento da Matriz
        if nivel_risco > 60 and nivel_potencial > 60:
            estrategia = f"🔥 ALTO POTENCIAL EM RISCO: {nome_cliente} pode trazer muita receita, mas está frustrado ou sem engajamento."
            acoes_taticas.extend(["Envolver liderança (Sponsor to Sponsor)", "Montar plano de reversão imediato focando na dor principal", "Pausar qualquer tentativa de upsell até estabilizar o uso"])
        elif nivel_risco > 60 and nivel_potencial <= 60:
            estrategia = f"⚠️ RISCO COM BAIXO POTENCIAL: {nome_cliente} exige esforço, mas com baixo retorno financeiro."
            acoes_taticas.extend(["Avaliar se o cliente tem fit de longo prazo", "Automatizar o atendimento para reduzir Custo de Servir", "Aplicar reajuste de preço na renovação, se aplicável"])
        elif nivel_risco <= 60 and nivel_potencial > 60:
            estrategia = f"🚀 OPORTUNIDADE CLARA: {nome_cliente} está saudável e pronto para expansão."
            acoes_taticas.extend(["Apresentar novas features ou serviços adicionais", "Mapear áreas correlatas para cross-sell", "Solicitar indicação ou caso de sucesso"])
        else:
            estrategia = f"🛡️ MANUTENÇÃO ESTÁVEL: {nome_cliente} está saudável, mas com baixo potencial de expansão."
            acoes_taticas.extend(["Manter cadência de relacionamento padrão", "Garantir a renovação automática", "Focar na entrega de valor contínua"])

        return estrategia, acoes_taticas

    def calcular(self, dados):
        regras = self.regras_fase[dados['fase']]
        
        # 1. CÁLCULO DE RISCO (Uso 40%, Engajamento 30%, Satisfação 30%)
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
        score_engajamento = (score_presenca*0.5) + ((book_pts + qbr_pts)/2*0.5) + bonus_online
        score_engajamento = min(score_engajamento, 100.0)

        if dados['nps'] is None:
            score_satisfacao = 50
            msg_nps = "N/A"
        else:
            score_satisfacao = dados['nps'] * 10
            msg_nps = dados['nps']

        risco_engajamento = 100 - score_engajamento
        risco_satisfacao = 100 - score_satisfacao
        risco_uso = 100 - dados['uso']

        risco_total = (risco_uso * 0.40) + (risco_engajamento * 0.30) + (risco_satisfacao * 0.30)

        # 2. CÁLCULO DE POTENCIAL (Receita 40%, Fit 30%, Crescimento 30%)
        potencial_total = (dados['receita'] * 0.40) + (dados['fit'] * 0.30) + (dados['crescimento'] * 0.30)

        if risco_total > 60: cor, icone = "red", "🚨"
        elif risco_total > 40: cor, icone = "orange", "⚠️"
        else: cor, icone = "green", "✅"
        
        estrategia, acoes = self.gerar_playbook_matriz(risco_total, potencial_total, dados['nome'])
            
        return {
            "Risco": round(risco_total, 1),
            "Potencial": round(potencial_total, 1),
            "Cor": cor, "Icone": icone,
            "Engajamento": int(score_engajamento), 
            "Uso": int(dados['uso']), 
            "NPS": msg_nps, 
            "Estrategia": estrategia, "Acoes": acoes
        }

# ==================================================
# 🖥️ UI PRINCIPAL (DASHBOARD)
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
    if st.button("🚪 Sair / Logout"): st.session_state.clear(); st.rerun()
    
    st.markdown("### 1. Perfil do Cliente")
    nome = st.text_input("Nome da Empresa", placeholder="Ex: Strati Tecnologia")
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    fase = st.selectbox("Fase da Jornada", ['Onboarding', 'Adoção', 'Retenção'])

st.markdown("<h1>🛡️ Calculadora de <span style='color:#3b82f6'>Potencial vs. Risco</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#94a3b8; font-size:1.1rem'>Análise de Carteira: <b>{nome if nome else 'Novo Cliente'}</b></p>", unsafe_allow_html=True)

# Linha 1: Fatores de Risco
st.markdown("### 📉 Avaliação de Risco")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("**Uso do Produto**")
        uso = st.slider("Taxa de Adoção (%)", 0, 100, 50, help="Qual a aderência do cliente à plataforma/serviço?")
with r2:
    with st.container(border=True):
        st.markdown("**Engajamento**")
        if local == "SP (Local)":
            visitas = st.slider("Visitas Presenciais", 0, 5, 1)
            online = st.slider("Calls Online", 0, 10, 2)
        else:
            online = st.slider("Calls Online (Meta: 2)", 0, 10, 2)
            visitas = 0
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        qbr_realizado = st.radio("QBR Apresentado?", ["Sim", "Não"], horizontal=True)
with r3:
    with st.container(border=True):
        st.markdown("**Satisfação**")
        tem_nps = st.toggle("Cliente respondeu NPS?", value=True)
        if tem_nps: nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
        else: nps_valor = None; st.warning("Sem dados recentes.")

st.write("---")

# Linha 2: Fatores de Potencial
st.markdown("### 🚀 Avaliação de Potencial")
p1, p2, p3 = st.columns(3)
with p1:
    with st.container(border=True):
        receita = st.slider("Receita (Score 0-100)", 0, 100, 50, help="Volume financeiro que o cliente representa.")
with p2:
    with st.container(border=True):
        fit = st.slider("Fit do Cliente (Score 0-100)", 0, 100, 70, help="O quanto nossa solução resolve a dor real dele.")
with p3:
    with st.container(border=True):
        crescimento = st.slider("Oportunidade de Upsell/Cross-sell", 0, 100, 30, help="Qual a margem para expansão nesta conta?")

st.write("")

if st.button("PROCESSAR RECLASSIFICAÇÃO", type="primary"):
    if not nome:
        st.toast("Preencha o nome do cliente.", icon="⚠️")
    else:
        progress_text = "Calculando Matriz..."
        my_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.005)
            my_bar.progress(percent_complete + 1, text=progress_text)
        my_bar.empty()

        try:
            fase_map = {'Onboarding': 'Onboarding (0-6m)', 'Adoção': 'Adoção (6-24m)', 'Retenção': 'Retenção (+2 anos)'}
            modelo = CustomerHealthModel()
            inputs = {
                'fase': fase_map[fase], 'local': local, 'nps': nps_valor, 'visitas': visitas, 
                'book': book, 'qbr_realizado': qbr_realizado, 'online': online, 'nome': nome,
                'uso': uso, 'receita': receita, 'fit': fit, 'crescimento': crescimento
            }
            res = modelo.calcular(inputs)
        except Exception as e:
            st.error(f"Erro no Cálculo: {e}")
            st.stop()
        
        st.markdown("---")
        
        # Resultados e Gráficos
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align:center'>Risco Calculado</h3>", unsafe_allow_html=True)
                fig_risco = create_gauge_chart(res['Risco'])
                st.plotly_chart(fig_risco, use_container_width=True)
                st.markdown("<p style='text-align:center; color:#94a3b8'>*Quanto maior, mais propensão a Churn</p>", unsafe_allow_html=True)
        with c_res2:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align:center'>Potencial Calculado</h3>", unsafe_allow_html=True)
                fig_potencial = create_gauge_chart(res['Potencial'])
                st.plotly_chart(fig_potencial, use_container_width=True)
                st.markdown("<p style='text-align:center; color:#94a3b8'>*Quanto maior, mais propensão a Expansão</p>", unsafe_allow_html=True)

        st.write("")
        st.markdown("### 📋 Posicionamento na Matriz e Plano de Ação") 
        
        with st.container(border=True):
            estrat = res.get('Estrategia', 'Erro ao gerar estratégia')
            acoes_list = res.get('Acoes', [])

            if res['Cor'] == 'green': st.success(estrat, icon="✅")
            elif res['Cor'] == 'orange': st.warning(estrat, icon="⚠️")
            else: st.error(estrat, icon="🚨")
            
            st.write("")
            st.markdown("**Passos Seguintes:**")
            for acao in acoes_list:
                st.markdown(f"""<div style="background-color:rgba(255,255,255,0.05); padding:10px; border-radius:5px; margin-bottom:5px; border-left: 3px solid #3b82f6;">{acao}</div>""", unsafe_allow_html=True)

        # 5. Salvamento no Banco
        st.write("💾 Salvando dados...")
        
        nps_banco = res['NPS'] if res['NPS'] != "N/A" else ""
        str_acoes = "\n".join([f"- {a}" for a in res.get('Acoes', [])])
        playbook_completo = f"{res.get('Estrategia', '')}\n\n[AÇÕES SUGERIDAS]\n{str_acoes}"
        
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"), 
            "Cliente": nome, 
            "Fase": fase,
            "Local": local, 
            "Risco (%)": res['Risco'], 
            "Potencial (%)": res['Potencial'],
            "Engajamento": res['Engajamento'], 
            "Uso": res['Uso'], 
            "NPS": nps_banco, 
            "Responsável": st.session_state.get('user_logado', 'Admin'), 
            "Playbook": playbook_completo
        }
        
        if salvar_no_banco(dados_db):
            st.toast("Sucesso! Análise salva no banco.", icon="✅")
        else:
            st.error("Erro ao conectar com a planilha. Verifique os Secrets.")
