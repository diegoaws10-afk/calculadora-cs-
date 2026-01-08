import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Strati | CS Intelligence", layout="wide", page_icon="🛡️")

# ==================================================
# 🎨 DESIGN SYSTEM (CSS INJETADO)
# ==================================================
def local_css():
    st.markdown("""
        <style>
        /* Importando Fontes Modernas */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Montserrat:wght@600;700&display=swap');

        /* Fundo Geral da Aplicação */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }

        /* Sidebar - Visual Profissional */
        [data-testid="stSidebar"] {
            background-color: #0b1120;
            border-right: 1px solid #334155;
        }

        /* Títulos e Cabeçalhos */
        h1, h2, h3 {
            font-family: 'Montserrat', sans-serif !important;
            color: #ffffff !important;
            font-weight: 700;
        }
        
        /* Ajuste do Título Principal para destaque */
        h1 {
            text-shadow: 0px 4px 10px rgba(0,0,0,0.3);
            background: -webkit-linear-gradient(0deg, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Cartões (Containers) - Efeito Glassmorphism */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 20px;
            backdrop-filter: blur(10px);
        }

        /* Botões Primários (Estilo Neon/Tech) */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-family: 'Montserrat', sans-serif;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.23);
            background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        }

        /* Inputs e Selectboxes */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
            background-color: #1e293b !important;
            color: white !important;
            border: 1px solid #475569 !important;
            border-radius: 6px;
        }
        
        /* Métricas (Big Numbers) */
        [data-testid="stMetricValue"] {
            font-family: 'Montserrat', sans-serif;
            font-size: 3rem !important;
            font-weight: 700;
        }

        /* Ajuste de Alertas (Success, Error, Warning) */
        .stAlert {
            background-color: rgba(30, 41, 59, 0.9);
            border: none;
            border-radius: 8px;
        }
        
        /* Remove padding extra do topo */
        .block-container {
            padding-top: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ==================================================
# 🔐 SEGURANÇA
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False):
        return True

    # Tela de Login Estilizada
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: white;'>🔐 Strati | Secure Access</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94a3b8;'>Área restrita para equipe de CS</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                token_mfa = st.text_input("Código Authenticator") 
                st.write("")
                submit = st.form_submit_button("ACESSAR SISTEMA", use_container_width=True)
                
                if submit:
                    if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                        secret_key = st.secrets["mfa"]["secret_key"]
                        totp = pyotp.TOTP(secret_key)
                        if totp.verify(token_mfa.replace(" ", "")):
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.toast("Login realizado com sucesso!", icon="🔓")
                            time.sleep(0.5)
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

        if final < 60: 
            status, cor, icone = "CRÍTICO", "red", "🚨"
        elif final < 75: 
            status, cor, icone = "ATENÇÃO", "orange", "⚠️"
        else: 
            status, cor, icone = "SAUDÁVEL", "green", "✅"
        
        playbook = self.gerar_playbook(status, score_tecnico, score_interacao, msg_nps, dados['local'])
            
        return {
            "Score": round(final, 1), "Status": status, "Cor": cor, "Icone": icone,
            "Tec": int(score_tecnico), "Int": int(score_interacao), 
            "NPS": msg_nps, "Acoes": playbook
        }

# ==================================================
# 🖥️ INTERFACE PRINCIPAL
# ==================================================
with st.sidebar:
    logo_carregado = False
    possible_names = ["strati_logo.png", "Logo Strati.png", "logo.png"]
    for nome_arquivo in possible_names:
        if os.path.exists(nome_arquivo):
            st.image(nome_arquivo, use_column_width=True)
            logo_carregado = True
            break
    if not logo_carregado: st.markdown("<h1>STRATI</h1>", unsafe_allow_html=True)
        
    st.write("---")
    
    # Botão de Sair com estilo sutil
    if st.button("🚪 Encerrar Sessão"):
        st.session_state.clear(); st.rerun()
    
    st.markdown("### 1. Perfil")
    nome = st.text_input("Nome da Empresa", placeholder="Ex: Strati Tecnologia")
    local = st.radio("Localização", ["SP (Local)", "Fora de SP (Remoto)"], horizontal=True)
    
    c1, c2 = st.columns(2)
    tier = c1.selectbox("Tier", ["Ouro", "Prata", "Bronze"])
    fase = c2.selectbox("Fase", ['Onboarding', 'Adoção', 'Retenção'])
    
    st.write("---")
    st.markdown("### 2. Chamados")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0)
    c1, c2 = st.columns(2)
    c_in = c1.number_input("Abertos", value=5)
    c_out = c2.number_input("Fechados", value=5)

# Título Estilizado
st.markdown("<h1>🛡️ Calculadora CS <span style='color:#2563eb'>Intelligence</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#94a3b8'>Análise de Saúde: <b>{nome if nome else 'Novo Cliente'}</b></p>", unsafe_allow_html=True)

# Layout em Cartões
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 🤝 Relacionamento")
        st.write("")
        if local == "SP (Local)":
            visitas = st.slider("Visitas Presenciais", 0, 5, 1)
            online = st.slider("Calls Online (Bônus)", 0, 10, 2)
        else:
            st.info("✈️ Cliente Remoto: Foco em Calls Online")
            online = st.slider("Calls Online (Meta: 2)", 0, 10, 2)
            visitas = st.slider("Visitas Presenciais (Opcional)", 0, 5, 0)
            
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        st.write("")
        st.markdown("**QBR (Resultados)**")
        qbr_realizado = st.radio("QBR Apresentado?", ["Sim", "Não"], horizontal=True)
        qbr_freq = st.selectbox("Frequência", ["Trimestral", "Semestral", "Anual"]) if qbr_realizado == "Sim" else "N/A"

with col2:
    with st.container(border=True):
        st.markdown("### ❤️ Satisfação (NPS)")
        st.write("")
        tem_nps = st.toggle("Cliente respondeu NPS recente?", value=True) # Mudei para Toggle (mais moderno)
        if tem_nps:
            nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
        else:
            nps_valor = None
            st.warning("⚖️ Peso redistribuído automaticamente.")

st.write("")
st.write("")

# Botão de Ação Grande
if st.button("PROCESSAR ANÁLISE DE SAÚDE", type="primary", use_container_width=True):
    if not nome:
        st.toast("Por favor, preencha o nome do cliente.", icon="⚠️")
    else:
        # Corrige o mapeamento da fase (Sidebar estava abreviada)
        fase_map = {'Onboarding': 'Onboarding (0-6m)', 'Adoção': 'Adoção (6-24m)', 'Retenção': 'Retenção (+2 anos)'}
        
        modelo = CustomerHealthModel()
        inputs = {
            'tier': tier, 'fase': fase_map[fase], 'local': local,
            'nps': nps_valor, 'criados': c_in, 'encerrados': c_out, 
            'sla': sla, 'visitas': visitas, 'book': book, 
            'qbr_realizado': qbr_realizado, 'online': online
        }
        res = modelo.calcular(inputs)
        
        st.markdown("---")
        
        # Resultados Visuais
        c_score, c_acao = st.columns([1, 1.5])
        
        with c_score:
            with st.container(border=True):
                st.markdown("<p style='text-align:center; margin-bottom:0'>HEALTH SCORE</p>", unsafe_allow_html=True)
                
                # Cores dinâmicas para o número
                cor_num = "#22c55e" if res['Cor'] == 'green' else ("#f97316" if res['Cor'] == 'orange' else "#ef4444")
                st.markdown(f"<h1 style='text-align:center; color:{cor_num}; font-size: 4rem !important'>{res['Score']}</h1>", unsafe_allow_html=True)
                
                st.markdown(f"<h3 style='text-align:center'>{res['Icone']} {res['Status']}</h3>", unsafe_allow_html=True)
        
        with c_acao:
            with st.container(border=True):
                st.markdown("### 📝 Diagnóstico & Ações")
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
            "Técnico": res['Tec'], "Interação": res['Int'],
            "NPS": nps_banco, "Responsável": st.session_state.get('user_logado', 'Admin')
        }
        
        with st.spinner("Sincronizando banco de dados..."):
            salvar_no_banco(dados_db)
            st.toast("Análise registrada com sucesso!", icon="💾")
