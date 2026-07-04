import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import time

# Configuração da página do Streamlit
st.set_page_config(page_title="Zínia - Planejador", page_icon="🌼", layout="centered")

st.title("🌼 Zínia - Sistema de Agendamento")
st.write("Gerencie os pedidos, orçamentos e prazos de entrega.")

# Inicializa o "banco de dados" na memória do navegador se não existir
if "pedidos" not in st.session_state:
    st.session_state.pedidos = []

# --- FORMULÁRIO PARA ADICIONAR CLIENTE ---
st.header("📋 Novo Pedido")

with st.form(key="form_pedido", clear_on_submit=True):
    nome = st.text_input("Nome do Cliente", placeholder="Ex: Clodoaldo")
    arranjo = st.text_input("Nome do Arranjo", placeholder="Ex: Vaso de Zínias Amarelas")
    
    col1, col2 = st.columns(2)
    with col1:
        orcamento_base = st.number_input("Orçamento do Arranjo (R$)", min_value=0.0, format="%.2f")
    with col2:
        # Botão/Checkbox "Com Frete"
        com_frete = st.checkbox("Com Frete?")
    
    # Se o botão "Com Frete" for marcado, mostra o campo do valor do frete
    valor_frete = 0.0
    if com_frete:
        valor_frete = st.number_input("Valor do Frete (R$)", min_value=0.0, format="%.2f")
    
    # Campos de Data e Hora de entrega
    col3, col4 = st.columns(2)
    with col3:
        data_entrega = st.date_input("Data de Entrega", value=datetime.today())
    with col4:
        hora_entrega = st.time_input("Hora de Entrega")

    botao_salvar = st.form_submit_button(label="Adicionar Cliente")

# --- LÓGICA AO CLICAR NO BOTÃO ---
if botao_salvar:
    if nome and arranjo:
        # Calcula o orçamento total
        orcamento_total = orcamento_base + valor_frete
        
        # Junta data e hora em um único objeto datetime
        data_hora_entrega = datetime.combine(data_entrega, hora_entrega)
        
        # Cria o dicionário do novo pedido
        novo_pedido = {
            "Cliente": nome,
            "Arranjo": arranjo,
            "Orçamento Total (R$)": f"R$ {orcamento_total:.2f}",
            "Com Frete": "Sim" if com_frete else "Não",
            "Data/Hora Entrega": data_hora_entrega.strftime("%d/%m/%Y às %H:%M"),
            "Status": "Agendado"
        }
        
        # Salva na lista de pedidos
        st.session_state.pedidos.append(novo_pedido)
        st.success(f"Pedido de {nome} adicionado com sucesso!")
        
        # Alerta visual dos prazos na tela (Cálculo dos alarmes de dias/horas)
        tempo_restante = data_hora_entrega - datetime.now()
        if tempo_restante.total_seconds() > 0:
            st.info(f"⏰ Alarme configurado! Esse pedido deve ser entregue em {tempo_restante.days} dias e {tempo_restante.seconds // 3600} horas.")
    else:
        st.error("Por favor, preencha o nome do cliente e do arranjo.")

# --- EXIBIÇÃO DOS PEDIDOS ---
st.header("📑 Pedidos Agendados")
if st.session_state.pedidos:
    # Transforma a lista em uma tabela bonita do Streamlit (DataFrame)
    df = pd.DataFrame(st.session_state.pedidos)
    st.dataframe(df, use_container_width=True)
else:
    st.write("Nenhum pedido agendado por enquanto.")
