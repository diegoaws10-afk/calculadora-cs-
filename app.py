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
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("⚠️ Erro de Conexão IA: Verifique a GEMINI_API_KEY nos Secrets.")

# ==================================================
# 🎨 DESIGN SYSTEM (ESTÉTICA PREMIUM STRATI)
# ==================================================
def load_css():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        /* FUNDO PRINCIPAL COM IMAGEM STRATI */
        .stApp {{
            font-family: 'Inter', sans-serif;
            background-image: linear-gradient(rgba(11, 13, 25, 0.85), rgba(11, 13, 25, 0.85)), url("https://raw.githubusercontent.com/sua_conta/seu_repo/main/background_strati.png");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #f8fafc;
        }}

        /* SIDEBAR */
        [data-testid="stSidebar"] {{
            background-color: rgba(11, 17, 32, 0.98);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}

        h1, h2, h3 {{ font-family: 'Montserrat', sans-serif !important; font-weight: 700; color: #ffffff !important; }}
        
        /* BOTÃO LARANJA STRATI */
        div.stButton > button:first-child {{
            background: linear-gradient(90deg, #F6A41A 0%, #ED701B 100%);
            color: white; border: none; padding: 18px; border-radius: 12px;
            font-weight: 700; font-size: 16px; width: 100%; transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(246, 164, 26, 0.3);
        }}
        div.stButton > button:first-child:hover {{
            transform: translateY(-2px); box-shadow: 0 8px 25px rgba(246, 164, 26, 0.5);
        }}

        /* SLIDERS AZUL GUARDIAN */
        div[data-baseweb="slider"] div[role="slider"] {{ background-color: #189CD8 !important; border: 2px solid white !important; }}
        div[data-baseweb="slider"] > div > div > div:first-child {{ background-color: #189CD8 !important; }}

        /* CARDS E CONTAINERS */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px;
            background-color: rgba(30, 41, 59, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
        }}

        .stCaption {{ color: #cbd5e1 !important; font-size: 13px !important; line-height: 1.4 !important; }}
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==================================================
# 🔐 SEGURANÇA (AUTENTICAÇÃO)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False): return True
    
    col_vazia_top = st.empty(); col_vazia_top.markdown("<br><br><br>", unsafe_allow_html=True)
    c_esq, c_centro, c_dir = st.columns([1, 1.2, 1])
    
    with c_centro:
        with st.container(border=True):
            if os.path.exists("strati_logo.png"): st.image("strati_logo.png", use_column_width=True)
            else: st.markdown("<h1 style='text-align: center; color: #F6A41A !important;'>STRATI</h1>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                t = st.text_input("Token MFA (Se Admin)")
                if st.form_submit_button("ACESSAR SISTEMA"):
                    if u in st.secrets["passwords"] and p == st.secrets["passwords"][u]:
                        if u == "diego_admin":
                            totp = pyotp.TOTP(st.secrets["mfa"]["secret_key"])
                            if totp.verify(t.replace(" ", "")):
                                st.session_state["authenticated"] = True
                                st.session_state["user_logado"] = u
                                st.rerun()
                            else: st.error("MFA Inválido")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = u
                            st.rerun()
                    else: st.error("Credenciais incorretas")
    return False

if not check_authentication(): st.stop()

# ==================================================
# 🧠 IA STRATI (PROMPT ENGENHARIA)
# ==================================================
def gerar_playbook_ia(d):
    prompt = f"""
    Aja como um Diretor de Customer Success para MSPs. Analise este cenário e gere um playbook tático:
    - Tier/Cohort: {d['cohort']}
    - Fase da Jornada: {d['fase']}
    - Risco Atual: {d['Risco']}% | Potencial de Expansão: {d['Potencial']}%
    - Saúde Técnica (SLA/Chamados): {d['Servico']}/100
    - Engajamento: {d['Engajamento']}/100
    - Satisfação (NPS): {d['NPS']}
    
    Contexto Crítico: {d['gatilhos']}
    
    Formate sua resposta rigorosamente em 3 seções:
    1. 🎯 ESTRATÉGIA MACRO (Uma frase forte sobre o direcional da conta)
    2. 🛠️ AÇÕES IMEDIATAS (3 tópicos curtos e acionáveis)
    3. 💡 INSIGHT DE EXPANSÃO (Onde está o dinheiro/White Space baseando-se no tier do cliente)
    
    Use tom executivo e não cite nomes fictícios de clientes.
    """
    try:
        # AUTODESCOBERTA: O código procura o modelo válido automaticamente
        modelo_correto = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo_correto = m.name
                break
                
        if not modelo_correto:
            return "⚠️ Erro: A sua chave de API não tem acesso a modelos de texto."
            
        model_dinamico = genai.GenerativeModel(modelo_correto)
        response = model_dinamico.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro detalhado da IA: {str(e)}"
# ==================================================
# 📊 GRÁFICOS (GAUGE CUSTOM)
# ==================================================
def create_gauge(label, value, color_steps):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': label, 'font': {'size': 24, 'color': 'white'}},
        number = {'suffix': "%", 'font': {'color': 'white'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "rgba(255,255,255,0.5)"},
            'steps': color_steps,
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(l=30, r=30, t=50, b=20))
    return fig

# ==================================================
# 🖥️ INTERFACE PRINCIPAL
# ==================================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>STRATI CONTROL</h2>", unsafe_allow_html=True)
    st.write("---")
    nome_cliente = st.text_input("Nome da Conta", placeholder="Ex: Cliente Alpha")
    
    # NOVO: SELEÇÃO DE COHORT
    cohort = st.selectbox("Tier / Cohort", ["Diamante", "Ouro", "Prata", "Bronze"])
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    
    # FASE DA JORNADA COM LEGENDAS RESTAURADAS
    fase_jornada = st.selectbox("Fase Atual", ['Onboarding', 'Adoção', 'Retenção'])
    if fase_jornada == 'Onboarding':
        st.info("🎯 **0-6 meses:** Foco em implementação, formação e entrega do primeiro valor técnico.")
    elif fase_jornada == 'Adoção':
        st.info("⚙️ **6-24 meses:** Foco em uso recorrente, estabilidade técnica e maturidade operacional.")
    else:
        st.info("🤝 **+24 meses:** Parceria estratégica a longo prazo, foco em renovação e novos negócios.")
        
    st.write("---")
    if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()

# CABEÇALHO
st.markdown(f"<h1>🛡️ CS Intelligence <span style='color:#F6A41A'>AI Edition</span></h1>", unsafe_allow_html=True)
st.markdown(f"Análise Estratégica para: **{nome_cliente if nome_cliente else 'Nova Consulta'}**")

# LINHA 1: RISCO (RESTAUROU VISITAS, CALLS E QBR POR COHORT)
st.markdown("### 📉 Avaliação de Risco (Operacional & Relacionamento)")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("**Saúde do Serviço (SLA)**")
        vol_chamados = st.selectbox("Volume de Chamados", ["Adequado / Estável", "Muito Baixo (Silêncio)", "Alto (Instabilidade)", "Crítico (Incidentes Graves)"])
        sla_mes = st.slider("SLA Atingido (%)", 50, 100, 98)
with r2:
    with st.container(border=True):
        st.markdown("**Engajamento Contínuo**")
        # Restauro das visitas e online
        if local == "SP (Local)":
            visitas = st.slider("Visitas Presenciais", 0, 5, 1)
            online = st.slider("Calls Online", 0, 10, 2)
        else:
            online = st.slider("Calls Online (Meta: 2)", 0, 10, 2)
            visitas = 0
            
        # Restauro das 3 opções do Book
        book_st = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        
        # Inteligência da QBR baseada no Tier
        if cohort in ["Diamante", "Ouro", "Prata"]:
            qbr_st = st.radio("QBR no Prazo?", ["Sim", "Não"], horizontal=True)
        else:
            qbr_st = "N/A"
            st.caption("ℹ️ *QBR não aplicável para tier Bronze.*")
            
with r3:
    with st.container(border=True):
        st.markdown("**Satisfação Percebida**")
        # Restauro do Toggle de NPS
        tem_nps = st.toggle("Cliente respondeu NPS recente?", value=True)
        if tem_nps: 
            nps_nota = st.slider("Nota NPS (0-10)", 0, 10, 8)
        else: 
            nps_nota = None
            st.warning("⚖️ Peso do NPS redistribuído nas outras métricas.")

st.write("---")

# LINHA 2: POTENCIAL (LEGENDAS ABC RESTAURADAS)
st.markdown("### 🚀 Avaliação de Potencial & Fit")
p1, p2, p3 = st.columns(3)

with p1:
    with st.container(border=True):
        st.markdown("**Representatividade (MRR)**")
        receita_abc = st.slider("Score Financeiro", 0, 100, 50, key="abc")
        st.caption("**Curva ABC:**<br>• **80-100:** Estratégico (Top faturamento)<br>• **40-79:** Médio Impacto<br>• **0-39:** Contas Pequenas", unsafe_allow_html=True)

with p2:
    with st.container(border=True):
        st.markdown("**Fit Operacional**")
        fit_tecnico = st.slider("Alinhamento Stack", 0, 100, 70, key="fit")
        st.caption("**Alinhamento Strati:**<br>O quanto o cliente segue nossos padrões técnicos e confia na nossa stack oficial.", unsafe_allow_html=True)

with p3:
    with st.container(border=True):
        st.markdown("**Expansão (White Space)**")
        exp_ws = st.slider("Potencial de Novos Negócios", 0, 100, 30, key="exp")
        st.caption("**Novas Torres:**<br>Mapeie se há torres (Segurança, Cloud, Guardian) que o cliente ainda não contratou.", unsafe_allow_html=True)

st.write("")

if st.button("PROCESSAR RECLASSIFICAÇÃO COM IA"):
    if not nome_cliente: st.error("⚠️ Por favor, insira o nome do cliente.")
    else:
        # LÓGICA DE CÁLCULO ATUALIZADA
        score_vol = {"Adequado / Estável": 100, "Muito Baixo (Silêncio)": 30, "Alto (Instabilidade)": 50, "Crítico (Incidentes Graves)": 10}[vol_chamados]
        saude_servico = (score_vol * 0.6) + (sla_mes * 0.4)
        
        # Presença
        if local == "SP (Local)":
            meta_v = 2 if fase_jornada == 'Onboarding' else (1 if fase_jornada == 'Adoção' else 0.5)
            score_presenca = 100 if meta_v == 0 else min((visitas/meta_v)*100, 100.0)
            bonus_online = min(online*2, 10)
        else:
            score_presenca = min((online/2)*100, 100.0)
            bonus_online = 0 if visitas == 0 else 10 
            
        # Book de Serviços
        book_pts = 100 if book_st == 'Apresentado' else (50 if book_st == 'Enviado' else 0)
        
        # Engajamento com regra de Cohort (Bronze não dilui nota com QBR)
        if cohort in ["Diamante", "Ouro", "Prata"]:
            qbr_pts = 100 if qbr_st == 'Sim' else 0
            engajamento = min((score_presenca*0.5) + ((qbr_pts + book_pts)/2*0.5) + bonus_online, 100.0)
        else:
            engajamento = min((score_presenca*0.5) + (book_pts * 0.5) + bonus_online, 100.0)
            
        # Risco e Potencial Final
        nps_score = nps_nota * 10 if tem_nps else 50
        risco_f = ((100 - saude_servico) * 0.4) + ((100 - engajamento) * 0.3) + ((100 - nps_score) * 0.3)
        potencial_f = (receita_abc * 0.4) + (fit_tecnico * 0.3) + (exp_ws * 0.3)
        
        # Geração de Gatilhos para IA
        gats = []
        if sla_mes < 90: gats.append("SLA Crítico")
        if tem_nps and nps_nota <= 6: gats.append("Cliente Detrator")
        if cohort in ["Diamante", "Ouro", "Prata"] and qbr_st == 'Não': gats.append(f"QBR Atrasada para Conta {cohort}")
        if not gats: gats.append("Operação técnica controlada, sem red flags.")
        
        # Dashboard de Gráficos
        res1, res2 = st.columns(2)
        with res1:
            st.plotly_chart(create_gauge("Nível de Risco", risco_f, [
                {'range': [0, 40], 'color': "#22c55e"}, 
                {'range': [40, 65], 'color': "#f97316"}, 
                {'range': [65, 100], 'color': "#ef4444"}]), use_container_width=True)
        with res2:
            st.plotly_chart(create_gauge("Potencial Expansão", potencial_f, [
                {'range': [0, 40], 'color': "#94a3b8"}, 
                {'range': [40, 75], 'color': "#189CD8"}, 
                {'range': [75, 100], 'color': "#95C11F"}]), use_container_width=True)

        # PLAYBOOK IA
        st.write("---")
        with st.spinner("🤖 Gemini AI gerando estratégia personalizada..."):
            analise_ia = gerar_playbook_ia({
                'cohort': cohort, 'fase': fase_jornada, 'Risco': int(risco_f), 'Potencial': int(potencial_f),
                'Servico': int(saude_servico), 'Engajamento': int(engajamento), 
                'NPS': nps_nota if tem_nps else "Não respondeu", 'gatilhos': " | ".join(gats)
            })
            
            st.markdown("### 📋 Diagnóstico de Inteligência")
            st.markdown(f"""
            <div style="background-color:rgba(246, 164, 26, 0.1); padding:25px; border-radius:15px; border-left: 6px solid #F6A41A;">
                {analise_ia.replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            # SALVAR NO GOOGLE SHEETS
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Página1", ttl=0)
                nova_linha = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Cliente": nome_cliente, "Tier": cohort, "Risco": f"{risco_f:.1f}%",
                    "Potencial": f"{potencial_f:.1f}%", "Playbook IA": analise_ia
                }])
                conn.update(worksheet="Página1", data=pd.concat([df, nova_linha], ignore_index=True))
                st.toast("✅ Análise arquivada com sucesso!", icon="📊")
            except:
                st.warning("⚠️ Erro ao salvar na planilha, mas a análise foi concluída.")
