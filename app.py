import streamlit as st
from datetime import datetime
import sqlite3
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Zínia - Planejador", page_icon="🌼", layout="centered")

st.title("🌼 Zínia - Sistema de Agendamento")
st.write("Gerencie os pedidos, orçamentos e prazos de entrega com salvamento automático.")

# 2. FUNÇÕES DO BANCO DE DADOS (SQLite)
def conectar_banco():
    conn = sqlite3.connect('zinia_dados.db')
    cursor = conn.cursor()
    # Cria a tabela se ela não existir (Garante que os dados fiquem salvos no PC/Nuvem)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            arranjo TEXT,
            orcamento_base REAL,
            frete REAL,
            orcamento_total REAL,
            data_hora TEXT
        )
    ''')
    conn.commit()
    return conn

def salvar_pedido(cliente, arranjo, ob, fr, total, data_hora):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pedidos (cliente, arranjo, orcamento_base, frete, orcamento_total, data_hora)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cliente, arranjo, ob, fr, total, data_hora))
    conn.commit()
    conn.close()

def listar_pedidos():
    conn = conectar_banco()
    # Lê os dados do SQLite e joga direto em um DataFrame do Pandas
    df = pd.read_sql_query("SELECT * FROM pedidos", conn)
    conn.close()
    return df

def deletar_pedido(id_pedido):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id = ?", (id_pedido,))
    conn.commit()
    conn.close()

# 3. FORMULÁRIO PARA ADICIONAR CLIENTE
st.header("📋 Novo Pedido")

with st.form(key="form_pedido", clear_on_submit=True):
    nome = st.text_input("Nome do Cliente", placeholder="Ex: Clodoaldo")
    arranjo = st.text_input("Nome do Arranjo", placeholder="Ex: Vaso de Zínias Amarelas")
    
    # Caixas lado a lado: Orçamento do arranjo e Frete
    col1, col2 = st.columns(2)
    with col1:
        orcamento_base = st.number_input("Orçamento do Arranjo (R$)", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        valor_frete = st.number_input("Valor do Frete (R$)", min_value=0.0, step=1.0, format="%.2f")
    
    # Soma automática em tempo real para mostrar na tela
    orcamento_total = orcamento_base + valor_frete
    st.write(f"**Cálculo do Orçamento Total:** R$ {orcamento_total:.2f}")
    
    # Campos de Data e Hora de entrega
    col3, col4 = st.columns(2)
    with col3:
        data_entrega = st.date_input("Data de Entrega", value=datetime.today())
    with col4:
        hora_entrega = st.time_input("Hora de Entrega")

    botao_salvar = st.form_submit_button(label="Adicionar Cliente")

# 4. LÓGICA DE SALVAMENTO
if botao_salvar:
    if nome and arranjo:
        # Junta data e hora
        data_hora_entrega = datetime.combine(data_entrega, hora_entrega)
        data_hora_formatada = data_hora_entrega.strftime("%d/%m/%Y às %H:%M")
        
        # Salva permanentemente no arquivo .db
        salvar_pedido(nome, arranjo, orcamento_base, valor_frete, orcamento_total, data_hora_formatada)
        st.success(f"Pedido de {nome} salvo permanentemente!")
        st.rerun() # Atualiza a tela para mostrar o novo pedido
    else:
        st.error("Por favor, preencha o nome do cliente e do arranjo.")

# 5. EXIBIÇÃO E EXCLUSÃO DOS PEDIDOS
st.header("📑 Pedidos Agendados")
df_pedidos = listar_pedidos()

if not df_pedidos.empty:
    # Mostra a lista de pedidos com um botão de excluir ao lado de cada um
    for index, row in df_pedidos.iterrows():
        # Cria uma linha visual organizada para cada pedido
        with st.container():
            col_info, col_btn = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"### 👤 {row['cliente']} — *{row['arranjo']}*")
                st.write(f"📅 **Entrega:** {row['data_hora']}")
                st.write(f"💰 **Base:** R$ {row['orcamento_base']:.2f} | 🚚 **Frete:** R$ {row['frete']:.2f} | 💵 **Total:** R$ {row['orcamento_total']:.2f}")
                st.write("---")
                
            with col_btn:
                # Botão de excluir usando o ID único do banco de dados
                # O uso de 'key' serve para o Streamlit diferenciar os botões de cada linha
                if st.button("❌ Excluir", key=f"del_{row['id']}"):
                    deletar_pedido(row['id'])
                    st.success("Pedido excluído!")
                    st.rerun()
else:
    st.write("Nenhum pedido agendado por enquanto.")
