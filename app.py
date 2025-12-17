import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora CS AI", page_icon="🚀")

# --- LÓGICA DO MODELO ---
class CustomerHealthModel:
    def __init__(self):
        self.regras_tier = {
            'Ouro': {'peso_interacao': 0.40, 'peso_tecnico': 0.40, 'peso_nps': 0.20, 'meta_visitas_mes': 1},
            'Prata': {'peso_interacao': 0.30, 'peso_tecnico': 0.40, 'peso_nps': 0.30, 'meta_visitas_mes': 0.5},
            'Bronze': {'peso_interacao': 0.10, 'peso_tecnico': 0.60, 'peso_nps': 0.30, 'meta_visitas_mes': 0}
        }
        self.sla_target = 98.0

    def calcular_score_tecnico(self, chamados_criados, chamados_encerrados, sla_realizado):
        ratio = 1.0 if chamados_criados == 0 else chamados_encerrados / chamados_criados
        score_backlog = min(ratio, 1.0) * 100
        
        if sla_realizado >= self.sla_target:
            score_sla = 100
        else:
            score_sla = ((sla_realizado / self.sla_target) ** 5) * 100
        
        return (score_sla * 0.70) + (score_backlog * 0.30)

    def calcular_score_interacao(self, tier, visitas, status_book, qbr_entregue, reunioes_online):
        regras = self.regras_tier[tier]
        meta_visitas = regras['meta_visitas_mes']
        
        if meta_visitas > 0:
            atingimento_visitas = visitas / meta_visitas
        else:
            atingimento_visitas = 1.0 if visitas == 0 else 1.2
        
        score_visitas = min(atingimento_visitas * 100, 100.0)

        if status_book == 'Apresentado': pts_book = 100
        elif status_book == 'Enviado': pts_book = 50
        else: pts_book = 0
            
        pts_qbr = 100 if qbr_entregue == 'Sim' else 0 
        
        score_estrategico = (pts_book + pts_qbr) / 2
        bonus_online = min(reunioes_online * 2, 10)

        final_interacao = (score_visitas * 0.50) + (score_estrategico * 0.50) + bonus_online
        return min(final_interacao, 100.0)

    def analisar_cliente(self, dados):
        tier = dados['tier']
        regras = self.regras_tier[tier]
        score_nps = dados['nps'] * 10
        
        score_interacao = self.calcular_score_interacao(
            tier, dados['visitas_presenciais'], dados['status_book'],
            dados['qbr_entregue'], dados['reunioes_online']
        )
        score_tecnico = self.calcular_score_tecnico(
            dados['chamados_criados'], dados['chamados_encerrados'], dados['sla_realizado']
        )
        final_score = (score_interacao * regras['peso_interacao']) + \
                      (score_tecnico * regras['peso_tecnico']) + \
                      (score_nps * regras['peso_nps'])
        
        # Cores para Web
        cor_borda = "#28a745"
        bg_cor = "#d4edda"
        texto_status = "SAUDÁVEL"
        acao = "✅ Manter rotina de sucesso."

        if final_score < 60:
            cor_borda = "#dc3545"
            bg_cor = "#f8d7da"
            texto_status = "CRÍTICO"
            motivos = []
            if dados['sla_realizado'] < 98: motivos.append("Quebra de SLA")
            if dados['status_book'] != 'Apresentado': motivos.append("Book não apresentado")
            if dados['qbr_entregue'] == 'Não' and tier == 'Ouro': motivos.append("QBR Pendente")
            acao = f"🚨 **ACIONAR PLANO DE RECUPERAÇÃO**\n\nFoco: {', '.join(motivos)}."
        elif final_score < 75:
            cor_borda = "#ffc107"
            bg_cor = "#fff3cd"
            texto_status = "ATENÇÃO"
            acao = "⚠️ Agendar call de alinhamento."

        return {
            "Score": round(final_score, 1),
            "Status": texto_status, "Acao": acao,
            "Tec": int(score_tecnico), "Int": int(score_interacao), "NPS": int(score_nps),
            "Color": cor_borda
        }

# --- INTERFACE VISUAL (SIDEBAR E MAIN) ---
st.title("🚀 Calculadora Customer Success AI")
st.markdown("Preencha os dados abaixo para obter o diagnóstico preditivo.")

with st.sidebar:
    st.header("📋 Dados Cadastrais")
    nome = st.text_input("Nome do Cliente", placeholder="Ex: Empresa X")
    tier = st.selectbox("Tier / Classificação", ["Ouro", "Prata", "Bronze"])
    
    st.divider()
    st.header("⚙️ Métricas Técnicas")
    sla = st.slider("SLA Realizado (%)", 80.0, 100.0, 98.0, step=0.1)
    col1, col2 = st.columns(2)
    chamados_in = col1.number_input("Chamados Abertos", min_value=0, value=10)
    chamados_out = col2.number_input("Chamados Fechados", min_value=0, value=10)

col_form1, col_form2 = st.columns(2)

with col_form1:
    st.subheader("🤝 Relacionamento")
    visitas = st.slider("Visitas Presenciais", 0, 5, 1)
    online = st.slider("Reuniões Online", 0, 10, 2)
    book = st.selectbox("Status do Book", ["Apresentado", "Enviado", "Não realizado"])
    qbr = st.radio("QBR Entregue?", ["Sim", "Não"], horizontal=True)

with col_form2:
    st.subheader("❤️ Sentimento")
    nps = st.slider("NPS (0 a 10)", 0, 10, 9)
    st.markdown("<br><br>", unsafe_allow_html=True) # Espaço
    calcular = st.button("CALCULAR HEALTH SCORE", use_container_width=True, type="primary")

# --- RESULTADO ---
if calcular:
    modelo = CustomerHealthModel()
    dados = {
        'tier': tier, 'nps': nps, 'chamados_criados': chamados_in, 'chamados_encerrados': chamados_out,
        'sla_realizado': sla, 'visitas_presenciais': visitas, 'status_book': book,
        'qbr_entregue': qbr, 'reunioes_online': online
    }
    res = modelo.analisar_cliente(dados)
    
    st.divider()
    
    # Cabeçalho do Card
    st.markdown(f"### Resultado: {nome.upper() if nome else 'CLIENTE'}")
    
    # Métricas Principais
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.metric("Tier", tier)
    with c2:
        st.metric("Health Score", f"{res['Score']} / 100", delta=res['Status'], delta_color="normal" if res['Score'] > 75 else "inverse")
    
    # Detalhes
    st.info(f"**Recomendação:** {res['Acao']}")
    
    d1, d2, d3 = st.columns(3)
    d1.metric("🔧 Técnico", f"{res['Tec']}%")
    d2.metric("🤝 Interação", f"{res['Int']}%")
    d3.metric("❤️ NPS", res['NPS'])
