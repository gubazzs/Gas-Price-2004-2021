from datetime import datetime
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import json
import os

##Otimização da Planilha caso necessario
#if not os.path.exists("app/GasOtimized.parquet"):
#    df0409 = pd.read_csv("/home/gubazzs/Documents/DashGasolina/gasolina_2000+.csv", index_col=0)
#    df1021 = pd.read_csv("/home/gubazzs/Documents/DashGasolina/gasolina_2010+.csv", index_col=0)
#
#    df0421 = pd.concat([df0409, df1021])
#    df0421['DATA INICIAL'] = pd.to_datetime(df0421['DATA INICIAL'])
#    df0421['DATA FINAL'] = pd.to_datetime(df0421['DATA FINAL'])
#
#    dfclean = df0421[['DATA INICIAL', 'DATA FINAL', 'REGIÃO', 'ESTADO', 'PRODUTO', 'PREÇO MÉDIO REVENDA']]
#    dfclean.to_csv("app/GasOtimized.csv")
#
#    df0421_csv = pd.read_csv("/home/gubazzs/Documents/DashGasolina/gasolina_2000+.csvGasOtimized.csv", index_col=0)
#
#    df0421_csv.to_parquet("app/GasOtimized_P.parquet", index=False)
#

# Configuração da Página
st.set_page_config(
    page_title="Gas Price - 2004-2021",
    page_icon=":bar_chart:",
    initial_sidebar_state="expanded",
    layout="wide"
)
#CSS Style
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Carregar dados
@st.cache_data
def carregar_dados():
    return pd.read_parquet("GasOtimized_P.parquet")

df = carregar_dados()


# Carregar GeoJSON
@st.cache_data
def carregar_geojson():
    with open("brazil_geo.json", "r") as f:
        return json.load(f)

brazil_states = carregar_geojson()

# Converter para datetime.date antes de passar para st.date_input
def CvDate(valor):
    if isinstance(valor, str):
        return pd.to_datetime(valor).date()  # Converte string para datetime.date
    elif isinstance(valor, pd.Timestamp):
        return valor.date()  # Converte Timestamp para datetime.date
    return valor

# Inicializar session_state
for key, default in {
    "selected_estado": "TODOS",
    "selected_regiao": "TODOS",
    "selected_produto": df["PRODUTO"].iloc[0],
    "selected_data_inicial": CvDate(df["DATA INICIAL"].min()),
    "selected_data_final": CvDate(df["DATA FINAL"].max())
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

#Função para filtrar os dados
def filtrar_dados():
    df_filtrado = df.copy()

    # Converter as colunas de data para datetime
    df_filtrado["DATA INICIAL"] = pd.to_datetime(df_filtrado["DATA INICIAL"])
    df_filtrado["DATA FINAL"] = pd.to_datetime(df_filtrado["DATA FINAL"])

    data_inicial = pd.Timestamp(st.session_state["selected_data_inicial"])
    data_final = pd.Timestamp(st.session_state["selected_data_final"])

    df_filtrado = df_filtrado[
        (df_filtrado["DATA INICIAL"] >= data_inicial) & 
        (df_filtrado["DATA FINAL"] <= data_final)
    ]

    if st.session_state["selected_produto"] != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["PRODUTO"] == st.session_state["selected_produto"]]

    if st.session_state["selected_regiao"] != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["REGIÃO"] == st.session_state["selected_regiao"]]

    if st.session_state["selected_estado"] != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["ESTADO"] == st.session_state["selected_estado"]]

    return df_filtrado

# **Criar o mapa (sem cache para refletir mudanças imediatamente)**
def criar_mapa(df_filtrado):
    return px.choropleth_map(
        df_filtrado,
        locations="ESTADO",
        geojson=brazil_states,
        color="PREÇO MÉDIO REVENDA",
        color_continuous_scale="Bluered",
        center={"lat": -14.23, "lon": -51.92},
        zoom=4,
        opacity=0.7,
        map_style="carto-darkmatter",
        hover_data={"ESTADO": True, "PRODUTO": True, "PREÇO MÉDIO REVENDA": True}
    ).update_layout(
        width=1920,
        height=1080,
        autosize=True,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        margin=dict(r=0, t=0, l=0, b=0)
    )

# **Criar gráfico de evolução do preço médio**
def criar_grafico(df_filtrado):
    df_filtrado['PREÇO MÉDIO REVENDA'] = pd.to_numeric(df_filtrado['PREÇO MÉDIO REVENDA'], errors='coerce').fillna(0)
    df_filtrado = df_filtrado.groupby(['DATA INICIAL', 'ESTADO'])[['PREÇO MÉDIO REVENDA']].mean().reset_index()

    return px.line(
        df_filtrado,
        x="DATA INICIAL",
        y="PREÇO MÉDIO REVENDA",
        color="ESTADO" if st.session_state["selected_estado"] == "TODOS" else None,
        title=f"Evolução do Preço Médio - {st.session_state['selected_produto']}",
        labels={"DATA INICIAL": "Data", "PREÇO MÉDIO REVENDA": "Preço Médio (R$)"},
        markers=True
    ).update_layout(
        autosize=True,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        margin=dict(r=0, t=0, l=0, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        legend=dict(
            orientation="h",  # Define a orientação horizontal
            x=0.5,  # Centraliza a legenda horizontalmente
            y=-0.2,  # Move a legenda para baixo do gráfico
            xanchor="center",  # Define a âncora horizontal no centro
            yanchor="top",  # Define a âncora vertical no topo
            bgcolor="rgba(0,0,0,0.5)",  # Fundo semitransparente
            bordercolor="white",
            borderwidth=1
        )
    )
# Inicializar a chave no session_state, caso não exista
if "trigger_rerun" not in st.session_state:
    st.session_state["trigger_rerun"] = False

# Função de atualização que ativa o rerun
def atualizar():
    st.session_state["trigger_rerun"] = True

# Layout principal
df_filtrado = filtrar_dados()

with st.container():
    st.plotly_chart(criar_mapa(df_filtrado), use_container_width=True)

# Sidebar
with st.sidebar:
    st.title("RIBAZZS")
    st.write("Preço do Combustível de 2004 a 2021")

    Produto, DataInicial, DataFinal = st.columns([2, 1, 1])

    with Produto:
        st.selectbox(
            "Produtos",
            options=df["PRODUTO"].unique(),
            key="selected_produto"
        )

    with DataInicial:
        st.date_input(
            "DATA INICIAL",
            #value=CvDate(st.session_state["selected_data_inicial"]),
            min_value=CvDate(df["DATA INICIAL"].min()),
            max_value=CvDate(df["DATA INICIAL"].max()),
            key="selected_data_inicial"
        )

    with DataFinal:
        st.date_input(
            "DATA FINAL",
            #value=CvDate(st.session_state["selected_data_final"]),
            min_value=CvDate(df["DATA INICIAL"].min()),
            max_value=CvDate(df["DATA FINAL"].max()),
            key="selected_data_final"
        )

    if pd.Timestamp(st.session_state["selected_data_inicial"]) > pd.Timestamp(st.session_state["selected_data_final"]):
        st.error("A data inicial deve ser anterior ou igual à data final.", icon="⚠️")

    Brazil_btt, Regiao_box, Estado_box = st.columns([1, 2, 2.5], vertical_alignment='bottom')

    with Brazil_btt:
        if st.button("Brasil", type="primary"):
            st.session_state["selected_regiao"] = "TODOS"
            st.session_state["selected_estado"] = "TODOS"
            atualizar()

    with Regiao_box:
        st.selectbox(
            "Região",
            options=np.append(df["REGIÃO"].unique(), "TODOS"),
            key="selected_regiao",
            on_change=atualizar
        )

    with Estado_box:
        estados = np.append(df[df["REGIÃO"] == st.session_state["selected_regiao"]]["ESTADO"].unique(), "TODOS") if st.session_state["selected_regiao"] in df["REGIÃO"].unique() else ["TODOS"]
        st.selectbox(
            "Estado",
            options=estados,
            key="selected_estado",
        )

    #if st.button("Aplicar", type="primary"):
    #    atualizar()

    preco_medio = df_filtrado.loc[df_filtrado["DATA FINAL"].idxmax(), "PREÇO MÉDIO REVENDA"] if not df_filtrado.empty else 0
        
    preco_inicial = df_filtrado.loc[df_filtrado["DATA INICIAL"].idxmin(), "PREÇO MÉDIO REVENDA"] if not df_filtrado.empty else 0
    preco_final = df_filtrado.loc[df_filtrado["DATA FINAL"].idxmax(), "PREÇO MÉDIO REVENDA"] if not df_filtrado.empty else 0

    # Evitar divisão por zero
    if preco_inicial != 0:
        variacao_percentual = ((preco_final - preco_inicial) / preco_inicial) * 100
    else:
        variacao_percentual = 0

    delta_preco = preco_final - preco_inicial  # Diferença do preço

    Metric_Revenda, Metric_Crescimento_Porcent = st.columns([1,1], vertical_alignment="center")

    # Obtém o valor da data final correspondente
    data_final_str = str(df_filtrado.loc[df_filtrado["DATA FINAL"].idxmax(), "DATA FINAL"])

    # Garante que a string esteja no formato correto antes de converter
    data_formatada = datetime.strptime(data_final_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y")

    with Metric_Revenda:
        st.metric(
            label=f"Preço Revenda de {data_formatada}",
            value=f"R$ {preco_medio:.2f}",
            delta=f"R$ {delta_preco:.2f}",
            delta_color="inverse" if delta_preco < 0 else "normal",  # Corrige cor
            border=True
        )

    with Metric_Crescimento_Porcent:
        st.metric(
            label="Crescimento %",
            value=f"{variacao_percentual:.2f}%",
            delta=f"{variacao_percentual:.2f}%",
            border=True
        )
    
    # Gráfico de evolução do preço médio
    with st.container():
        st.plotly_chart(criar_grafico(df_filtrado), use_container_width=True)

    @st.cache_data
    @st.dialog("Como Funciono?")
    def quest():
        st.title("Ola!")
            
    if st.button("?", key="floating_button"):
        quest()
