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
# 🔐 SEGURANÇA (MFA SIMPLIFICADO)
# ==================================================
def check_authentication():
    # Se já estiver autenticado, libera o acesso
    if st.session_state.get("authenticated", False):
        return True

    st.markdown("<br><div style='text-align:center'><h2>🔐 Acesso Seguro Strati</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            token_mfa = st.text_input("Código Authenticator (6 dígitos)") 
            submit = st.form_submit_button("Entrar")
            
            if submit:
                # 1. Verifica Usuário e Senha nos Secrets
                if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                    
                    # 2. Verifica MFA (Código do Google Authenticator)
                    # .replace garante que espaços (123 456) não quebrem a verificação
                    secret_key = st.secrets["mfa"]["secret_key"]
                    totp = pyotp.TOTP(secret_key)
                    
                    if totp.verify(token_mfa.replace(" ", "")):
                        st.session_state["authenticated"] = True
                        st.session_state["user_logado"] = username
                        st.success("Login realizado com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Código MFA Inválido.")
                else:
                    st.error("❌ Usuário ou Senha incorretos.")
    return False

# Bloqueia o app se não estiver logado
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
        if "200" in str(e) or "Response" in str(e):
            return True
        else:
            st.error(f"Erro ao salvar: {str(e)}")
            return False

# ==================================================
# 🧠 LÓGICA CS (DINÂMICA)
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_fase = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'peso_tecnico': 0.20, 'peso_nps': 0.20, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'peso_tecnico': 0.50, 'peso_nps': 0.30, 'meta_visitas': 0.5}
        }
        self.sla_targets = {'Ouro': 99.0, 'Prata': 98.0, 'Bronze': 95.0}

    def calcular(self, dados):
        regras = self.regras_fase[dados['fase']]
        sla_alvo = self.sla_targets.get(dados['tier'], 98.0)
        
        # --- Técnico ---
        ratio = 1.0 if dados['criados'] == 0 else dados['encerrados'] / dados['criados']
        score_backlog = min(ratio, 1.0) * 100
        score_sla = 100 if dados['sla'] >= sla_alvo else ((dados['sla'] / sla_alvo) ** 5) * 100
        score_tecnico = (score_sla * 0.70) + (score_backlog * 0.30)
        
        # --- Interação ---
        meta = regras['meta_visitas']
        visitas_score = 100 if meta == 0 else min((dados['visitas']/meta)*100, 100.0)
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        qbr_pts = 100 if dados['qbr']=='Sim' else 0
        score_interacao = (visitas_score*0.5) + ((book_pts + qbr_pts)/2*0.5) + min(dados['online']*2, 10)
        score_interacao = min(score_interacao, 100.0)

        # --- Final (Com ou Sem NPS) ---
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

        status, cor = "SAUDÁVEL", "green"
        if final < 60: status, cor = "CRÍTICO", "red"
        elif final < 75: status, cor = "ATENÇÃO", "orange"
            
        return {
            "Score": round(final, 1), "Status": status, "Cor": cor, 
            "Tec": int(score_tecnico), "Int": int(score_interacao), 
            "NPS": msg_nps, "Meta_SLA": sla_alvo
        }

# ==================================================
# 🖥️ INTERFACE E SIDEBAR
# ==================================================
with st.sidebar:
    # --- LOGO ---
    logo_carregado = False
    possible_names = ["strati_logo.png", "Logo Strati.png", "logo.png"]
    for nome_arquivo in possible_names:
        if os.path.exists(nome_arquivo):
            st.image(nome_arquivo, use_column_width=True)
            logo_carregado = True
            break
    if not logo_carregado:
        st.header("STRATI")
        
    # --- LOGOUT ---
    st.write("---")
    st.caption(f"👤 {st.session_state.get('user_logado', 'Admin')}")
    
    # BOTÃO DE SAIR REFORÇADO
    if st.button("Sair / Logout", type="primary"):
        # Limpa TODAS as variáveis da memória
        st.session_state.clear()
        # Recarrega a página (vai cair na tela de login)
        st.rerun()
        
    st.write("---")
    
    # --- INPUTS LATERAIS ---
    st.markdown("### 1. Perfil do Cliente")
    nome = st.text_input("Nome da Empresa")
    
    col_tier, col_fase = st.columns(2)
    with col_tier: tier = st.selectbox("Tier", ["Ouro", "Prata", "Bronze"])
    with col_fase: fase = st.selectbox("Fase", ['Onboarding (0-6m)', 'Adoção (6-24m)', 'Retenção (+2 anos)'])
    
    st.write("---")
    st.markdown("### 2. Métricas")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0)
    c_in = st.number_input("Chamados Abertos", value=5)
    c_out = st.number_input("Chamados Fechados", value=5)

# --- ÁREA PRINCIPAL ---
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
        st.subheader("❤️ Satisfação (NPS)")
        tem_nps = st.checkbox("Cliente respondeu NPS recente?", value=True)
        if tem_nps:
            nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
            st.info("NPS será considerado no cálculo.")
        else:
            nps_valor = None
            st.warning("⚠️ Peso do NPS será redistribuído.")

st.write("")
if st.button("CALCULAR E SALVAR", type="primary", use_container_width=True):
    if not nome:
        st.warning("Preencha o nome do cliente para salvar.")
    else:
        modelo = CustomerHealthModel()
        inputs = {
            'tier': tier, 'fase': fase, 'nps': nps_valor, 
            'criados': c_in, 'encerrados': c_out, 'sla': sla, 
            'visitas': visitas, 'book': book, 'qbr': qbr, 'online': online
        }
        res = modelo.calcular(inputs)
        
        st.divider()
        c1, c2 = st.columns([1,2])
        c1.metric("Health Score Final", res['Score'], delta=res['Status'], delta_color="inverse")
        
        msg = f"**Status:** {res['Status']}"
        if res['Cor'] == 'red': st.error(msg)
        elif res['Cor'] == 'orange': st.warning(msg)
        else: st.success(msg)
        
        nps_banco = res['NPS'] if res['NPS'] != "N/A" else ""
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cliente": nome, "Tier": tier, "Fase": fase,
            "Score": res['Score'], "Status": res['Status'],
            "Técnico": res['Tec'], "Interação": res['Int'],
            "NPS": nps_banco, "Responsável": st.session_state.get('user_logado', 'Admin')
        }
        
        with st.spinner("Salvando..."):
            if salvar_no_banco(dados_db):
                st.toast("Salvo no Google Sheets!", icon="✅")
