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
# 🎨 DESIGN SYSTEM (CSS GLOBAL + LOGIN + STRATI PALETTE)
# ==================================================
def load_css():
    st.markdown("""
        <style>
        /* Importando Fontes */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        /* ANIMAÇÃO DE FUNDO (AURORA - ADAPTADO STRATI FUNDO GRays) */
        @keyframes gradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        .stApp {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(-45deg, #1A1A1A, #000000, #1A1A1A, #262626);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            color: #f8fafc;
        }

        /* Sidebar (FUNDO AZUL Escuro) */
        [data-testid="stSidebar"] {
            background-color: rgba(11, 13, 25, 0.95); 
            border-right: 1px solid #262626;
            backdrop-filter: blur(10px);
        }

        /* Títulos */
        h1, h2, h3 { font-family: 'Montserrat', sans-serif !important; color: #ffffff !important; }

        /* ESTILO ESPECÍFICO DO LOGIN */
        .stVerticalBlockBorderWrapper {
            border-radius: 16px;
            background-color: rgba(26, 20, 46, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Inputs Modernos (Texto e Números) */
        .stTextInput input, .stNumberInput input {
            background-color: rgba(0, 0, 0, 0.4) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #189CD8 !important; /* Azul Guardian */
            box-shadow: 0 0 0 2px rgba(24, 156, 216, 0.2) !important;
        }

        /* ========================================= */
        /* CUSTOMIZAÇÃO DOS SLIDERS (Remover Vermelho) */
        /* ========================================= */
        /* Marcador (Bolinha) do Slider */
        div[data-baseweb="slider"] div[role="slider"] {
            background-color: #189CD8 !important; /* Azul Guardian */
            border: 2px solid #ffffff !important;
        }
        /* Marcador com foco */
        div[data-baseweb="slider"] div[role="slider"]:focus {
            box-shadow: 0 0 0 0.2rem rgba(24, 156, 216, 0.4) !important;
        }
        /* Barra preenchida à esquerda do marcador */
        div[data-baseweb="slider"] > div > div > div:first-child {
            background-color: #189CD8 !important; /* Azul Guardian */
        }
        /* Barra não preenchida à direita do marcador */
        div[data-baseweb="slider"] > div > div > div:last-child {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }

        /* Botão Principal (LARANJA STRATI degradê: #F6A41A -> #ED701B) */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #F6A41A 0%, #ED701B 100%);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 16px;
            letter-spacing: 0.5px;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(237, 112, 27, 0.4);
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(237, 112, 27, 0.5);
        }

        /* Esconde elementos padrão */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Divs de ação sugeridas */
        [data-testid="stAlert"] {
            border-left: 3px solid #ED701B !important;
        }
        
        /* Ajuste geral dos containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            background-color: rgba(26, 20, 46, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
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
            if os.path.exists("strati_logo.png"):
                st.image("strati_logo.png", use_column_width=True)
            elif os.path.exists("logo.png"):
                st.image("logo.png", use_column_width=True)
            else:
                st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>STRATI</h1>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: #A6A6A6; margin-bottom: 25px;'>Intelligence Control Center</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Ex: nome_cs")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                token_mfa = st.text_input("Token MFA", placeholder="6 dígitos (Deixar em branco se não for Admin)") 
                
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
                                st.toast("Acesso Autorizado (Admin)! 🛡️", icon="🛡️")
                                time.sleep(0.5)
                                st.rerun()
                            else: 
                                st.error("MFA incorreto. Acesso negado.")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.toast(f"Bem-vindo(a), {username}! 🚀", icon="🚀")
                            time.sleep(0.5)
                            st.rerun()
                            
                    else: 
                        st.error("Credenciais inválidas.")
    return False

if not check_authentication():
    st.stop()

# ==================================================
# 💾 BANCO DE DADOS (GSheets)
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
# 📊 GRÁFICOS (ADAPTADO CORES STRATI)
# ==================================================
def create_gauge_chart(score):
    red_func = "#ef4444"      # Crítico
    orange_deep = "#ED701B"  # Strati Deep Orange
    green_work = "#95C11F"   # Digital Work Green

    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        number = {'font': {'size': 40, 'color': "white"}, 'suffix': "%"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#A6A6A6"},
            'bar': {'color': "rgba(255,255,255,0.3)"},
            'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
            'steps': [
                {'range': [0, 60], 'color': red_func},
                {'range': [60, 75], 'color': orange_deep},
                {'range': [75, 100], 'color': green_work}
            ],
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
            estrategia = f"🔥 ALTO POTENCIAL EM RISCO: {nome_cliente} pode trazer muita receita, mas apresenta risco técnico/engajamento."
            acoes_taticas.extend(["Envolver liderança", "Plano de estabilização imediata", "Pausar Upsell"])
        elif nivel_risco > 60 and nivel_potencial <= 60:
            estrategia = f"⚠️ RISCO COM BAIXO POTENCIAL: {nome_cliente} exige alto esforço de suporte técnico com baixo retorno financeiro."
            acoes_taticas.extend(["Revisar fit técnico do cliente", "Automatizar suporte (reduzir custo)", "Ajustar precificação na renovação"])
        elif nivel_risco <= 60 and nivel_potencial > 60:
            estrategia = f"🚀 OPORTUNIDADE CLARA: {nome_cliente} possui serviço estável e alto potencial estratégico."
            acoes_taticas.extend(["Cross-sell (Segurança/Cloud/Guardian)", "Mapear expansão de infraestrutura", "Pedir Indicação/Case"])
        else:
            estrategia = f"🛡️ MANUTENÇÃO ESTÁVEL: {nome_cliente} possui operação saudável, mas com baixo teto de crescimento atual."
            acoes_taticas.extend(["Manter cadência de relacionamento", "Garantir renovação contratual", "Focar na entrega de valor (SLA)"])

        return estrategia, acoes_taticas

    def calcular(self, dados):
        regras = self.regras_fase[dados['fase']]
        
        # Engajamento
        if dados['local'] == "SP (Local)":
            meta = regras['meta_visitas']
            score_presenca = 100 if meta == 0 else min((dados['visitas']/meta)*100, 100.0)
            bonus_online = min(dados['online']*2, 10)
        else:
            score_presenca = min((dados['online']/2)*100, 100.0)
            bonus_online = 0 if dados['visitas'] == 0 else 10 

        qbr_pts = 100 if dados['qbr_realizado'] == 'Sim' else 0
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        score_engajamento = min((score_presenca*0.5) + ((qbr_pts + book_pts)/2*0.5) + bonus_online, 100.0)

        # Satisfação
        if dados['nps'] is None:
            score_satisfacao = 50
            msg_nps = "N/A"
        else:
            score_satisfacao = dados['nps'] * 10
            msg_nps = dados['nps']

        # Saúde MSP
        score_volume = {"Adequado / Estável": 100, "Alto (Instabilidade/Atrito)": 50, "Muito Baixo (Silêncio/Shadow IT)": 30}.get(dados['cenario_chamados'], 10)
        score_servico = (score_volume * 0.60) + (dados['sla_atingido'] * 0.40)

        # Risco Total
        risco_total = ((100 - score_servico) * 0.40) + ((100 - score_engajamento) * 0.30) + ((100 - score_satisfacao) * 0.30)

        # Potencial
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
            "Servico": int(score_servico), 
            "NPS": msg_nps, 
            "Estrategia": estrategia, "Acoes": acoes
        }

# ==================================================
# 🖥️ UI PRINCIPAL
# ==================================================
with st.sidebar:
    if os.path.exists("strati_logo.png"):
        st.image("strati_logo.png", use_column_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        st.markdown("<h1>STRATI</h1>", unsafe_allow_html=True)
        
    st.write("---")
    if st.button("🚪 Sair / Logout"): st.session_state.clear(); st.rerun()
    
    st.markdown("### 1. Perfil do Cliente")
    nome = st.text_input("Nome da Empresa", placeholder="Ex: Strati Tecnologia")
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    
    fase = st.selectbox("Fase da Jornada", ['Onboarding', 'Adoção', 'Retenção'])
    if fase == 'Onboarding':
        st.info("🎯 **0-6 meses:** Foco em implementação, formação e entrega do primeiro valor técnico.")
    elif fase == 'Adoção':
        st.info("⚙️ **6-24 meses:** Foco em uso recorrente, estabilidade técnica e maturidade operacional.")
    else:
        st.info("🤝 **+24 meses:** Parceria estratégica a longo prazo, foco em renovação e novos negócios.")

st.markdown("<h1>🛡️ Calculadora CS <span style='color:#F6A41A'>Intelligence</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#A6A6A6; font-size:1.1rem'>Análise de Carteira: <b>{nome if nome else 'Novo Cliente'}</b></p>", unsafe_allow_html=True)

# RISCO
st.markdown("### 📉 Avaliação de Risco (Operacional & Relacionamento)")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("**Saúde do Serviço (Chamados & SLA)**")
        cenario_chamados = st.selectbox(
            "Volume de Chamados (Últimos 30 dias)",
            ["Adequado / Estável", "Muito Baixo (Silêncio/Shadow IT)", "Alto (Instabilidade/Atrito)", "Crítico (Incidentes Graves)"]
        )
        sla_atingido = st.slider("SLA Atingido no Mês (%)", 50, 100, 98)
with r2:
    with st.container(border=True):
        st.markdown("**Engajamento Contínuo**")
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
        st.markdown("**Satisfação Percebida**")
        tem_nps = st.toggle("Cliente respondeu NPS recente?", value=True)
        if tem_nps: nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
        else: nps_valor = None; st.warning("⚖️ Peso redistribuído.")

st.write("---")

# POTENCIAL (COM TEXTOS DETALHADOS RESTAURADOS)
st.markdown("### 🚀 Avaliação de Potencial (Financeiro & Estratégico)")
p1, p2, p3 = st.columns(3)

with p1:
    with st.container(border=True):
        st.markdown("**Representatividade Financeira**")
        receita = st.slider("Volume Financeiro (Score 0-100)", 0, 100, 50)
        st.caption("**Curva ABC (MRR):**<br>• **80-100:** Contas estratégicas (Maior impacto).<br>• **40-79:** Contas médias.<br>• **0-39:** Contas de menor impacto financeiro.", unsafe_allow_html=True)

with p2:
    with st.container(border=True):
        st.markdown("**Fit Operacional**")
        fit = st.slider("Alinhamento Técnico (Score 0-100)", 0, 100, 70)
        st.caption("**Alinhamento à Stack Strati:**<br> O quanto o cliente confia e segue os nossos padrões técnicos sem exigir inúmeras exceções no dia a dia.", unsafe_allow_html=True)

with p3:
    with st.container(border=True):
        st.markdown("**Oportunidade de Novos Negócios**")
        crescimento = st.slider("Expansão (Score 0-100)", 0, 100, 30)
        st.caption("**White Space (Venda Cruzada):**<br> Notas altas indicam que o cliente tem potencial para contratar outras soluções do nosso portfólio (Segurança, Backup, etc).", unsafe_allow_html=True)

st.write("")

if st.button("PROCESSAR RECLASSIFICAÇÃO MSP", type="primary"):
    if not nome:
        st.toast("Preenche o nome do cliente.", icon="⚠️")
    else:
        progress_text = "A calcular a Matriz MSP Strati..."
        my_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.005)
            my_bar.progress(percent_complete + 1, text=progress_text)
        my_bar.empty()

        try:
            fase_map = {'Onboarding': 'Onboarding', 'Adoção': 'Adoção', 'Retenção': 'Retenção'}
            modelo = CustomerHealthModel()
            inputs = {
                'fase': fase_map[fase], 'local': local, 'nps': nps_valor, 'visitas': visitas, 
                'book': book, 'qbr_realizado': qbr_realizado, 'online': online, 'nome': nome,
                'cenario_chamados': cenario_chamados, 'sla_atingido': sla_atingido,
                'receita': receita, 'fit': fit, 'crescimento': crescimento
            }
            res = modelo.calcular(inputs)
        except Exception as e:
            st.error(f"Erro no Cálculo: {e}")
            st.stop()
        
        st.markdown("---")
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align:center'>Risco Calculado</h3>", unsafe_allow_html=True)
                fig_risco = create_gauge_chart(res['Risco'])
                st.plotly_chart(fig_risco, use_container_width=True)
                st.markdown("<p style='text-align:center; color:#A6A6A6'>*Quanto maior, maior a propensão a Churn</p>", unsafe_allow_html=True)
        with c_res2:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align:center'>Potencial Calculado</h3>", unsafe_allow_html=True)
                fig_potencial = create_gauge_chart(res['Potencial'])
                st.plotly_chart(fig_potencial, use_container_width=True)
                st.markdown("<p style='text-align:center; color:#A6A6A6'>*Quanto maior, maior a propensão a Expansão</p>", unsafe_allow_html=True)

        st.write("")
        st.markdown("### 📋 Posicionamento e Plano de Ação Strati") 
        
        with st.container(border=True):
            estrat = res.get('Estrategia', 'Erro ao gerar estratégia')
            acoes_list = res.get('Acoes', [])

            if res['Cor'] == 'green': st.success(estrat, icon="✅")
            elif res['Cor'] == 'orange': st.warning(estrat, icon="⚠️")
            else: st.error(estrat, icon="🚨")
            
            st.write("")
            st.markdown("**Próximos Passos Táticos:**")
            for acao in acoes_list:
                st.markdown(f"""<div style="background-color:rgba(255,255,255,0.03); padding:10px; border-radius:8px; margin-bottom:5px; border-left: 3px solid #F6A41A;">{acao}</div>""", unsafe_allow_html=True)

        st.write("💾 A guardar os dados na folha de cálculo...")
        
        nps_banco = res['NPS'] if res['NPS'] != "N/A" else ""
        str_acoes = "\n".join([f"- {a}" for a in res.get('Acoes', [])])
        playbook_completo = f"{res.get('Estrategia', '')}\n\n[AÇÕES SUGERIDAS]\n{str_acoes}"
        
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"), 
            "Cliente": nome, 
            "Local": local, 
            "Fase": fase,
            "Risco (%)": res['Risco'], 
            "Potencial (%)": res['Potencial'],
            "Engajamento": res['Engajamento'], 
            "Serviço (Saúde)": res['Servico'], 
            "NPS": nps_banco, 
            "Responsável": st.session_state.get('user_logado', 'Admin'), 
            "Playbook Sugerido": playbook_completo
        }
        
        if salvar_no_banco(dados_db):
            st.toast("Sucesso! Análise guardada na folha de cálculo.", icon="✅")
        else:
            st.error("Erro ao ligar à folha de cálculo. Verifica os Secrets.")
