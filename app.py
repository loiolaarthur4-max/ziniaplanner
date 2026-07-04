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

def atualizar_pedido(id_pedido, cliente, arranjo, ob, fr, total, data_hora):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE pedidos 
        SET cliente = ?, arranjo = ?, orcamento_base = ?, frete = ?, orcamento_total = ?, data_hora = ?
        WHERE id = ?
    ''', (cliente, arranjo, ob, fr, total, data_hora, id_pedido))
    conn.commit()
    conn.close()

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
            prazo_entrega = datetime.strptime(row['data_hora'], "%d/%m/%Y às %H:%M")
            agora = datetime.now()
            tempo_restante = prazo_entrega - agora
            horas_restantes = tempo_restante.total_seconds() / 3600
            
            if 0 <= horas_restantes <= 2:
                st.error(f"🚨 **ALERTA CRÍTICO:** A entrega de **{row['cliente']}** ({row['arranjo']}) é DAQUI A POUCO, às {prazo_entrega.strftime('%H:%M')}!")
                alertas_disparados = True
            elif 2 < horas_restantes <= 24:
                st.warning(f"⚠️ **ATENÇÃO:** O arranjo de **{row['cliente']}** precisa ser entregue em menos de 24 horas! (Prazo: {row['data_hora']})")
                alertas_disparados = True
            elif horas_restantes < 0:
                st.info(f"⏳ **Prazo Encerrado:** O pedido de {row['cliente']} passou do horário ({row['data_hora']}).")
                alertas_disparados = True
        except:
            pass

if not alertas_disparados:
    st.success("✅ Tudo sob controle! Nenhuma entrega urgente para as próximas horas.")

st.write("---")

# Criando duas abas para organizar o app: uma para ver/editar e outra para adicionar novos
aba_visualizar, aba_adicionar = st.tabs(["📑 Pedidos Agendados", "➕ Adicionar Novo Pedido"])

# 3. ABA: ADICIONAR CLIENTE
with aba_adicionar:
    st.header("📋 Novo Pedido")
    with st.form(key="form_pedido", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente", placeholder="Ex: Clodoaldo")
        arranjo = st.text_input("Nome do Arranjo", placeholder="Ex: Vaso de Zínias Amarelas")
        
        col1, col2 = st.columns(2)
        with col1:
            orcamento_base = st.number_input("Orçamento do Arranjo (R$)", min_value=0.0, step=1.0, format="%.2f", key="add_ob")
        with col2:
            valor_frete = st.number_input("Valor do Frete (R$)", min_value=0.0, step=1.0, format="%.2f", key="add_fr")
        
        orcamento_total = orcamento_base + valor_frete
        st.write(f"**Cálculo do Orçamento Total:** R$ {orcamento_total:.2f}")
        
        col3, col4 = st.columns(2)
        with col3:
            data_entrega = st.date_input("Data de Entrega", value=datetime.today(), key="add_dt")
        with col4:
            hora_entrega = st.time_input("Hora de Entrega", key="add_hr")

        botao_salvar = st.form_submit_button(label="Adicionar Cliente")

    if botao_salvar:
        if nome and arranjo:
            data_hora_entrega = datetime.combine(data_entrega, hora_entrega)
            data_hora_formatada = data_hora_entrega.strftime("%d/%m/%Y às %H:%M")
            salvar_pedido(nome, arranjo, orcamento_base, valor_frete, orcamento_total, data_hora_formatada)
            st.success(f"Pedido de {nome} salvo permanentemente!")
            st.rerun()
        else:
            st.error("Por favor, preencha o nome do cliente e do arranjo.")

# 4. ABA: LISTAR, EXCLUIR E EDITAR PEDIDOS
with aba_visualizar:
    st.header("📑 Todos os Pedidos")
    df_pedidos = listar_pedidos()

    # Cria uma variável no session_state para saber qual item estamos editando
    if "id_editando" not in st.session_state:
        st.session_state.id_editando = None

    if not df_pedidos.empty:
        for index, row in df_pedidos.iterrows():
            with st.container():
                col_info, col_botoes = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"### 👤 {row['cliente']} — *{row['arranjo']}*")
                    st.write(f"📅 **Entrega:** {row['data_hora']}")
                    st.write(f"💰 **Base:** R$ {row['orcamento_base']:.2f} | 🚚 **Frete:** R$ {row['frete']:.2f} | 💵 **Total:** R$ {row['orcamento_total']:.2f}")
                
                with col_botoes:
                    # Botão para ativar o modo de edição deste ID
                    if st.button("✏️ Editar", key=f"btn_edit_{row['id']}"):
                        st.session_state.id_editando = row['id']
                        st.rerun()
                        
                    # Botão para excluir
                    if st.button("❌ Excluir", key=f"del_{row['id']}"):
                        deletar_pedido(row['id'])
                        st.success("Pedido excluído!")
                        st.rerun()
                
                # SE O USUÁRIO CLICOU EM EDITAR NESTE PRODUTO, MOSTRA O FORMULÁRIO DE EDIÇÃO LOGO ABAIXO DELE
                if st.session_state.id_editando == row['id']:
                    st.info(f"Modo de Edição: Alterando dados de {row['cliente']}")
                    
                    with st.form(key=f"form_edit_{row['id']}"):
                        novo_nome = st.text_input("Nome do Cliente", value=row['cliente'])
                        novo_arranjo = st.text_input("Nome do Arranjo", value=row['arranjo'])
                        
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            novo_ob = st.number_input("Orçamento do Arranjo (R$)", min_value=0.0, value=row['orcamento_base'], format="%.2f")
                        with edit_col2:
                            novo_fr = st.number_input("Valor do Frete (R$)", min_value=0.0, value=row['frete'], format="%.2f")
                        
                        novo_total = novo_ob + novo_fr
                        st.write(f"**Novo Orçamento Total:** R$ {novo_total:.2f}")
                        
                        # Tenta recuperar as datas antigas para preencher o formulário
                        try:
                            dt_antiga = datetime.strptime(row['data_hora'], "%d/%m/%Y às %H:%M")
                            val_dt = dt_antiga.date()
                            val_hr = dt_antiga.time()
                        except:
                            val_dt = datetime.today()
                            val_hr = datetime.now().time()

                        edit_col3, edit_col4 = st.columns(2)
                        with edit_col3:
                            nova_dt = st.date_input("Nova Data", value=val_dt)
                        with edit_col4:
                            nova_hr = st.time_input("Nova Hora", value=val_hr)
                        
                        col_salvar_cancelar = st.columns(2)
                        with col_salvar_cancelar[0]:
                            btn_atualizar = st.form_submit_button("💾 Salvar Alterações")
                        with col_salvar_cancelar[1]:
                            btn_cancelar = st.form_submit_button("Cancel")
                            
                        if btn_atualizar:
                            nova_data_hora = datetime.combine(nova_dt, nova_hr)
                            nova_dt_formatada = nova_data_hora.strftime("%d/%m/%Y às %H:%M")
                            
                            # Atualiza no banco SQLite
                            atualizar_pedido(row['id'], novo_nome, novo_arranjo, novo_ob, novo_fr, novo_total, nova_dt_formatada)
                            st.success("Pedido atualizado com sucesso!")
                            st.session_state.id_editando = None # Sai do modo de edição
                            st.rerun()
                            
                        if btn_cancelar:
                            st.session_state.id_editando = None # Cancela e fecha o form
                            st.rerun()
                st.write("---")
    else:
        st.write("Nenhum pedido agendado por enquanto.")
