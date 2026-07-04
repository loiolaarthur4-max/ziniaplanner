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
    df = pd.read_sql_query("SELECT * FROM pedidos", conn)
    conn.close()
    return df

def deletar_pedido(id_pedido):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id = ?", (id_pedido,))
    conn.commit()
    conn.close()

# --- SISTEMA DE ALARMES EM TEMPO REAL ---
st.header("⏰ Painel de Alertas Urgentes")
df_prazos = listar_pedidos()
alertas_disparados = False

if not df_prazos.empty:
    for index, row in df_prazos.iterrows():
        try:
            # Converte o texto do banco de volta para um objeto de tempo do Python
            prazo_entrega = datetime.strptime(row['data_hora'], "%d/%m/%Y às %H:%M")
            agora = datetime.now()
            
            # Calcula a diferença de tempo
            tempo_restante = prazo_entrega - agora
            horas_restantes = tempo_restante.total_seconds() / 3600
            
            # ALARME CRÍTICO: Menos de 2 horas para a entrega
            if 0 <= horas_restantes <= 2:
                st.error(f"🚨 **ALERTA CRÍTICO:** A entrega de **{row['cliente']}** ({row['arranjo']}) é DAQUI A POUCO, às {prazo_entrega.strftime('%H:%M')}!")
                alertas_disparados = True
                
            # ALARME DE ATENÇÃO: Menos de 24 horas (1 dia) para a entrega
            elif 2 < horas_restantes <= 24:
                st.warning(f"⚠️ **ATENÇÃO:** O arranjo de **{row['cliente']}** precisa ser entregue em menos de 24 horas! (Prazo: {row['data_hora']})")
                alertas_disparados = True
                
            # Pedido que já passou do prazo e não foi deletado
            elif horas_restantes < 0:
                st.info(f"⏳ **Prazo Encerrado:** O pedido de {row['cliente']} passou do horário ({row['data_hora']}). Lembre de excluir se já foi entregue!")
                alertas_disparados = True
        except Exception as e:
            pass

if not alertas_disparados:
    st.success("✅ Tudo sob controle! Nenhuma entrega urgente para as próximas horas.")

st.write("---")

# 3. FORMULÁRIO PARA ADICIONAR CLIENTE
st.header("📋 Novo Pedido")

with st.form(key="form_pedido", clear_on_submit=True):
    nome = st.text_input("Nome do Cliente", placeholder="Ex: Clodoaldo")
    arranjo = st.text_input("Nome do Arranjo", placeholder="Ex: Vaso de Zínias Amarelas")
    
    col1, col2 = st.columns(2)
    with col1:
        orcamento_base = st.number_input("Orçamento do Arranjo (R$)", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        valor_frete = st.number_input("Valor do Frete (R$)", min_value=0.0, step=1.0, format="%.2f")
    
    orcamento_total = orcamento_base + valor_frete
    st.write(f"**Cálculo do Orçamento Total:** R$ {orcamento_total:.2f}")
    
    col3, col4 = st.columns(2)
    with col3:
        data_entrega = st.date_input("Data de Entrega", value=datetime.today())
    with col4:
        hora_entrega = st.time_input("Hora de Entrega")

    botao_salvar = st.form_submit_button(label="Adicionar Cliente")

# 4. LÓGICA DE SALVAMENTO
if botao_salvar:
    if nome and arranjo:
        data_hora_entrega = datetime.combine(data_entrega, hora_entrega)
        data_hora_formatada = data_hora_entrega.strftime("%d/%m/%Y às %H:%M")
        
        salvar_pedido(nome, arranjo, orcamento_base, valor_frete, orcamento_total, data_hora_formatada)
        st.success(f"Pedido de {nome} salvo permanentemente!")
        st.rerun()
    else:
        st.error("Por favor, preencha o nome do cliente e do arranjo.")

# 5. EXIBIÇÃO E EXCLUSÃO DOS PEDIDOS
st.header("📑 Todos os Pedidos Agendados")
df_pedidos = listar_pedidos()

if not df_pedidos.empty:
    for index, row in df_pedidos.iterrows():
        with st.container():
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(f"### 👤 {row['cliente']} — *{row['arranjo']}*")
                st.write(f"📅 **Entrega:** {row['data_hora']}")
                st.write(f"💰 **Base:** R$ {row['orcamento_base']:.2f} | 🚚 **Frete:** R$ {row['frete']:.2f} | 💵 **Total:** R$ {row['orcamento_total']:.2f}")
                st.write("---")
            with col_btn:
                if st.button("❌ Excluir", key=f"del_{row['id']}"):
                    deletar_pedido(row['id'])
                    st.success("Pedido excluído!")
                    st.rerun()
else:
    st.write("Nenhum pedido agendado por enquanto.")
