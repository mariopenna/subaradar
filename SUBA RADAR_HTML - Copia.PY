import streamlit as st
import pandas as pd
import plotly.express as px

# Carregando os dados
caminho_arquivo = r'C:\Users\Mario Gouvea\OneDrive - SUBA CONTEUDO E INFLUENCIA LTDA\Área de Trabalho\SUBA Radar\Basev2.xlsx'
df = pd.read_excel(caminho_arquivo)

# Converter a coluna 'Data' para exibir apenas a data
df['Data'] = pd.to_datetime(df['Data']).dt.date

# Preencher valores NaN na coluna 'Followers max' com zero
df['Followers max'] = df['Followers max'].fillna(0)

# Converter 'Followers Growth' para float antes de ordenar
if df['Followers Growth'].dtype == 'object':
    df['Followers Growth'] = df['Followers Growth'].str.replace('%', '').astype(float) / 100

# Extrair categorias únicas
categorias_unicas = set()
df['Categories'].dropna().apply(lambda x: categorias_unicas.update(x.split(', ')))

# Título do aplicativo
st.title('SUBA RADAR')

# Filtro de data com slider
start_date, end_date = st.slider(
    'Selecione o intervalo de datas',
    min_value=min(df['Data']),
    max_value=max(df['Data']),
    value=(min(df['Data']), max(df['Data']))
)

# Filtro de Account username
selected_usernames = st.multiselect(
    'Selecione um usuário',
    options=df['Account username'].unique()
)

# Filtro de Categorias
selected_categories = st.multiselect(
    'Selecione uma categoria',
    options=sorted(categorias_unicas)
)

# Filtro de Verified account
selected_verified = st.multiselect(
    'Selecione Verified account',
    options=df['Verified account'].unique()
)

# Filtro de Is brand
selected_is_brand = st.multiselect(
    'Selecione Is brand',
    options=df['Is brand'].unique()
)

# Filtro de Cluster
selected_cluster = st.multiselect(
    'Selecione um Cluster',
    options=df['Cluster'].unique()
)

# Filtrar o DataFrame com base nos filtros
filtered_df = df[(df['Data'] >= start_date) & (df['Data'] <= end_date)]

if selected_usernames:
    filtered_df = filtered_df[filtered_df['Account username'].isin(selected_usernames)]

if selected_categories:
    filtered_df = filtered_df[filtered_df['Categories'].apply(lambda x: isinstance(x, str) and any(cat in x.split(', ') for cat in selected_categories))]

if selected_verified:
    filtered_df = filtered_df[filtered_df['Verified account'].isin(selected_verified)]

if selected_is_brand:
    filtered_df = filtered_df[filtered_df['Is brand'].isin(selected_is_brand)]

if selected_cluster:
    filtered_df = filtered_df[filtered_df['Cluster'].isin(selected_cluster)]

# Exibir tabelas
st.subheader('Crescimento da Base')
st.dataframe(filtered_df[['Data', 'Account username', 'Followers Growth', 'Followers max', 'Categories']])

st.subheader('Taxa de Engajamento')
st.dataframe(filtered_df[['Data', 'Account username', 'Engagement rate (ER)', 'Followers max', 'Categories']])

# Criar gráficos
fig_er = px.bar(filtered_df.sort_values('Engagement rate (ER)', ascending=False), x='Account username', y='Engagement rate (ER)', title='Engagement Rate (ER)')
fig_followers = px.bar(filtered_df.sort_values('Followers Growth', ascending=False), x='Account username', y='Followers Growth', title='Followers Growth')

# Exibir gráficos
st.plotly_chart(fig_er)
st.plotly_chart(fig_followers)

