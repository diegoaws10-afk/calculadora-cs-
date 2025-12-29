import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Strati | CS Segura", layout="wide", page_icon="🛡️")

# ==================================================
# 🔐 SEGURANÇA (MFA)
# ==================================================
def check_authentication():
    if st.session_state.get("authenticated", False):
        return True

    st.markdown("<br><div style='text-align:center'><h2>🔐 Acesso Seguro Strati</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            token_mfa = st.text_input("Código Authenticator (6 dígitos)", max_chars=6)
            submit = st.form_submit_button("Entrar")
            
            if submit:
                # Verifica se usuário existe e senha confere
                if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                    try:
                        # Valida o token MFA
                        totp = pyotp.TOTP(st.secrets["mfa"]["secret_key"])
                        if totp.verify(token_mfa):
                            st.session_state["authenticated"] = True
                            st.session_state["user_logado"] = username
                            st.success("Login realizado!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Código MFA Inválido.")
                    except:
                        st.error("❌ Erro na configuração do MFA. Verifique os Secrets.")
                else:
                    st.error("❌ Usuário ou Senha incorretos.")
    return False

if not check_authentication():
    st.stop()

# ==================================================
# 💾 BANCO DE DADOS
# ==================================================
def salvar_no_banco(dados):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Lê a aba 'Página1' (Se sua planilha usa 'Sheet1', altere aqui)
        df_atual = conn.read(worksheet="Página1", ttl=0)
        
        # Cria a nova linha
        nova_linha = pd.DataFrame([dados])
        
        # Concatena e salva
        df_atualizado = pd.concat([df_atual, nova_linha], ignore_index=True)
        conn.update(worksheet="Página1", data=df_atualizado)
        return True
        
    except Exception as e:
        # Ignora falso erro de sucesso (200)
        if "200" in str(e) or "Response" in str(e):
            return True
        else:
            st.error(f"Erro ao salvar: {str(e)}")
            return False

# ==================================================
# 🧠 LÓGICA CS (HÍBRIDA: FASE + TIER)
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        # Pesos definidos pela FASE (Momento do cliente)
        self.regras_fase = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'peso_tecnico': 0.20, 'peso_nps': 0.20, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'peso_tecnico': 0.50, 'peso_nps': 0.30, 'meta_visitas': 0.5}
        }
        
        # SLA Alvo definido pelo TIER (Valor do cliente)
        # Clientes Ouro exigem SLA mais rigoroso para dar nota máxima
        self.sla_targets = {
            'Ouro': 99.0,
            'Prata': 98.0,
            'Bronze': 95.0
        }

    def calcular(self, dados):
        # 1. Busca regras baseadas na FASE
        regras = self.regras_fase[dados['fase']]
        
        # 2. Busca alvo de SLA baseado no TIER
        sla_alvo = self.sla_targets.get(dados['tier'], 98.0)
        
        # --- Cálculo Técnico ---
        ratio = 1.0 if dados['criados'] == 0 else dados['encerrados'] / dados['criados']
        score_backlog = min(ratio, 1.0) * 100
        
        if dados['sla'] >= sla_alvo:
            score_sla = 100
        else:
            # Penalidade exponencial se ficar abaixo da meta do Tier
            score_sla = ((dados['sla'] / sla_alvo) ** 5) * 100
        
        score_tecnico = (score_sla * 0.70) + (score_backlog * 0.30)
        
        # --- Cálculo Interação ---
        meta = regras['meta_visitas']
        if meta > 0:
            visitas_score = min((dados['visitas']/meta)*100, 100.0)
        else:
            visitas_score = 100
            
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        qbr_pts = 100 if dados['qbr']=='Sim' else 0
        score_interacao = (visitas_score*0.5) + ((book_pts + qbr_pts)/2*0.5) + min(dados['online']*2, 10)
        
        # --- Final ---
        score_nps = dados['nps'] * 10
        final = (score_interacao * regras['peso_interacao']) + \
                (score_tecnico * regras['peso_tecnico']) + \
                (score_nps * regras['peso_nps'])
        
        status, cor = "SAUDÁVEL", "green"
        if final < 60: status, cor = "CRÍTICO", "red"
        elif final < 75: status, cor = "ATENÇÃO", "orange"
            
        return {
            "Score": round(final, 1), 
            "Status": status, 
            "Cor": cor, 
            "Tec": int(score_tecnico), 
            "Int": int(score_interacao), 
            "NPS": int(score_nps),
            "Meta_SLA": sla_alvo
        }

# ==================================================
# 🖥️ INTERFACE
# ==================================================
with st.sidebar:
    # Tenta carregar o logo
    logo_carregado = False
    possible_names = ["strati_logo.png", "Logo Strati.png", "logo.png"]
    for nome_arquivo in possible_names:
        if os.path.exists(nome_arquivo):
            st.image(nome_arquivo, use_column_width=True)
            logo_carregado = True
            break
    if not logo_carregado:
        st.header("STRATI")
        
    st.caption(f"👤 {st.session_state['user_logado']}")
    if st.button("Sair"):
        st.session_state["authenticated"] = False
        st.rerun()
        
    st.divider()
    
    # --- NOVOS INPUTS DE CLASSIFICAÇÃO ---
    st.markdown("### 1. Perfil do Cliente")
    nome = st.text_input("Nome da Empresa")
    
    col_tier, col_fase = st.columns(2)
    with col_tier:
        tier = st.selectbox("Tier", ["Ouro", "Prata", "Bronze"])
    with col_fase:
        fase = st.selectbox("Fase", ['Onboarding (0-6m)', 'Adoção (6-24m)', 'Retenção (+2 anos)'])
    
    st.divider()
    
    st.markdown("### 2. Métricas")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0)
    c_in = st.number_input("Chamados Abertos", value=5)
    c_out = st.number_input("Chamados Fechados", value=5)

st.title("🛡️ Calculadora CS Strati")
st.markdown(f"Análise: **{nome if nome else 'Novo Cliente'}** | Perfil: **{tier}** - **{fase}**")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("🤝 Relacionamento")
        visitas = st.slider("Visitas Presenciais", 0, 5, 1)
        online = st.slider("Calls Online", 0, 10, 2)
        book = st.selectbox("Book de Serviços", ["Apresentado", "Enviado", "Não realizado"])
        qbr = st.radio("QBR Trimestral?", ["Sim", "Não"], horizontal=True)

with col2:
    with st.container(border=True):
        st.subheader("❤️ Satisfação")
        nps = st.slider("NPS (0-10)", 0, 10, 9)

st.write("")
if st.button("CALCULAR E SALVAR", type="primary", use_container_width=True):
    if not nome:
        st.warning("Preencha o nome do cliente para salvar.")
    else:
        modelo = CustomerHealthModel()
        inputs = {
            'tier': tier, 'fase': fase, 'nps': nps, 
            'criados': c_in, 'encerrados': c_out, 'sla': sla, 
            'visitas': visitas, 'book': book, 'qbr': qbr, 'online': online
        }
        res = modelo.calcular(inputs)
        
        st.divider()
        
        # Resultado Visual
        c1, c2 = st.columns([1,2])
        c1.metric("Health Score Final", res['Score'], delta=res['Status'], delta_color="inverse")
        
        msg_result = f"**Status:** {res['Status']}"
        if res['Cor'] == 'red': st.error(msg_result)
        elif res['Cor'] == 'orange': st.warning(msg_result)
        else: st.success(msg_result)
        
        # Dados para o Google Sheets (Incluindo Tier e Fase)
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cliente": nome,
            "Tier": tier,  # Nova Coluna
            "Fase": fase,
            "Score": res['Score'],
            "Status": res['Status'],
            "Técnico": res['Tec'],
            "Interação": res['Int'],
            "NPS": res['NPS'],
            "Responsável": st.session_state['user_logado']
        }
        
        with st.spinner("Salvando..."):
            if salvar_no_banco(dados_db):
                st.toast("Salvo no Google Sheets!", icon="✅")
