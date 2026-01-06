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
# 🔐 SEGURANÇA
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
            token_mfa = st.text_input("Código Authenticator") 
            submit = st.form_submit_button("Entrar")
            
            if submit:
                if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                    secret_key = st.secrets["mfa"]["secret_key"]
                    totp = pyotp.TOTP(secret_key)
                    if totp.verify(token_mfa.replace(" ", "")):
                        st.session_state["authenticated"] = True
                        st.session_state["user_logado"] = username
                        st.success("Login realizado!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Código MFA Inválido.")
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
        df_atual = conn.read(worksheet="Página1", ttl=0)
        nova_linha = pd.DataFrame([dados])
        df_atualizado = pd.concat([df_atual, nova_linha], ignore_index=True)
        conn.update(worksheet="Página1", data=df_atualizado)
        return True
    except Exception as e:
        if "200" in str(e) or "Response" in str(e): return True
        else: st.error(f"Erro ao salvar: {str(e)}"); return False

# ==================================================
# 🧠 LÓGICA CS + PLAYBOOKS
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_fase = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'peso_tecnico': 0.20, 'peso_nps': 0.20, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'peso_tecnico': 0.50, 'peso_nps': 0.30, 'meta_visitas': 0.5}
        }
        self.sla_targets = {'Ouro': 99.0, 'Prata': 98.0, 'Bronze': 95.0}

    def gerar_playbook(self, status, score_tec, score_int, score_nps):
        acoes = []
        if status in ["CRÍTICO", "ATENÇÃO"]:
            acoes.append("⚠️ **Ação Imediata:** Registrar risco no CRM.")
            if score_tec < 70:
                acoes.append("🔧 **Técnico:** Agendar War Room com suporte.")
                acoes.append("🔧 **Técnico:** Enviar plano de correção de SLA.")
            if score_int < 60:
                acoes.append("🤝 **Relacionamento:** Agendar visita executiva urgente.")
            if score_nps != "N/A" and score_nps < 70:
                acoes.append("❤️ **NPS:** Ligar para entender a nota baixa.")
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
        meta = regras['meta_visitas']
        visitas_score = 100 if meta == 0 else min((dados['visitas']/meta)*100, 100.0)
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        qbr_pts = 100 if dados['qbr']=='Sim' else 0
        score_interacao = (visitas_score*0.5) + ((book_pts + qbr_pts)/2*0.5) + min(dados['online']*2, 10)
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

        status, cor = "SAUDÁVEL", "green"
        if final < 60: status, cor = "CRÍTICO", "red"
        elif final < 75: status, cor = "ATENÇÃO", "orange"
        
        playbook = self.gerar_playbook(status, score_tecnico, score_interacao, msg_nps)
            
        return {
            "Score": round(final, 1), "Status": status, "Cor": cor, 
            "Tec": int(score_tecnico), "Int": int(score_interacao), 
            "NPS": msg_nps, "Acoes": playbook
        }

# ==================================================
# 🖥️ INTERFACE
# ==================================================
with st.sidebar:
    logo_carregado = False
    possible_names = ["strati_logo.png", "Logo Strati.png", "logo.png"]
    for nome_arquivo in possible_names:
        if os.path.exists(nome_arquivo):
            st.image(nome_arquivo, use_column_width=True)
            logo_carregado = True
            break
    if not logo_carregado: st.header("STRATI")
        
    st.write("---")
    st.caption(f"👤 {st.session_state.get('user_logado', 'Admin')}")
    if st.button("Sair / Logout", type="primary"):
        st.session_state.clear(); st.rerun()
    st.write("---")
    
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
        tem_nps = st.checkbox("Respondeu NPS?", value=True)
        if tem_nps:
            nps_valor = st.slider("Nota NPS (0-10)", 0, 10, 9)
        else:
            nps_valor = None
            st.warning("⚠️ Peso redistribuído.")

st.write("")
if st.button("CALCULAR SAÚDE & AÇÕES", type="primary", use_container_width=True):
    if not nome:
