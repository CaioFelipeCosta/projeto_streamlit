import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configurações de exibição
st.set_page_config(layout = "wide")

# Função para formatar números
def formata_numero(valor, prefixo = ""):
    for unidade in ["", "mil"]:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        valor /= 1000
    return f"{prefixo} {valor:.2f} milhões"

# Título da página
st.title("DASHBOARD DE VENDAS")

# Captura os dados
url = "https://labdados.com/produtos"
regioes = ["Brasil", "Centro-Oeste", "Nordeste", "Norte", "Nordeste", "Sul"]

st.sidebar.title("Filtros")
regiao = st.sidebar.selectbox("Região", regioes)

if regiao == "Brasil":
    regiao = ""

todos_anos = st.sidebar.checkbox("Dados de todo o período", value = True)
if todos_anos:
    ano = ""
else:
    ano = st.sidebar.slider("Ano", 2020, 2023)
    

query_string = {"regiao": regiao.lower(), "ano": ano}

response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados["Data da Compra"] = pd.to_datetime(dados["Data da Compra"], format = "%d/%m/%Y")

filtro_vendedores = st.sidebar.multiselect("Vendedores", dados["Vendedor"].unique())
if filtro_vendedores:
    dados = dados[dados["Vendedor"].isin(filtro_vendedores)]

## Tabelas
# Cria uma tabela com o total vendido por Estado
receita_estados = dados.groupby("Local da compra")[["Preço"]].sum()
# Tira os valores repetidos (estado), mantendo apenas o estado, latitude e longitude, para unir com a tabela com o valor total das vendas por estado
receita_estados = dados.drop_duplicates(subset = "Local da compra")[["Local da compra", "lat", "lon"]].merge(receita_estados, left_on = "Local da compra", right_index = True).sort_values("Preço", ascending = False)

# Cria uma tabela com as vendas totais por período (mês e ano)
receita_mensal = dados.set_index("Data da Compra").groupby(pd.Grouper(freq="M"))["Preço"].sum().reset_index()
receita_mensal["Ano"] = receita_mensal["Data da Compra"].dt.year
receita_mensal["Mês"] = receita_mensal["Data da Compra"].dt.month_name()

# Cria uma tabela para exibir o total de vendas por estados
receita_categorias = dados.groupby("Categoria do Produto")[["Preço"]].sum().sort_values("Preço", ascending = False)

# Cria tabelas de quantidade de vendas
vendas_estados = pd.DataFrame(dados.groupby("Local da compra")["Preço"].count())
vendas_estados = dados.drop_duplicates(subset = "Local da compra")[["Local da compra","lat", "lon"]].merge(vendas_estados, left_on = "Local da compra", right_index = True).sort_values("Preço", ascending = False)
vendas_mensal = pd.DataFrame(dados.set_index("Data da Compra").groupby(pd.Grouper(freq = "M"))["Preço"].count()).reset_index()
vendas_mensal["Ano"] = vendas_mensal["Data da Compra"].dt.year
vendas_mensal["Mes"] = vendas_mensal["Data da Compra"].dt.month_name()
vendas_categorias = pd.DataFrame(dados.groupby("Categoria do Produto")["Preço"].count().sort_values(ascending = False))

# Cria uma tabela vendedores
vendedores = pd.DataFrame(dados.groupby("Vendedor")["Preço"].agg(["sum", "count"]))

## Gráficos
# Cria um gráfico com o total da receita por estado
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = "lat",
                                  lon = "lon",
                                  scope = "south america",
                                  size = "Preço",
                                  template = "seaborn",
                                  hover_name = "Local da compra",
                                  hover_data = {"lat": False, "lon": False,},
                                  title = "Receita por estado")
# Cria um gráfico com as vendas totais por período (mês e ano)
fig_receita_mensal = px.line(receita_mensal,
                             x = "Mês",
                             y = "Preço",
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = "Ano",
                             line_dash = "Ano",
                             title = "Receita mensal")
fig_receita_mensal.update_layout(yaxis_title = "Receita")
# Cria o gráfico de colunas
fig_receita_estados = px.bar(receita_estados.head(),
                             x = "Local da compra",
                             y = "Preço",
                            text_auto = True,
                            title = "Top estados (receita)")
fig_receita_estados.update_layout(yaxis_title = "Receita")
fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = "Receita por categoria")
fig_receita_categorias.update_layout(yaxis_title = "Receita")
# Cria gráficos das quantidade de vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                     lat = "lat", 
                     lon= "lon", 
                     scope = "south america", 
                     #fitbounds = 'locations', 
                     template = "seaborn", 
                     size = "Preço", 
                     hover_name ="Local da compra", 
                     hover_data = {"lat":False, "lon":False},
                     title = "Vendas por estado",
                     )
fig_vendas_mensal = px.line(vendas_mensal, 
              x = "Mes",
              y = "Preço",
              markers = True, 
              range_y = (0,vendas_mensal.max()), 
              color = "Ano", 
              line_dash = "Ano",
              title = "Quantidade de vendas mensal")
fig_vendas_mensal.update_layout(yaxis_title = "Quantidade de vendas")
fig_vendas_estados = px.bar(vendas_estados.head(),
                             x = "Local da compra",
                             y = "Preço",
                             text_auto = True,
                             title = "Top 5 estados"
)
fig_vendas_estados.update_layout(yaxis_title = "Quantidade de vendas")
fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = "Vendas por categoria")
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title = "Quantidade de vendas")

## Visualização
# Cria as abas
aba1, aba2, aba3 = st.tabs(["Receita", "Quantidade de vendas", "Vendedores"])

with aba1:
# Cria duas colunas adicionar elementos para exibição
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados['Preço'].sum(), "R$"))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
        
    with coluna2:
        st.metric("Quantidade total de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)
        
with aba2:
# Cria duas colunas adicionar elementos para exibição
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados['Preço'].sum(), "R$"))
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)
    with coluna2:
        st.metric("Quantidade total de vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)

with aba3:
    qtd_vendedores = st.number_input("Quantidade de vendedores", 2, 10, 5)
# Cria duas colunas adicionar elementos para exibição
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric("Receita", formata_numero(dados['Preço'].sum(), "R$"))
        fig_receita_vendedores = px.bar(vendedores[["sum"]].sort_values("sum", ascending = False).head(qtd_vendedores),
                                        x = "sum",
                                        y = vendedores[["sum"]].sort_values("sum", ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f"Top {qtd_vendedores} vendedores (receita)")
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric("Quantidade total de vendas", formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[["count"]].sort_values("count", ascending = False).head(qtd_vendedores),
                                        x = "count",
                                        y = vendedores[["count"]].sort_values("count", ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f"Top {qtd_vendedores} vendedores (vendas)")
        st.plotly_chart(fig_vendas_vendedores)


# Exibe a tabela com os dados
#st.dataframe(dados)

