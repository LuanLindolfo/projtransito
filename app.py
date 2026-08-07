import os
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

# 1. Configuração da Página (Precisa ser obrigatoriamente a primeira linha do Streamlit)
st.set_page_config(page_title="Dashboard de Tráfego", page_icon="🚦", layout="wide")

# 2. Definição de Caminhos dos Arquivos gerados pelo GitHub Actions
DATA_PATH = "data/traffic_log.csv"
IMAGE_PATH = "images/latest_detection.jpg"

st.title("🚦 Dashboard de Monitoramento de Tráfego")
st.markdown("Os dados são atualizados automaticamente em segundo plano.")

# 3. Função segura para carregar os dados (com cache para ficar rápido)
@st.cache_data(ttl=60) # O cache expira a cada 60 segundos para buscar dados novos
def carregar_dados():
    if not os.path.exists(DATA_PATH):
        return None
    
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = carregar_dados()

# 4. Tratamento de Erro: Se o CSV ainda não existir
if df is None or df.empty:
    st.warning("⏳ Aguardando a primeira execução do pipeline de IA gerar os dados...")
    st.stop() # Para a execução do painel aqui para não dar erro

# 5. Estrutura do Dashboard
ultimo_registro = df.iloc[-1]

# Divide a tela em duas colunas (Esquerda para Imagem, Direita para Gráficos)
col_esquerda, col_direita = st.columns([1, 1.2])

with col_esquerda:
    st.subheader("📷 Última Captura do YOLOv8")
    
    if os.path.exists(IMAGE_PATH):
        image = Image.open(IMAGE_PATH)
        st.image(image, caption=f"Atualizado em: {ultimo_registro['timestamp']}", use_column_width=True)
    else:
        st.info("A imagem processada ainda não está disponível.")
        
    st.caption(f"Condição de Iluminação: **{ultimo_registro['periodo']}** (Brilho: {ultimo_registro['brilho']})")

with col_direita:
    st.subheader("📊 Contagem do Momento")
    
    # Cartões de métricas (Metrics nativas do Streamlit)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Carros 🚗", int(ultimo_registro['car']))
    m2.metric("Caminhões 🚚", int(ultimo_registro['truck']))
    m3.metric("Ônibus 🚌", int(ultimo_registro['bus']))
    m4.metric("Pessoas 🚶", int(ultimo_registro['person']))
    
    st.subheader("📈 Histórico (Últimas 24 leituras)")
    
    # Prepara os dados para o Plotly
    df_plot = df.tail(24)
    
    # O comando 'melt' transforma as colunas em linhas para o Plotly criar múltiplas linhas de cores diferentes
    df_melt = df_plot.melt(
        id_vars=['timestamp'], 
        value_vars=['car', 'truck', 'bus', 'person'],
        var_name='Categoria', 
        value_name='Quantidade'
    )
    
    # Gráfico interativo com Plotly Express
    fig = px.line(
        df_melt, 
        x='timestamp', 
        y='Quantidade', 
        color='Categoria',
        markers=True,
        color_discrete_map={
            "car": "blue", 
            "truck": "red", 
            "bus": "orange", 
            "person": "green"
        }
    )
    
    # Remove o fundo branco para integrar melhor com o tema do Streamlit
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    
    # Renderiza o gráfico na tela
    st.plotly_chart(fig, use_container_width=True)
