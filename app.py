import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pyotp
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Strati | CS Segura", layout="wide")

# ==================================================
# 🔐 SEGURANÇA (SENHA + MFA TOTP)
# ==================================================
def check_authentication():
    """Verifica Senha E Token MFA (Google Authenticator)"""
    
    if st.session_state.get("authenticated", False):
        return True

    st.markdown("<div style='text-align:center'><h2>🔐 Acesso Seguro Strati</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        token_mfa = st.text_input("Código MFA (Authenticator)", max_chars=6)
        
        if st.button("Entrar"):
            # 1. Verifica Usuário e Senha
            if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                
                # 2. Verifica MFA (Time-based One-Time Password)
                # O segredo MFA deve estar nos secrets. Ex: "JBSWY3DPEHPK3PXP"
                totp = pyotp.TOTP(st.secrets["mfa"]["secret_key"])
                
                if totp.verify(token_mfa):
                    st.session_state["authenticated"] = True
                    st.session_state["user_logado"] = username
                    st.success("Login realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Código MFA Inválido ou Expirado.")
            else:
                st.error("❌ Usuário ou Senha incorretos.")

    return False

# SE NÃO ESTIVER LOGADO, PARA O CÓDIGO
if not check_authentication():
    st.stop()

# ==================================================
# 💾 BANCO DE DADOS (GOOGLE SHEETS)
# ==================================================
def salvar_no_banco(dados):
    try:
        # Cria conexão
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Lê dados atuais (para não sobrescrever, e sim adicionar)
        # ttl=0 garante que não pegue cache velho
        df_atual = conn.read(worksheet="Página1", ttl=0) 
        
        # Cria nova linha
        nova_linha = pd.DataFrame([dados])
        
        # Concatena (Junta o velho com o novo)
        df_atualizado = pd.concat([df_atual, nova_linha], ignore_index=True)
        
        # Envia de volta pro Google Sheets
        conn.update(worksheet="Página1", data=df_atualizado)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
        return False

# ==================================================
# 🧠 LÓGICA DA CALCULADORA
# ==================================================
class CustomerHealthModel:
    def __init__(self):
        self.regras_cohort = {
            'Onboarding (0-6m)': {'peso_interacao': 0.60, 'peso_tecnico': 0.20, 'peso_nps': 0.20, 'meta_visitas': 2},
            'Adoção (6-24m)':    {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas': 1},
            'Retenção (+2 anos)':{'peso_interacao': 0.20, 'peso_tecnico': 0.50, 'peso_nps': 0.30, 'meta_visitas': 0.5}
        }
        self.sla_target = 98.0

    def calcular(self, dados):
        # Lógica simplificada para brevidade (mantendo a sua original)
        regras = self.regras_cohort[dados['cohort']]
        
        # Score Técnico
        ratio = 1.0 if dados['criados'] == 0 else dados['encerrados'] / dados['criados']
        score_backlog = min(ratio, 1.0) * 100
        score_sla = 100 if dados['sla'] >= self.sla_target else ((dados['sla'] / self.sla_target) ** 5) * 100
        score_tecnico = (score_sla * 0.70) + (score_backlog * 0.30)
        
        # Score Interação
        meta = regras['meta_visitas']
        visitas_score = min((dados['visitas']/meta)*100, 100.0) if meta > 0 else (100 if dados['visitas']>0 else 100)
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        qbr_pts = 100 if dados['qbr']=='Sim' else 0
        score_interacao = (visitas_score*0.5) + ((book_pts + qbr_pts)/2*0.5) + min(dados['online']*2, 10)
        score_interacao = min(score_interacao, 100.0)
        
        # Score NPS
        score_nps = dados['nps'] * 10
        
        # Final
        final = (score_interacao * regras['peso_interacao']) + \
                (score_tecnico * regras['peso_tecnico']) + \
                (score_nps * regras['peso_nps'])
        
        status = "SAUDÁVEL"
        cor = "green"
        if final < 60: status, cor = "CRÍTICO", "red"
        elif final < 75: status, cor = "ATENÇÃO", "orange"
            
        return {
            "Score": round(final, 1), "Status": status, "Cor": cor,
            "Tec": int(score_tecnico), "Int": int(score_interacao), "NPS": int(score_nps)
        }

# ==================================================
# 🖥️ INTERFACE (SIDEBAR + MAIN)
# ==================================================
with st.sidebar:
    st.header("STRATI")
    st.caption(f"Logado como: {st.session_state['user_logado']}")
    if st.button("Sair"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()
    
    nome = st.text_input("Nome Cliente")
    cohort = st.selectbox("Fase", ['Onboarding (0-6m)', 'Adoção (6-24m)', 'Retenção (+2 anos)'])
    
    st.divider()
    sla = st.slider("SLA %", 80.0, 100.0, 98.0)
    c_in = st.number_input("Chamados Criados", value=5)
    c_out = st.number_input("Chamados Encerrados", value=5)

st.title("🛡️ Calculadora CS + Database")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("Relacionamento")
        visitas = st.slider("Visitas", 0, 5, 1)
        online = st.slider("Calls Online", 0, 10, 2)
        book = st.selectbox("Book", ["Apresentado", "Enviado", "Não realizado"])
        qbr = st.radio("QBR?", ["Sim", "Não"], horizontal=True)

with col2:
    with st.container(border=True):
        st.subheader("NPS")
        nps = st.slider("Nota", 0, 10, 9)

if st.button("CALCULAR E SALVAR", type="primary", use_container_width=True):
    if not nome:
        st.warning("Preencha o nome do cliente para salvar.")
    else:
        modelo = CustomerHealthModel()
        inputs = {
            'cohort': cohort, 'nps': nps, 'criados': c_in, 'encerrados': c_out,
            'sla': sla, 'visitas': visitas, 'book': book, 'qbr': qbr, 'online': online
        }
        res = modelo.calcular(inputs)
        
        # Exibir Resultado
        st.divider()
        c1, c2 = st.columns([1,2])
        c1.metric("Health Score", res['Score'], delta=res['Status'], delta_color="inverse")
        if res['Cor'] == 'red': st.error(f"Status: {res['Status']}")
        elif res['Cor'] == 'orange': st.warning(f"Status: {res['Status']}")
        else: st.success(f"Status: {res['Status']}")
        
        # Preparar dados para o Google Sheets
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cliente": nome,
            "Cohort": cohort,
            "Score": res['Score'],
            "Status": res['Status'],
            "Técnico": res['Tec'],
            "Interação": res['Int'],
            "NPS": res['NPS'],
            "Responsável": st.session_state['user_logado']
        }
        
        with st.spinner("Salvando no banco de dados..."):
            if salvar_no_banco(dados_db):
                st.toast("✅ Cálculo salvo com sucesso no Google Sheets!", icon="💾")
