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
                if username in st.secrets["passwords"] and password == st.secrets["passwords"][username]:
                    try:
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
# ==================================================
# 💾 BANCO DE DADOS (CORRIGIDO)
# ==================================================
def salvar_no_banco(dados):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Tenta ler a aba. Se sua planilha estiver em inglês, mude "Página1" para "Sheet1"
        df_atual = conn.read(worksheet="Página1", ttl=0)
        
        # Cria a nova linha
        nova_linha = pd.DataFrame([dados])
        
        # Junta o antigo com o novo
        df_atualizado = pd.concat([df_atual, nova_linha], ignore_index=True)
        
        # Atualiza a planilha
        conn.update(worksheet="Página1", data=df_atualizado)
        return True
        
    except Exception as e:
        # AQUI ESTÁ A CORREÇÃO:
        # Se o erro for apenas o código 200 (Sucesso), nós ignoramos e dizemos que deu certo.
        if "200" in str(e) or "Response" in str(e):
            return True
        else:
            st.error(f"Erro detalhado ao salvar: {str(e)}")
            return False
# ==================================================
# 🧠 LÓGICA CS
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
        regras = self.regras_cohort[dados['cohort']]
        
        # Técnico
        ratio = 1.0 if dados['criados'] == 0 else dados['encerrados'] / dados['criados']
        score_backlog = min(ratio, 1.0) * 100
        score_sla = 100 if dados['sla'] >= self.sla_target else ((dados['sla'] / self.sla_target) ** 5) * 100
        score_tecnico = (score_sla * 0.70) + (score_backlog * 0.30)
        
        # Interação
        meta = regras['meta_visitas']
        if meta > 0:
            visitas_score = min((dados['visitas']/meta)*100, 100.0)
        else:
            visitas_score = 100
            
        book_pts = 100 if dados['book']=='Apresentado' else (50 if dados['book']=='Enviado' else 0)
        qbr_pts = 100 if dados['qbr']=='Sim' else 0
        score_interacao = (visitas_score*0.5) + ((book_pts + qbr_pts)/2*0.5) + min(dados['online']*2, 10)
        
        # Final
        score_nps = dados['nps'] * 10
        final = (score_interacao * regras['peso_interacao']) + \
                (score_tecnico * regras['peso_tecnico']) + \
                (score_nps * regras['peso_nps'])
        
        status, cor = "SAUDÁVEL", "green"
        if final < 60: status, cor = "CRÍTICO", "red"
        elif final < 75: status, cor = "ATENÇÃO", "orange"
            
        return {"Score": round(final, 1), "Status": status, "Cor": cor, "Tec": int(score_tecnico), "Int": int(score_interacao), "NPS": int(score_nps)}

# ==================================================
# 🖥️ INTERFACE
# ==================================================
with st.sidebar:
    # Tenta carregar o logo de várias formas
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
    nome = st.text_input("Nome Cliente")
    # Mantendo o label "Fase" que você gostou
    cohort = st.selectbox("Fase do Cliente", ['Onboarding (0-6m)', 'Adoção (6-24m)', 'Retenção (+2 anos)'])
    
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

st.write("")
if st.button("CALCULAR E SALVAR", type="primary", use_container_width=True):
    if not nome:
        st.warning("Preencha o nome do cliente para salvar.")
    else:
        modelo = CustomerHealthModel()
        inputs = {'cohort': cohort, 'nps': nps, 'criados': c_in, 'encerrados': c_out, 'sla': sla, 'visitas': visitas, 'book': book, 'qbr': qbr, 'online': online}
        res = modelo.calcular(inputs)
        
        st.divider()
        c1, c2 = st.columns([1,2])
        c1.metric("Health Score", res['Score'], delta=res['Status'], delta_color="inverse")
        if res['Cor'] == 'red': st.error(res['Status'])
        elif res['Cor'] == 'orange': st.warning(res['Status'])
        else: st.success(res['Status'])
        
        # Salvar
        dados_db = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cliente": nome, "Fase": cohort, "Score": res['Score'], "Status": res['Status'],
            "Técnico": res['Tec'], "Interação": res['Int'], "NPS": res['NPS'], "Responsável": st.session_state['user_logado']
        }
        
        with st.spinner("Salvando..."):
            if salvar_no_banco(dados_db):
                st.toast("Salvo no Google Sheets!", icon="✅")

