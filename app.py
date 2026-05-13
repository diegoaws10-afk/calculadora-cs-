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
except:
    st.error("⚠️ Erro de Conexão IA: Verifique a GEMINI_API_KEY nos Secrets.")

# ==================================================
# 🎨 UI/UX DESIGN SYSTEM (GLASSMORPHISM & TECH)
# ==================================================
def load_css():
    st.markdown("""
        <style>
        /* IMPORTAÇÃO DE FONTES TECNOLÓGICAS E MODERNAS */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        /* FUNDO GLOBAL: DARK MODE PROFUNDO + IMAGEM COM OVERLAY GRADIENTE */
        .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: linear-gradient(135deg, rgba(8, 10, 16, 0.95) 0%, rgba(15, 23, 42, 0.85) 100%), url("https://raw.githubusercontent.com/sua_conta/seu_repo/main/background_strati.png");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #e2e8f0;
        }

        /* SIDEBAR ESTILO FROSTED GLASS (VIDRO FOSCO) */
        [data-testid="stSidebar"] {
            background-color: rgba(10, 15, 28, 0.65) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* TIPOGRAFIA DE TÍTULOS (OUTFIT) */
        h1, h2, h3, h4, h5 { 
            font-family: 'Outfit', sans-serif !important; 
            font-weight: 800; 
            letter-spacing: -0.5px;
            color: #ffffff !important; 
        }
        
        /* BOTÃO PRINCIPAL (NEON GLOW + PULSO) */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #F6A41A 0%, #E05C00 100%);
            color: white; 
            border: 1px solid rgba(246, 164, 26, 0.4);
            padding: 20px; 
            border-radius: 16px;
            font-family: 'Outfit', sans-serif;
            font-weight: 800; 
            font-size: 18px; 
            letter-spacing: 1px;
            width: 100%; 
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 0 15px rgba(246, 164, 26, 0.2);
            text-transform: uppercase;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-3px) scale(1.02); 
            box-shadow: 0 10px 30px rgba(246, 164, 26, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.4);
        }

        /* SLIDERS MODERNIZADOS (AZUL STRATI GUARDIAN) */
        div[data-baseweb="slider"] div[role="slider"] { 
            background-color: #189CD8 !important; 
            border: 3px solid #0f172a !important; 
            box-shadow: 0 0 10px rgba(24, 156, 216, 0.5);
        }
        div[data-baseweb="slider"] > div > div > div:first-child { 
            background-color: #189CD8 !important; 
        }

        /* CARDS & CONTAINERS (GLASSMORPHISM) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 20px;
            background: rgba(30, 41, 59, 0.25) !important;
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, border 0.3s ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border: 1px solid rgba(246, 164, 26, 0.3);
            transform: translateY(-2px);
        }

        /* TOGGLES E RADIOS */
        .st-bb { background-color: transparent; }
        
        /* CAIXA DE RESULTADO DA IA (CYBERBOX) */
        .ai-playbook-box {
            background: linear-gradient(145deg, rgba(20, 24, 39, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(246, 164, 26, 0.3);
            border-left: 6px solid #F6A41A;
            padding: 30px;
            border-radius: 16px;
            box-shadow: inset 0 0 20px rgba(246, 164, 26, 0.05), 0 10px 30px rgba(0,0,0,0.5);
            font-size: 15px;
            line-height: 1.6;
            color: #f1f5f9;
        }
        .ai-playbook-box h1, .ai-playbook-box h2, .ai-playbook-box h3 {
            color: #F6A41A !important;
            font-size: 18px;
            margin-top: 15px;
            margin-bottom: 10px;
        }

        /* LEGENDAS MAIS SUTIS */
        .stCaption { color: #94a3b8 !important; font-size: 13px !important; font-weight: 500; }
        
        /* SCROLLBAR CUSTOMIZADA */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
        ::-webkit-scrollbar-thumb { background: rgba(246, 164, 26, 0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(246, 164, 26, 0.8); }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ==================================================
# 🔐 SEGURANÇA (AUTENTICAÇÃO)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False): return True
    col_vazia_top = st.empty(); col_vazia_top.markdown("<br><br><br><br>", unsafe_allow_html=True)
    c_esq, c_centro, c_dir = st.columns([1, 1.2, 1])
    with c_centro:
        with st.container(border=True):
            if os.path.exists("strati_logo.png"): st.image("strati_logo.png", use_column_width=True)
            else: st.markdown("<h1 style='text-align: center; color: #F6A41A !important; font-size: 3rem;'>STRATI<span style='color: white;'>.AI</span></h1>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 20px;'>Autenticação Segura de Sistema</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Credencial de Acesso")
                p = st.text_input("Código de Segurança", type="password")
                t = st.text_input("Token MFA (Nível Admin)")
                st.write("")
                if st.form_submit_button("INICIAR SESSÃO"):
                    if u in st.secrets["passwords"] and p == st.secrets["passwords"][u]:
                        if u == "diego_admin":
                            totp = pyotp.TOTP(st.secrets["mfa"]["secret_key"])
                            if totp.verify(t.replace(" ", "")):
                                st.session_state["authenticated"] = True; st.session_state["user_logado"] = u; st.rerun()
                            else: st.error("Falha de Autenticação MFA.")
                        else:
                            st.session_state["authenticated"] = True; st.session_state["user_logado"] = u; st.rerun()
                    else: st.error("Acesso Negado.")
    return False

if not check_authentication(): st.stop()

# ==================================================
# 🧠 IA STRATI (PROMPT ENGENHARIA)
# ==================================================
def gerar_playbook_ia(d):
    prompt = f"""
    Aja como um Diretor de Customer Success para MSPs. Analise este cenário e gere um playbook tático de alto impacto:
    - Setor de Atuação: {d['segmento']}
    - Tier/Cohort: {d['cohort']}
    - Fase da Jornada: {d['fase']}
    - Risco Atual: {d['Risco']}% | Potencial: {d['Potencial']}%
    - Saúde Técnica (SLA/Chamados): {d['Servico']}/100
    - Engajamento: {d['Engajamento']}/100
    - Satisfação (NPS): {d['NPS']}
    
    Contexto Crítico: {d['gatilhos']}
    
    Formate sua resposta rigorosamente em 3 seções:
    ### 🎯 ESTRATÉGIA MACRO
    (Uma frase forte conectando o direcional da conta ao negócio/setor do cliente)
    
    ### 🛠️ AÇÕES IMEDIATAS
    (3 tópicos curtos e acionáveis)
    
    ### 💡 INSIGHT DE EXPANSÃO
    (Como vender mais serviços como Segurança, Cloud ou Guardian, justificando com as dores típicas do setor de {d['segmento']})
    
    Use tom executivo e não cite nomes fictícios.
    """
    try:
        modelo_correto = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo_correto = m.name
                break
        if not modelo_correto: return "⚠️ Erro: API Key sem permissão de texto."
        
        model_dinamico = genai.GenerativeModel(modelo_correto)
        response = model_dinamico.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro detalhado da IA: {str(e)}"

# ==================================================
# 📊 GRÁFICOS (GAUGE CUSTOMIZADOS)
# ==================================================
def create_gauge(label, value, color_steps):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': label, 'font': {'family': 'Outfit', 'size': 20, 'color': '#cbd5e1'}},
        number = {'suffix': "%", 'font': {'family': 'Outfit', 'size': 36, 'color': '#ffffff', 'weight': 'bold'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "rgba(255,255,255,0.2)", 'tickwidth': 1},
            'bar': {'color': "rgba(255,255,255,0.8)", 'thickness': 0.15},
            'bgcolor': "rgba(0,0,0,0.2)",
            'steps': color_steps,
            'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.8, 'value': value}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=220, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# ==================================================
# 🖥️ INTERFACE PRINCIPAL
# ==================================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #F6A41A !important; font-size: 24px;'>STRATI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 12px; margin-top:-10px;'>CS Intelligence Engine</p>", unsafe_allow_html=True)
    st.write("---")
    nome_cliente = st.text_input("Nome da Conta", placeholder="Ex: Corporação Alpha")

    segmento = st.selectbox("Setor de Atuação", ["Tecnologia / SaaS", "Saúde / Clínicas", "Varejo / E-commerce", "Indústria / Manufatura", "Serviços B2B / Consultoria", "Educação", "Financeiro / Contabilidade", "Outro"])
    cohort = st.selectbox("Tier de Serviço", ["Diamante", "Ouro", "Prata", "Bronze"])
    local = st.radio("Localização Física", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    
    st.write("---")
    fase_jornada = st.selectbox("Fase do Ciclo de Vida", ['Onboarding', 'Adoção', 'Retenção'])
    if fase_jornada == 'Onboarding': st.caption("🎯 **0-6 meses:** Foco em implementação.")
    elif fase_jornada == 'Adoção': st.caption("⚙️ **6-24 meses:** Foco em estabilidade.")
    else: st.caption("🤝 **+24 meses:** Expansão e parceria estratégica.")
        
    st.write("---")
    st.markdown("### ⚡ Telemetria Base")
    vol_chamados = st.selectbox("Volume de Chamados", ["Adequado / Estável", "Muito Baixo (Silêncio)", "Alto (Instabilidade)", "Crítico (Incidentes Graves)"])
    sla_mes = st.slider("SLA Atingido (%)", 50, 100, 98)
    
    st.write("")
    if st.button("🚪 Encerrar Sessão", type="secondary"): st.session_state.clear(); st.rerun()

st.markdown(f"<h1>🛡️ STRATI <span style='color:#F6A41A'>CS AI</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 18px; color: #cbd5e1;'>Motor de diagnóstico e estratégia para: <strong style='color: white;'>{nome_cliente if nome_cliente else 'Nova Consulta'}</strong></p>", unsafe_allow_html=True)
st.write("")

# LINHA 1: RISCO
st.markdown("### 📉 Telemetria de Risco (Operação & Relacionamento)")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600; color: #F6A41A;'>1. Saúde do Serviço</p>", unsafe_allow_html=True)
        st.caption(f"**Carga Base:** {vol_chamados}<br>**SLA Medido:** {sla_mes}%", unsafe_allow_html=True)
with r2:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600; color: #189CD8;'>2. Matriz de Engajamento</p>", unsafe_allow_html=True)
        if local == "SP (Local)":
            visitas = st.slider("Touchpoints Físicos", 0, 5, 1)
            online = st.slider("Touchpoints Digitais", 0, 10, 2)
        else:
            online = st.slider("Touchpoints Digitais", 0, 10, 2)
            visitas = 0
            
        book_st = st.selectbox("Status do Book", ["Apresentado", "Enviado", "Não realizado"])
        if cohort in ["Diamante", "Ouro", "Prata"]: qbr_st = st.radio("EBR/QBR Executada?", ["Sim", "Não"], horizontal=True)
        else: qbr_st = "N/A"; st.caption("ℹ️ *By-pass de QBR ativado (Tier Bronze).*")
            
with r3:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600; color: #95C11F;'>3. Sentimento (NPS)</p>", unsafe_allow_html=True)
        tem_nps = st.toggle("Possui coleta recente?", value=True)
        if tem_nps: nps_nota = st.slider("Score Promoter (0-10)", 0, 10, 8)
        else: nps_nota = None; st.caption("Algoritmo calibrado para ausência de NPS.")

st.write("---")

# LINHA 2: POTENCIAL
st.markdown("### 🚀 Vetores de Expansão & Fit")
p1, p2, p3 = st.columns(3)
with p1:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600;'>Representatividade MRR</p>", unsafe_allow_html=True)
        receita_abc = st.slider("Impacto Financeiro", 0, 100, 50, key="abc")
with p2:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600;'>Alinhamento de Stack</p>", unsafe_allow_html=True)
        fit_tecnico = st.slider("Score de Fit Técnico", 0, 100, 70, key="fit")
with p3:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600;'>White Space Analysis</p>", unsafe_allow_html=True)
        exp_ws = st.slider("Oportunidade Cross-sell", 0, 100, 30, key="exp")

st.write("")
st.write("")

if st.button("PROCESSAR MOTOR NEURAL STRATI"):
    if not nome_cliente: st.error("⚠️ Identificação da conta é obrigatória para processamento.")
    else:
        # LÓGICA DE CÁLCULO
        score_vol = {"Adequado / Estável": 100, "Muito Baixo (Silêncio)": 30, "Alto (Instabilidade)": 50, "Crítico (Incidentes Graves)": 10}[vol_chamados]
        saude_servico = (score_vol * 0.6) + (sla_mes * 0.4)
        
        if local == "SP (Local)":
            meta_v = 2 if fase_jornada == 'Onboarding' else (1 if fase_jornada == 'Adoção' else 0.5)
            score_presenca = 100 if meta_v == 0 else min((visitas/meta_v)*100, 100.0)
            bonus_online = min(online*2, 10)
        else:
            score_presenca = min((online/2)*100, 100.0)
            bonus_online = 0 if visitas == 0 else 10 
            
        book_pts = 100 if book_st == 'Apresentado' else (50 if book_st == 'Enviado' else 0)
        
        if cohort in ["Diamante", "Ouro", "Prata"]:
            qbr_pts = 100 if qbr_st == 'Sim' else 0
            engajamento = min((score_presenca*0.5) + ((qbr_pts + book_pts)/2*0.5) + bonus_online, 100.0)
        else:
            engajamento = min((score_presenca*0.5) + (book_pts * 0.5) + bonus_online, 100.0)
            
        nps_score = nps_nota * 10 if tem_nps else 50
        risco_f = ((100 - saude_servico) * 0.4) + ((100 - engajamento) * 0.3) + ((100 - nps_score) * 0.3)
        potencial_f = (receita_abc * 0.4) + (fit_tecnico * 0.3) + (exp_ws * 0.3)
        
        gats = []
        if sla_mes < 90: gats.append("SLA Crítico")
        if tem_nps and nps_nota <= 6: gats.append("Cliente Detrator")
        if cohort in ["Diamante", "Ouro", "Prata"] and qbr_st == 'Não': gats.append(f"Ausência de QBR no tier {cohort}")
        if not gats: gats.append("Parâmetros técnicos estáveis.")
        
        st.write("---")
        st.markdown("### 📊 Dashboards de Compilação")
        res1, res2 = st.columns(2)
        with res1:
            st.plotly_chart(create_gauge("Índice de Risco", risco_f, [{'range': [0, 40], 'color': "rgba(34, 197, 94, 0.6)"}, {'range': [40, 65], 'color': "rgba(249, 115, 22, 0.6)"}, {'range': [65, 100], 'color': "rgba(239, 68, 68, 0.6)"}]), use_container_width=True)
        with res2:
            st.plotly_chart(create_gauge("Score de Potencial", potencial_f, [{'range': [0, 40], 'color': "rgba(148, 163, 184, 0.6)"}, {'range': [40, 75], 'color': "rgba(24, 156, 216, 0.6)"}, {'range': [75, 100], 'color': "rgba(149, 193, 31, 0.6)"}]), use_container_width=True)

        st.write("")
        with st.spinner("🔄 Conectando aos servidores Gemini para síntese estratégica..."):
            analise_ia = gerar_playbook_ia({
                'segmento': segmento, 'cohort': cohort, 'fase': fase_jornada, 
                'Risco': int(risco_f), 'Potencial': int(potencial_f),
                'Servico': int(saude_servico), 'Engajamento': int(engajamento), 
                'NPS': nps_nota if tem_nps else "Não respondeu", 'gatilhos': " | ".join(gats)
            })
            
            st.markdown("### 🤖 Output de Inteligência Artificial")
            st.markdown(f"""
            <div class="ai-playbook-box">
                {analise_ia}
            </div>
            """, unsafe_allow_html=True)
            
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Página1", ttl=0)
                nova_linha = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Cliente": nome_cliente,
                    "Segmento": segmento,
                    "Tier": cohort, 
                    "Fase": fase_jornada,
                    "Risco": f"{risco_f:.1f}%",
                    "Potencial": f"{potencial_f:.1f}%", 
                    "Playbook IA": analise_ia
                }])
                conn.update(worksheet="Página1", data=pd.concat([df, nova_linha], ignore_index=True))
                st.toast("✅ Telemetria e Playbook sincronizados no Data Lake (Sheets).", icon="💾")
            except Exception as e:
                st.warning(f"⚠️ Alerta de Sincronização: {e}")
