import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

# Inicializando o aplicativo Dash
app = dash.Dash(__name__)

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

# Criando gráficos ordenados antes de formatar
fig_er = px.bar(df.sort_values('Engagement rate (ER)', ascending=False), x='Account username', y='Engagement rate (ER)', title='Engagement Rate (ER)')
fig_followers = px.bar(df.sort_values('Followers Growth', ascending=False), x='Account username', y='Followers Growth', title='Followers Growth')

# Extrair categorias únicas
categorias_unicas = set()
df['Categories'].dropna().apply(lambda x: categorias_unicas.update(x.split(', ')))

# Callback para atualizar os gráficos com base nos filtros de data
@app.callback(
    [Output('engagement-rate-graph', 'figure'), Output('followers-growth-graph', 'figure')],
    [Input('start-date-dropdown', 'value'), Input('end-date-dropdown', 'value')]
)
def update_graphs(start_date, end_date):
    # Filtrar o DataFrame com base nas datas selecionadas
    if start_date and end_date:
        filtered_df = df[(df['Data'] >= start_date) & (df['Data'] <= end_date)]
    else:
        filtered_df = df

    # Atualizar os gráficos
    fig_er = px.bar(filtered_df.sort_values('Engagement rate (ER)', ascending=False), x='Account username', y='Engagement rate (ER)', title='Engagement Rate (ER)')
    fig_followers = px.bar(filtered_df.sort_values('Followers Growth', ascending=False), x='Account username', y='Followers Growth', title='Followers Growth')

    return fig_er, fig_followers

# Callback para atualizar os dados das tabelas e dos gráficos de dispersão com base nos filtros
@app.callback(
    [Output('followers-growth-table', 'data'), Output('engagement-rate-table', 'data'), 
     Output('scatter-plot', 'figure'), Output('scatter-plot-unique-categories', 'figure'),
     Output('bar-chart-er-categories', 'figure')],
    [Input('date-range-slider', 'value'),
     Input('username-dropdown', 'value'),
     Input('categories-dropdown', 'value'),
     Input('verified-account-dropdown', 'value'),
     Input('is-brand-dropdown', 'value'),
     Input('cluster-dropdown', 'value')]
)
def update_tables_and_scatters(date_range, selected_usernames, selected_categories, selected_verified, selected_is_brand, selected_cluster):
    # Obter as datas correspondentes aos índices do RangeSlider
    start_date = sorted(df['Data'].unique())[date_range[0]]
    end_date = sorted(df['Data'].unique())[date_range[1]]

    # Filtrar o DataFrame com base nas datas selecionadas
    filtered_df = df[(df['Data'] >= start_date) & (df['Data'] <= end_date)]

    # Filtrar por Account username
    if selected_usernames:
        filtered_df = filtered_df[filtered_df['Account username'].isin(selected_usernames)]

    # Filtrar por Categorias
    if selected_categories is not None:
        if 'Vazio' in selected_categories:
            # Incluir registros onde `Categories` está vazio
            filtered_df = filtered_df[filtered_df['Categories'].isna() | filtered_df['Categories'].apply(lambda x: isinstance(x, str) and any(cat in x.split(', ') for cat in selected_categories if cat != 'Vazio'))]
        else:
            filtered_df = filtered_df[filtered_df['Categories'].apply(lambda x: isinstance(x, str) and any(cat in x.split(', ') for cat in selected_categories))]

    # Filtrar por Verified account
    if selected_verified:
        filtered_df = filtered_df[filtered_df['Verified account'].isin(selected_verified)]

    # Filtrar por Is brand
    if selected_is_brand:
        filtered_df = filtered_df[filtered_df['Is brand'].isin(selected_is_brand)]

    # Filtrar por Cluster
    if selected_cluster:
        filtered_df = filtered_df[filtered_df['Cluster'].isin(selected_cluster)]

    # Verificar o estado dos dados após a aplicação dos filtros
    print('DataFrame filtrado:', filtered_df.head())
    print('Followers max:', filtered_df['Followers max'].head())

    # Ordenar os dados para as tabelas antes de formatar
    followers_growth_data = filtered_df.sort_values('Followers Growth', ascending=False)[['Data', 'Account username', 'Followers Growth', 'Followers max', 'Categories']]
    followers_growth_data['Followers max'] = followers_growth_data['Followers max'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    followers_growth_data['Followers Growth'] = followers_growth_data['Followers Growth'].apply(lambda x: f"{x * 100:.0f}%")
    followers_growth_data = followers_growth_data.to_dict('records')

    engagement_rate_data = filtered_df.sort_values('Engagement rate (ER)', ascending=False)[['Data', 'Account username', 'Engagement rate (ER)', 'Followers max', 'Categories']]
    engagement_rate_data['Followers max'] = engagement_rate_data['Followers max'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    engagement_rate_data['Engagement rate (ER)'] = engagement_rate_data['Engagement rate (ER)'].apply(lambda x: f"{x * 100:.0f}%")
    engagement_rate_data = engagement_rate_data.to_dict('records')

    # Calcular a média de ER por 'Account username' para o gráfico de dispersão
    scatter_data = filtered_df.groupby('Account username').agg({'Engagement rate (ER)': 'mean', 'Followers max': 'mean'}).reset_index()

    # Criar o gráfico de dispersão filtrado com média de ER
    scatter_fig = px.scatter(
        scatter_data,
        x='Engagement rate (ER)',
        y='Followers max',
        size='Followers max',
        color='Account username',
        hover_name='Account username',
        title='Média de ER vs Followers Max'
    )
    scatter_fig.update_layout(xaxis_tickformat='.2%')

    # Criar DataFrame expandido para categorias únicas
    categorias_expandidas = filtered_df.dropna(subset=['Categories']).copy()
    categorias_expandidas['Categories'] = categorias_expandidas['Categories'].apply(lambda x: x.split(', '))
    categorias_expandidas = categorias_expandidas.explode('Categories')

    # Calcular a média de ER por 'Categories' para o gráfico de dispersão
    scatter_data_unique = categorias_expandidas.groupby('Categories').agg({'Engagement rate (ER)': 'mean', 'Followers max': 'mean'}).reset_index()

    # Criar o gráfico de dispersão por média das categorias
    scatter_fig_unique = px.scatter(
        scatter_data_unique,
        x='Engagement rate (ER)',
        y='Followers max',
        size='Followers max',
        color='Categories',
        hover_name='Categories',
        title='Média de ER vs Followers Max por Categoria'
    )
    scatter_fig_unique.update_layout(xaxis_tickformat='.2%')

    # Criar o gráfico de colunas para média de ER por categorias
    bar_chart_er = px.bar(
        categorias_expandidas.groupby('Categories').agg({
            'Engagement rate (ER)': 'mean'
        }).reset_index().sort_values('Engagement rate (ER)', ascending=False),
        x='Categories',
        y='Engagement rate (ER)',
        title='Média de Engagement Rate (ER) por Categoria'
    )

    return followers_growth_data, engagement_rate_data, scatter_fig, scatter_fig_unique, bar_chart_er

# Criar DataFrame expandido para categorias únicas
categorias_expandidas = df.dropna(subset=['Categories']).copy()
categorias_expandidas['Categories'] = categorias_expandidas['Categories'].apply(lambda x: x.split(', '))
categorias_expandidas = categorias_expandidas.explode('Categories')

# Layout do aplicativo
app.layout = html.Div(children=[
    html.H1(children='SUBA RADAR'),

    # Filtro de data com RangeSlider
    dcc.RangeSlider(
        id='date-range-slider',
        min=0,
        max=len(df['Data'].unique()) - 1,
        value=[0, len(df['Data'].unique()) - 1],
        marks={i: str(date) for i, date in enumerate(sorted(df['Data'].unique()))},
        step=None
    ),

    # Filtro de Account username
    dcc.Dropdown(
        id='username-dropdown',
        options=[{'label': username, 'value': username} for username in df['Account username'].unique()],
        placeholder='Selecione um usuário',
        multi=True
    ),

    # Filtro de Categorias
    dcc.Dropdown(
        id='categories-dropdown',
        options=[{'label': category, 'value': category} for category in sorted(categorias_unicas)] + [{'label': 'Vazio', 'value': 'Vazio'}],
        placeholder='Selecione uma categoria',
        multi=True
    ),

    # Filtro de Verified account
    dcc.Dropdown(
        id='verified-account-dropdown',
        options=[{'label': str(verified), 'value': verified} for verified in df['Verified account'].unique()],
        placeholder='Selecione Verified account',
        multi=True
    ),

    # Filtro de Is brand
    dcc.Dropdown(
        id='is-brand-dropdown',
        options=[{'label': str(is_brand), 'value': is_brand} for is_brand in df['Is brand'].unique()],
        placeholder='Selecione Is brand',
        multi=True
    ),

    # Filtro de Cluster
    dcc.Dropdown(
        id='cluster-dropdown',
        options=[{'label': cluster, 'value': cluster} for cluster in df['Cluster'].unique()],
        placeholder='Selecione um Cluster',
        multi=True
    ),

    # Espaço entre filtros e tabelas
    html.Div(style={'margin': '20px 0'}),

    # Tabelas lado a lado
    html.Div(children=[
        html.Div(children=[
            html.H3('Crescimento da Base'),
            dash.dash_table.DataTable(
                id='followers-growth-table',
                columns=[
                    {'name': 'Data', 'id': 'Data'},
                    {'name': '@ do influenciador', 'id': 'Account username'},
                    {'name': 'Influenciador', 'id': 'Account username'},
                    {'name': 'Crescimento da base', 'id': 'Followers Growth'},
                    {'name': 'Seguidores', 'id': 'Followers max'},
                    {'name': 'Categorias', 'id': 'Categories'}
                ],
                data=df[['Data', 'Account username', 'Followers Growth', 'Followers max', 'Categories']].to_dict('records'),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center', 'minWidth': '100px', 'maxWidth': '150px', 'whiteSpace': 'normal'}
            )
        ]),
        html.Div(children=[
            html.H3('Taxa de Engajamento'),
            dash.dash_table.DataTable(
                id='engagement-rate-table',
                columns=[
                    {'name': 'Data', 'id': 'Data'},
                    {'name': '@ do influenciador', 'id': 'Account username'},
                    {'name': 'Influenciador', 'id': 'Account username'},
                    {'name': 'Engagement rate (ER)', 'id': 'Engagement rate (ER)'},
                    {'name': 'Seguidores', 'id': 'Followers max'},
                    {'name': 'Categorias', 'id': 'Categories'}
                ],
                data=df[['Data', 'Account username', 'Engagement rate (ER)', 'Followers max', 'Categories']].to_dict('records'),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center', 'minWidth': '100px', 'maxWidth': '150px', 'whiteSpace': 'normal'}
            )
        ])
    ], style={'display': 'flex', 'justify-content': 'space-between', 'gap': '20px'}),

    # Gráfico de Dispersão #Influs
    dcc.Graph(
        id='scatter-plot',
        figure=px.scatter(
            df,
            x='Engagement rate (ER)',
            y='Followers max',
            size='Followers max',
            color='Account username',
            hover_name='Account username',
            hover_data=['Categories'],
            title='Dispersão de ER vs Followers Max'
        )
    ),

    # Gráfico de Dispersão por Categorias Únicas
    dcc.Graph(
        id='scatter-plot-unique-categories',
        figure=px.scatter(
            categorias_expandidas,
            x='Engagement rate (ER)',
            y='Followers max',
            size='Followers max',
            color='Categories',
            hover_name='Categories',
            hover_data=['Account username'],
            title='Dispersão de ER vs Followers Max por Categoria Única'
        )
    ),

    # Gráfico de Colunas para Média de ER por Categorias
    dcc.Graph(
        id='bar-chart-er-categories',
        figure=px.bar(
            categorias_expandidas.groupby('Categories').agg({'Engagement rate (ER)': 'mean'}).reset_index(),
            x='Categories',
            y='Engagement rate (ER)',
            title='Média de Engagement Rate (ER) por Categoria'
        )
    )
])

# Executando o servidor
if __name__ == '__main__':
    app.run(debug=True, port=8051)

