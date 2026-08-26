import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time
import os
import plotly.graph_objects as go
import google.generativeai as genai

# ==================================================
# ⚙️ CONFIGURAÇÕES INICIAIS DA SUA NOVA EMPRESA
# ==================================================
NOME_PLATAFORMA = "Reten.AI"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title=f"{NOME_PLATAFORMA} | CS Intelligence", layout="wide", page_icon="⚡")

# --- CONFIGURAÇÃO GEMINI AI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("⚠️ Erro de Conexão IA: Verifique a GEMINI_API_KEY nos Secrets.")

# ==================================================
# 🎨 NOVO UI/UX DESIGN SYSTEM (DARK MODE MODERNO)
# ==================================================
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Space+Grotesk:wght@500;700&display=swap');

        /* Paleta: Fundo Escuro, Botões Indigo (#6366f1), Detalhes Ciano (#06b6d4) */
        
        .stApp {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at top left, #1e1b4b, #0f172a 40%, #020617 100%);
            color: #e2e8f0;
        }

        [data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.7) !important;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-right: 1px solid rgba(99, 102, 241, 0.15);
        }

        h1, h2, h3, h4, h5 { 
            font-family: 'Space Grotesk', sans-serif !important; 
            font-weight: 700; 
            letter-spacing: -0.5px;
            color: #ffffff !important; 
        }
        
        /* NOVO BOTÃO PRINCIPAL */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: white; 
            border: 1px solid rgba(99, 102, 241, 0.5);
            padding: 20px; 
            border-radius: 12px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700; 
            font-size: 16px; 
            letter-spacing: 1px;
            width: 100%; 
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            text-transform: uppercase;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }

        /* SLIDERS */
        div[data-baseweb="slider"] div[role="slider"] { 
            background-color: #06b6d4 !important; 
            border: 3px solid #0f172a !important; 
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }
        div[data-baseweb="slider"] > div > div > div:first-child { 
            background-color: #06b6d4 !important; 
        }

        /* CARDS / CONTAINERS */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            background: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            padding: 24px;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, border 0.3s ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border: 1px solid rgba(6, 182, 212, 0.3);
            transform: translateY(-2px);
        }
        
        .st-bb { background-color: transparent; }
        
        /* BOX DO PLAYBOOK DA IA */
        .ai-playbook-box {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.9) 0%, rgba(2, 6, 23, 0.95) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-left: 6px solid #06b6d4;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            font-size: 15px;
            line-height: 1.6;
            color: #f1f5f9;
        }
        .ai-playbook-box h1, .ai-playbook-box h2, .ai-playbook-box h3 {
            color: #06b6d4 !important;
            font-size: 18px;
            margin-top: 15px;
            margin-bottom: 10px;
        }

        .stCaption { color: #cbd5e1 !important; font-size: 13px !important; font-weight: 500; }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
        ::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.8); }
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
            
            # NOVO LOGO EM SVG (VETOR 100% NO CÓDIGO) E TIPOGRAFIA
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; margin-bottom: 20px;">
                <svg width="70" height="70" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="gradLogo" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <!-- Hexágono Base (Escudo de Retenção) -->
                    <path d="M50 5 L90 25 L90 75 L50 95 L10 75 L10 25 Z" fill="rgba(99, 102, 241, 0.05)" stroke="url(#gradLogo)" stroke-width="4" stroke-linejoin="round"/>
                    <!-- Letra R Abstrata e IA Nodes -->
                    <path d="M35 35 L35 70 M35 35 C 55 25, 65 40, 50 55 L35 55 M50 55 L65 75" fill="none" stroke="url(#gradLogo)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- Pontos Neurais (IA) -->
                    <circle cx="35" cy="35" r="5" fill="#06b6d4" />
                    <circle cx="65" cy="75" r="5" fill="#6366f1" />
                </svg>
                <h1 style='text-align: center; color: #ffffff !important; font-size: 2.8rem; margin-top: 10px; margin-bottom: 0px;'>Reten<span style='color: #06b6d4;'>.AI</span></h1>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 20px;'>Acesso Restrito - Consultoria Estratégica</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Credencial de Acesso")
                p = st.text_input("Código de Segurança", type="password")
                t = st.text_input("Token MFA (Opcional)", help="Apenas para administradores do sistema")
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
# ==================================================
# 🧠 CÉREBRO RETEN.AI (PROMPT ENGENHARIA AVANÇADA)
# ==================================================
def gerar_playbook_ia(d):
    prompt = f"""
    Atue como um Consultor Sênior de Customer Success e Retenção de Receita. 
    Sua missão é analisar os dados de telemetria deste cliente e gerar um Playbook Tático de Recuperação e Expansão. 
    Este relatório será apresentado para o CEO e Diretores da empresa que atende este cliente.

    DADOS DO CLIENTE E TELEMETRIA:
    - Setor de Atuação: {d['segmento']}
    - Tier/Cohort: {d['cohort']}
    - Fase da Jornada: {d['fase']}
    - Risco de Churn (Algoritmo Reten.AI): {d['Risco']}%
    - Potencial de Expansão (Algoritmo Reten.AI): {d['Potencial']}%
    - Saúde do Serviço Técnico: {d['Servico']}/100
    - Score de Engajamento: {d['Engajamento']}/100
    - Satisfação (NPS): {d['NPS']}
    
    GATILHOS DE ALERTA IDENTIFICADOS: {d['gatilhos']}
    
    DIRETRIZES DE SAÍDA (Formate rigorosamente em Markdown com os seguintes cabeçalhos):
    
    ### 📊 1. DIAGNÓSTICO EXECUTIVO
    (Escreva 1 parágrafo letal e direto ao ponto resumindo o cenário atual da conta. Foque no risco financeiro e no impacto dos gatilhos identificados. Use um tom consultivo e de urgência se o risco for alto.)
    
    ### 🗺️ 2. PLANO DE AÇÃO TÁTICO (30-60-90 Dias)
    (Crie um roadmap em bullet points com ações práticas para a equipe de CS e Operações. Sem jargões vazios, diga O QUE fazer e COMO fazer baseado no setor de {d['segmento']})
    * **Dia 1 ao 30 (Estancar Sangramento / Quick Wins):** (Liste 2 ações críticas)
    * **Dia 31 ao 60 (Estabilização e Valor):** (Liste 2 ações focadas em adoção/engajamento)
    * **Dia 61 ao 90 (Prevenção e QBR):** (Liste 1 ação para garantir retenção de longo prazo)
    
    ### 💰 3. ESTRATÉGIA DE EXPANSÃO (CROSS-SELL/UPSELL)
    (Considerando que o potencial de expansão é de {d['Potencial']}%, sugira 1 abordagem prática de como o CS pode plantar uma semente de venda de novos serviços. Justifique essa sugestão com as dores típicas de empresas do setor de {d['segmento']})
    
    Regras estritas: 
    - Não use introduções cordiais ("Olá", "Claro, aqui está"). 
    - Vá direto ao conteúdo.
    - O tom deve ser de um especialista cobrando caro pela consultoria: assertivo, analítico e pragmático.
    """
    try:
        modelo_correto = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo_correto = m.name
                break
        if not modelo_correto: return "⚠️ Erro: API Key sem permissão de texto."
        
        # Temperatura baixa para output executivo
        model_dinamico = genai.GenerativeModel(
            model_name=modelo_correto,
            generation_config={"temperature": 0.3} 
        )
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
        title = {'text': label, 'font': {'family': 'Space Grotesk', 'size': 20, 'color': '#cbd5e1'}},
        number = {'suffix': "%", 'font': {'family': 'Space Grotesk', 'size': 36, 'color': '#ffffff', 'weight': 'bold'}},
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
    st.markdown(f"<h2 style='text-align: center; color: #6366f1 !important; font-size: 24px;'>{NOME_PLATAFORMA}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 12px; margin-top:-10px;'>CS Intelligence Engine</p>", unsafe_allow_html=True)
    st.write("---")
    nome_cliente = st.text_input("Nome da Conta", placeholder="Ex: Corporação Alpha")
    segmento = st.selectbox("Setor de Atuação", ["Tecnologia / SaaS", "Saúde / Clínicas", "Varejo / E-commerce", "Indústria / Manufatura", "Serviços B2B / Consultoria", "Educação", "Financeiro / Contabilidade", "Outro"])
    cohort = st.selectbox("Tier de Serviço", ["Diamante", "Ouro", "Prata", "Bronze"])
    local = st.radio("Formato de Atendimento", ["Local (Presencial)", "Remoto"], horizontal=True)
    
    st.write("---")
    fase_jornada = st.selectbox("Fase do Ciclo de Vida", ['Onboarding', 'Adoção', 'Retenção'])
    if fase_jornada == 'Onboarding': st.caption("🎯 **0-6 meses:** Foco em implementação.")
    elif fase_jornada == 'Adoção': st.caption("⚙️ **6-24 meses:** Foco em uso recorrente.")
    else: st.caption("🤝 **+24 meses:** Expansão e renovação.")
        
    st.write("---")
    st.markdown("### 📈 Parâmetros Operacionais")
    vol_chamados = st.selectbox("Volume de Chamados", ["Adequado / Estável", "Muito Baixo (Silêncio)", "Alto (Instabilidade)", "Crítico (Incidentes Graves)"])
    sla_mes = st.slider("SLA Atingido (%)", 50, 100, 98)
    
    st.write("")
    if st.button("🚪 Encerrar Sessão", type="secondary"): st.session_state.clear(); st.rerun()

st.markdown(f"<h1>⚡ {NOME_PLATAFORMA} <span style='color:#06b6d4'>Intelligence</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 18px; color: #cbd5e1;'>Motor de diagnóstico e estratégia para: <strong style='color: white;'>{nome_cliente if nome_cliente else 'Nova Consulta'}</strong></p>", unsafe_allow_html=True)
st.write("")

# LINHA 1: RISCO
st.markdown("### 📉 Telemetria de Risco (Operação & Relacionamento)")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600; color: #6366f1;'>1. Saúde do Serviço</p>", unsafe_allow_html=True)
        st.caption(f"**Carga Base:** {vol_chamados}<br>**SLA Medido:** {sla_mes}%", unsafe_allow_html=True)
with r2:
    with st.container(border=True):
        st.markdown("<p style='font-weight: 600; color: #06b6d4;'>2. Matriz de Engajamento</p>", unsafe_allow_html=True)
        if local == "Local (Presencial)":
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
        st.markdown("<p style='font-weight: 600; color: #10b981;'>3. Sentimento (NPS)</p>", unsafe_allow_html=True) 
        tem_nps = st.toggle("Possui coleta recente?", value=True)
        if tem_nps: nps_nota = st.slider("Score Promoter (0-10)", 0, 10, 8)
        else: nps_nota = None; st.caption("Algoritmo calibrado para ausência de NPS.")

st.write("---")

# LINHA 2: POTENCIAL
st.markdown("### 🚀 Vetores de Expansão & Fit")
p1, p2, p3 = st.columns(3)

with p1:
    with st.container(border=True):
        st.markdown("**Representatividade MRR**")
        st.markdown("<p style='font-size: 14px; margin-bottom:5px; font-weight:600; color:#cbd5e1;'>Impacto Financeiro</p>", unsafe_allow_html=True)
        
        mrr_total = st.number_input("MRR Total da Empresa (R$)", value=1000000, step=50000, key="mrr_tot")
        mrr_cliente = st.number_input("MRR deste Cliente (R$)", value=50000, step=5000, key="mrr_cli")
        
        participacao = (mrr_cliente / mrr_total) * 100 if mrr_total > 0 else 0
        
        if participacao < 1: receita_abc = participacao * 40
        elif participacao < 5: receita_abc = 40 + ((participacao - 1) / 4) * 40
        else: receita_abc = min(80 + ((participacao - 5) / 5) * 20, 100.0)
            
        st.markdown(f"<p style='font-size: 13px; color: #6366f1; font-weight:bold; margin-top:8px; margin-bottom:8px;'>Impacto de perda em Churn: {participacao:.2f}% do faturamento geral<br>Score de Impacto: {receita_abc:.1f}/100</p>", unsafe_allow_html=True)
        st.caption("**Legenda - Impacto Financeiro:**<br>• **80-100 (Crítico - Curva A):** A conta representa 5% ou mais do faturamento total.<br>• **40-79 (Médio - Curva B):** Entre 1% e 4.9% do faturamento.<br>• **0-39 (Baixo - Curva C):** Menos de 1% do faturamento.", unsafe_allow_html=True)

with p2:
    with st.container(border=True):
        st.markdown("**Alinhamento de Stack**")
        fit_tecnico = st.slider("Score de Fit Técnico", 0, 100, 70, key="fit")
        st.caption("<br>**Legenda - Score de Fit Técnico:**<br>• **80-100 (Alto):** Utiliza as ferramentas homologadas e segue as boas práticas.<br>• **40-79 (Médio):** Aderência parcial; possui sistemas paralelos.<br>• **0-39 (Baixo):** Uso massivo de soluções desalinhadas com a stack oficial.", unsafe_allow_html=True)

with p3:
    with st.container(border=True):
        st.markdown("**White Space Analysis**")
        exp_ws = st.slider("Oportunidade Cross-sell", 0, 100, 30, key="exp")
        st.caption("<br>**Legenda - Oportunidade Cross-sell:**<br>• **80-100 (Alta):** Cliente não possui a maioria dos serviços cruciais do portfólio.<br>• **40-79 (Média):** Há espaço claro para venda de novos serviços.<br>• **0-39 (Baixa):** Cliente já contratou quase a totalidade do portfólio.", unsafe_allow_html=True)

st.write("")
st.write("")

if st.button(f"GERAR DIAGNÓSTICO {NOME_PLATAFORMA.upper()}"):
    if not nome_cliente: st.error("⚠️ Identificação da conta é obrigatória para processamento.")
    else:
        score_vol = {"Adequado / Estável": 100, "Muito Baixo (Silêncio)": 30, "Alto (Instabilidade)": 50, "Crítico (Incidentes Graves)": 10}[vol_chamados]
        saude_servico = (score_vol * 0.6) + (sla_mes * 0.4)
        
        if local == "Local (Presencial)":
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
        
        # Cores ajustadas para combinar com a nova UI
        with res1:
            st.plotly_chart(create_gauge("Índice de Risco", risco_f, [{'range': [0, 40], 'color': "rgba(16, 185, 129, 0.6)"}, {'range': [40, 65], 'color': "rgba(245, 158, 11, 0.6)"}, {'range': [65, 100], 'color': "rgba(239, 68, 68, 0.6)"}]), use_container_width=True)
        with res2:
            st.plotly_chart(create_gauge("Score de Potencial", potencial_f, [{'range': [0, 40], 'color': "rgba(148, 163, 184, 0.6)"}, {'range': [40, 75], 'color': "rgba(6, 182, 212, 0.6)"}, {'range': [75, 100], 'color': "rgba(99, 102, 241, 0.6)"}]), use_container_width=True)

        st.write("")
        with st.spinner(f"🔄 Conectando aos servidores {NOME_PLATAFORMA} para síntese estratégica..."):
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
                st.toast("✅ Telemetria e Playbook sincronizados com sucesso no Data Lake (Sheets).", icon="💾")
            except Exception as e:
                st.warning(f"⚠️ Alerta de Sincronização: {e}")
