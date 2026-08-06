import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Tráfego", layout="wide")
st.title("🚦 Monitoramento de Tráfego em Tempo Real")

# Uso de cache para evitar múltiplas requisições ao GitHub e melhorar a performance
@st.cache_data(ttl=600) # O cache expira a cada 10 minutos
def load_data():
    # Substitua pela URL 'Raw' do seu arquivo no GitHub
    csv_url = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/traffic_log.csv"
    
    df = pd.read_csv(csv_url)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

try:
    df = load_data()
    
    st.markdown("### 📊 Contagem da Última Atualização")
    # Pega a última linha do dataframe
    latest = df.iloc[-1] 
    
    # Cria cards com as métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Carros", int(latest['car']))
    col2.metric("Motos", int(latest['motorcycle']))
    col3.metric("Ônibus", int(latest['bus']))
    col4.metric("Caminhões", int(latest['truck']))

    st.markdown("---")
    st.markdown("### 📈 Tendência de Fluxo")
    
    # Gráfico interativo usando Plotly
    fig = px.line(
        df, 
        x='timestamp', 
        y=['car', 'motorcycle', 'bus', 'truck'],
        labels={'value': 'Quantidade de Veículos', 'timestamp': 'Horário', 'variable': 'Classe'},
        title="Volume de Tráfego ao Longo do Tempo"
    )
    
    # Melhora a exibição do gráfico
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
