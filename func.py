# func.py
import pandas as pd
import numpy as np
import streamlit as st
import json
import io
from datetime import datetime
from scipy.stats import norm
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import requests
import traceback
from utils_format import exibir_cards_de_posts, formatar_tabela_distribuicao_educacao, exibir_cartao, exibir_cartao_riscos, formatar_tabela_classes_sociais

# Inicialização centralizada de todas as chaves do session_state
keys_default = {
    "influencers_nomes": [],
    "influencers_dados": {},
    "df_classes_formatado": pd.DataFrame(),
    "df_educacao_formatado": pd.DataFrame(),
    "df_top_interesses_formatado": pd.DataFrame(),
    "perfis_e_dispersoes": {}
}

for key, val in keys_default.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Dicionário de tradução dos interesses
interests_translation = {
	"Activewear": "Roupas Esportivas",
	"Friends, Family & Relationships": "Amigos, Família e Relacionamentos",
	"Clothes, Shoes, Handbags & Accessories": "Moda",
	"Beauty & Cosmetics": "Beleza e Cosméticos",
	"Camera & Photography": "Fotografia",
	"Toys, Children & Baby": "Brinquedos, Crianças e Bebês",
	"Television & Film": "Televisão e Filmes",
	"Restaurants, Food & Grocery": "Restaurantes e Gastronomia",
	"Music": "Música",
	"Fitness & Yoga": "Fitness e Yoga",
	"Travel, Tourism & Aviation": "Turismo e Aviação",
	"Pets": "Animais de Estimação",
	"Cars & Motorbikes": "Carros e Motocicletas",
	"Beer, Wine & Spirits": "Cerveja, Vinho e Bebidas Alcoólicas",
	"Art & Design": "Arte e Design",
	"Sports": "Esportes",
	"Electronics & Computers": "Eletrônicos e Computadores",
	"Healthy Lifestyle": "Estilo de Vida Saudável",
	"Shopping & Retail": "Compras e Varejo",
	"Coffee, Tea & Beverages": "Café, Chá e Bebidas Quentes",
	"Jewellery & Watches": "Joias e Relógios",
	"Luxury Goods": "Artigos de Luxo",
	"Home Decor, Furniture & Garden": "Decoração, Móveis e Jardim",
	"Wedding": "Casamento",
	"Gaming": "Jogos Digitais",
	"Business & Careers": "Negócios e Carreiras",
	"Healthcare & Medicine": "Saúde e Medicina"
}

def carregar_planilhas_estaticas():
    """
    Carrega os arquivos de classes sociais e educação por cidade da pasta 'dados/'
    e armazena no session_state.
    """

    # Caminhos dos arquivos
    caminho_classes = "./dados/classes_sociais_por_cidade.xlsx"
    caminho_educacao = "./dados/educacao_por_cidade.xlsx"

    # Carrega apenas se ainda não estiverem no session_state
    if "df_classes_sociais" not in st.session_state:
        try:
            st.session_state.df_classes_sociais = pd.read_excel(caminho_classes)
        except Exception as e:
            st.error(f"Erro ao carregar 'classes_sociais_por_cidade.xlsx': {e}")
            st.session_state.df_classes_sociais = pd.DataFrame()

    if "df_educacao_por_cidade" not in st.session_state:
        try:
            st.session_state.df_educacao_por_cidade = pd.read_excel(caminho_educacao)
        except Exception as e:
            st.error(f"Erro ao carregar 'educacao_por_cidade.xlsx': {e}")
            st.session_state.df_educacao_por_cidade = pd.DataFrame()

def format_milhar(valor):
	return f"{round(valor):,}".replace(",", ".") if valor is not None else None

def get_classes_sociais_formatadas(df, nome_influencer):
    resultado = df.loc[df["influencer"] == nome_influencer, "classes_sociais_formatadas"].values
    return resultado[0] if len(resultado) > 0 else "N/A"

def get_escolaridades_formatadas(df, nome_influencer, default="N/A"):
    if df.empty or "influencer" not in df.columns:
        return default
    
    # Normaliza buscas (remove espaços e força caixa baixa para bater com o username)
    nome_alvo = str(nome_influencer).strip().lower()
    
    # Procura considerando busca case-insensitive
    df_temp = df.copy()
    df_temp["influencer_norm"] = df_temp["influencer"].astype(str).str.strip().str.lower()
    
    vals = df_temp.loc[df_temp["influencer_norm"] == nome_alvo, "educacao_formatada"]
    return vals.iloc[0] if not vals.empty else default

def calcular_dispersao_likes_comentarios(influencers_nomes, api_key="7f728d8233msh6b5402b6234f32ep135c63jsn7b9cdd64c9f7"):
    """
    Calcula a dispersão de likes e comentários dos últimos posts de influenciadores via API.

    Parâmetros:
        influencers_nomes (string): string com nome do influenciador.
        api_key (str): chave da API do RapidAPI.

    Retorno:
        dict: {nome_influencer: dispersão_normalizada_média}
    """

    url = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }

    try:
        likes_por_post = []
        comments_por_post = []

        querystring = {"username_or_id_or_url": influencers_nomes}
        response = requests.get(url, headers=headers, params=querystring)
        results = response.json()

        if "data" not in results or "items" not in results["data"]:
            st.warning(f"Resposta inválida para o perfil '{perfil}'.")

        n_posts = min(12, len(results["data"]["items"]))

        for i in range(n_posts):
            item = results["data"]["items"][i]
            likes_por_post.append(int(item.get("like_count") or 0))
            comments_por_post.append(int(item.get("comment_count") or 0))

        if not likes_por_post or not comments_por_post:
            st.warning(f"Perfil '{influencers_nomes}' sem dados de likes ou comentários.")

        media_likes = np.mean(likes_por_post)
        media_comments = np.mean(comments_por_post)
        desvpad_likes = np.std(likes_por_post)
        desvpad_comments = np.std(comments_por_post)

        if media_likes == 0 or media_comments == 0:
            st.warning(f"Perfil '{influencers_nomes}' com média de likes ou comentários zero.")

        norm_likes = (desvpad_likes / media_likes) * 100
        norm_comments = (desvpad_comments / media_comments) * 100
        dispersao_media = round((norm_likes + norm_comments) / 2, 0)

        return dispersao_media

    except Exception as e:
        st.warning(f"Erro ao processar dados de '{perfil}': {e}")

def consolidar_dados_de_perfil():
    dados_consolidados = {}

    # Check if the key exists in session_state before iteration
    if "influencers_nomes" not in st.session_state or "influencers_dados" not in st.session_state:
        st.warning("Nenhum influenciador foi carregado no session_state ainda.")
        return pd.DataFrame()

    for nome in st.session_state.influencers_nomes:
        try:
            dados = st.session_state.influencers_dados.get(nome, {})
            perfil = dados.get("user_profile", {})

            engagement_rate = perfil.get("engagement_rate")
            engagement_rate_str = f"{round(engagement_rate * 100, 2)}%" if engagement_rate is not None else None

            dados_consolidados[nome] = {
                "Followers": format_milhar(perfil.get("followers")),
                "Engajamento (%)": engagement_rate_str,
                "Média de Likes": format_milhar(perfil.get("avg_likes")),
                "Média de Comments": format_milhar(perfil.get("avg_comments")),
                "Média de Views (Reels)": format_milhar(perfil.get("avg_reels_plays")),
            }

        except Exception as e:
            st.warning(f"Erro ao processar dados de {nome}: {e}")

    try:
        df_consolidado = pd.DataFrame.from_dict(dados_consolidados, orient='index')
        if not df_consolidado.empty:
            df_consolidado.reset_index(inplace=True)
            df_consolidado.rename(columns={"index": "influencer"}, inplace=True)
        return df_consolidado
    except Exception as e:
        st.warning(f"Erro ao consolidar os dados: {e}")
        return pd.DataFrame()
    
def exibir_analise_individual(nome_influenciador):
    try:
        dados = st.session_state.influencers_dados[nome_influenciador]
        perfil = dados.get("user_profile", {})
        stat_history = perfil.get("stat_history", [])

        if not stat_history:
            st.info(f"Sem dados históricos para {nome_influenciador}")
            return

        # Cartões resumo
        col1, col2, col3 = st.columns(3)
        with col1:
            exibir_cartao("Likes Ocultos", f"{perfil.get('posts_with_hidden_like_percentage', 0):.1f}% dos posts")
        with col2:
            sentimento = perfil.get("comments_sentiment_analysis", {}).get("avg_sentiment", 0)
            exibir_cartao("Sentimento Médio", f"{sentimento:.2f}")
        with col3:
            brand_score = perfil.get("brand_safety_analysis", {}).get("brand_safety_score", 0)
            riscos = perfil.get("brand_safety_analysis", {}).get("risks", [])
            exibir_cartao_riscos("Brand Safety", brand_score, riscos)

        # Tags relevantes
        st.markdown("## Tags mais semelhantes ao conteúdo #️⃣")
        tags = perfil.get("relevant_tags", [])[:12]
        num_columns = 3
        for i in range(0, len(tags), num_columns):
            cols = st.columns(num_columns)
            for j, tag in enumerate(tags[i:i+num_columns]):
                with cols[j]:
                    exibir_cartao(tag['tag'], f"Distância: {tag['distance']:.2f}")

        # Gráficos históricos
        df_hist = pd.DataFrame(stat_history)
        df_hist['month'] = pd.to_datetime(df_hist['month'])
        df_hist = df_hist.sort_values('month')

        formatador = FuncFormatter(lambda x, _: f'{int(x):,}'.replace(",", "."))

        st.subheader(f"Evolução histórica - {nome_influenciador}")

        # Gráfico Followers
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(df_hist['month'], df_hist['followers'], marker='o')
        ax1.set_title('Followers')
        ax1.set_xlabel('Mês')
        ax1.set_ylabel('Followers')
        ax1.yaxis.set_major_formatter(formatador)
        ax1.grid(True)
        fig1.autofmt_xdate()
        st.pyplot(fig1)

        # Gráfico Engajamento Médio
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(df_hist['month'], df_hist['avg_engagements'], color='orange', marker='o')
        ax2.set_title('Engajamento Médio')
        ax2.set_xlabel('Mês')
        ax2.set_ylabel('Engajamentos')
        ax2.yaxis.set_major_formatter(formatador)
        ax2.grid(True)
        fig2.autofmt_xdate()
        st.pyplot(fig2)

    except Exception as e:
        st.warning(f"Erro ao gerar gráficos para {nome_influenciador}: {e}")

def exibir_cidades_por_influencer(df_cidades):
    """
    Exibe a tabela de cidades por influenciador com seleção de top N
    e permite exportar para Excel.
    """
    if df_cidades.empty:
        st.info("Nenhum dado de cidades disponível.")
        return

    df_exibicao = df_cidades.copy()

    # Limpar colunas indesejadas
    colunas_remover = [
        "coords.lat", "coords.lon", "country.id",
        "country.code", "state.id", "state.name", "id"
    ]
    df_exibicao.drop(columns=colunas_remover, inplace=True, errors="ignore")

    # Formatando coluna de peso como porcentagem
    if "weight" in df_exibicao.columns:
        df_exibicao["weight"] = df_exibicao["weight"] * 100
        df_exibicao["weight"] = df_exibicao["weight"].round(2).astype(str) + "%"
        df_exibicao.rename(columns={"weight": "Porcentagem da audiência"}, inplace=True)

    # Seleção do número de registros por influenciador
    top_n = st.selectbox("Quantas cidades deseja exibir por influencer?", [5, 10, 15, 20], index=0)

    df_exibicao = (
        df_exibicao
        .sort_values(by=["influencer", "Porcentagem da audiência"], ascending=[True, False])
        .groupby("influencer")
        .head(top_n)
    )

    st.dataframe(df_exibicao)

    # Exportação para Excel
    data_hoje = datetime.today().strftime("%Y-%m-%d")
    file_name = f"cidades_por_influencer_{data_hoje}.xlsx"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_exibicao.to_excel(writer, index=False, sheet_name='Cidades')
    output.seek(0)

    st.download_button(
        label="📥 Baixar tabela de cidades como Excel",
        data=output,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def calcular_distribuicao_classes_sociais(df_cidades, url_planilha_classes):
    """
    Faz o cálculo da distribuição de classes sociais ponderada por cidade.

    Parâmetros:
        df_cidades (pd.DataFrame): Dados de cidades com coluna 'weight' e 'Cidade'.
        url_planilha_classes (str): URL do arquivo Excel com as classes por cidade.

    Retorna:
        pd.DataFrame: Tabela formatada com distribuição de classes sociais por influenciador.
    """
    try:
        # Carregar a planilha de classes sociais
        classes_por_cidade = pd.read_excel(url_planilha_classes, header=0)

        # Normalizar peso por influencer
        df_cidades = df_cidades.copy()
        df_cidades["normalized_weight"] = df_cidades.groupby("influencer")["weight"].transform(lambda x: x / x.sum())

        # Merge com base na cidade
        df_merged = pd.merge(df_cidades, classes_por_cidade, on="Cidade", how="inner")

        # Calcular média ponderada para cada classe
        df_merged["normalized_classe_de"] = df_merged["normalized_weight"] * df_merged["Classes D e E"]
        df_merged["normalized_classe_c"] = df_merged["normalized_weight"] * df_merged["Classe C"]
        df_merged["normalized_classe_b"] = df_merged["normalized_weight"] * df_merged["Classe B"]
        df_merged["normalized_classe_a"] = df_merged["normalized_weight"] * df_merged["Classe A"]

        # Agregar resultado por influencer
        result = df_merged.groupby("influencer")[
            ["normalized_classe_de", "normalized_classe_c", "normalized_classe_b", "normalized_classe_a"]
        ].sum()
        result = result.round(2)

        # Formatar resultado para exibição
        df_formatado = formatar_tabela_classes_sociais(result)

        return df_formatado

    except Exception as e:
        st.error(f"Erro ao carregar ou processar a planilha de classes sociais: {e}")
        return pd.DataFrame()
    
def calcular_distribuicao_educacao(df_cidades, df_dados):
    """
    Calcula a distribuição educacional estimada dos influenciadores com base nos dados da audiência.
    """
    df = pd.DataFrame()
    df_ages = pd.DataFrame()

    # Extrair dados de cidades e idades
    for nome, data in df_dados.items():
        try:
            audience_data = data.get("audience_followers", {}).get("data", {})
            
            cities_entries = audience_data.get("audience_geo", {}).get("cities", [])
            df_cities = pd.json_normalize(cities_entries)
            df_cities["influencer"] = nome
            df = pd.concat([df, df_cities], ignore_ignore_index=True if hasattr(pd.concat, 'ignore_index') else False, ignore_index=True)

            age_entries = audience_data.get("audience_genders_per_age", [])
            df_idades = pd.json_normalize(age_entries)
            df_idades["influencer"] = nome
            df_ages = pd.concat([df_ages, df_idades], ignore_index=True)

        except Exception as e:
            st.warning(f"Erro ao processar dados de {nome}: {e}")

    if df.empty or df_ages.empty:
        st.info("Dados insuficientes para análise educacional.")
        return pd.DataFrame()

    try:
        # Converter para numérico
        df_ages["male"] = pd.to_numeric(df_ages["male"], errors="coerce").fillna(0)
        df_ages["female"] = pd.to_numeric(df_ages["female"], errors="coerce").fillna(0)

        df["Cidade"] = df["name"]
        df_unido = pd.merge(df, df_ages, on="influencer")

        # 1. Normalização do peso das cidades por influenciador
        total_weight_por_influencer = df_unido.groupby("influencer")["weight"].transform("sum")
        total_weight_por_cidade = df_unido.groupby(["influencer", "Cidade"])["weight"].transform("sum")
        
        # Evita divisão por zero
        df_unido["weight_normalized"] = np.where(
            total_weight_por_influencer > 0, 
            total_weight_por_cidade / total_weight_por_influencer, 
            0
        )

        # 2. Aplicação correta do peso na proporção de gênero/idade (Sem duplicar a multiplicação)
        df_unido["female_weighted"] = df_unido["female"] * df_unido["weight_normalized"]
        df_unido["male_weighted"] = df_unido["male"] * df_unido["weight_normalized"]

        df_unido.rename(columns={"code": "Grupo Etário"}, errors="ignore", inplace=True)

        # Carregar dados educacionais do session_state
        df_edu = st.session_state.df_educacao_por_cidade

        # Realiza o Merge com os dados de escolaridade base por cidade e faixa etária
        df_unido_edu = df_unido.merge(df_edu, on=["Cidade", "Grupo Etário"], how="left")

        # 3. Média Ponderada: Multiplica a taxa educacional pelos pesos já ponderados
        # Supondo que a planilha de educação tenha as colunas 'anos_estudo_female' e 'anos_estudo_male'
        if "anos_estudo_female" in df_unido_edu.columns and "anos_estudo_male" in df_unido_edu.columns:
            df_unido_edu["anos_female"] = df_unido_edu["female_weighted"] * df_unido_edu["anos_estudo_female"]
            df_unido_edu["anos_male"] = df_unido_edu["male_weighted"] * df_unido_edu["anos_estudo_male"]
        else:
            # Caso a planilha `educacao_por_cidade.xlsx` use apenas uma coluna agregada de escolaridade
            coluna_edu = [c for c in df_edu.columns if c not in ["Cidade", "Grupo Etário"]][0]
            df_unido_edu["anos_female"] = df_unido_edu["female_weighted"] * df_unido_edu[coluna_edu]
            df_unido_edu["anos_male"] = df_unido_edu["male_weighted"] * df_unido_edu[coluna_edu]

        # Agrupamento final
        result_edu = df_unido_edu.groupby("influencer")[["anos_female", "anos_male"]].sum().sum(axis=1)

        return formatar_tabela_distribuicao_educacao(result_edu)

    except Exception as e:
        st.error(f"Erro ao calcular distribuição educacional: {e}")
        return pd.DataFrame()

def extrair_top_interesses_formatados(dados_influencers: dict, interests_translation: dict) -> pd.DataFrame:
    """
    Extrai e formata os 5 principais interesses de cada influenciador.

    Parâmetros:
        dados_influencers (dict): dicionário com os dados JSON de cada influenciador (já carregados).
        interests_translation (dict): dicionário de tradução dos interesses (ex: inglês → português).

    Retorno:
        pd.DataFrame com colunas [influencer, interesses_formatados]
    """
    df_resultado = []

    for nome, dados in dados_influencers.items():
        try:
            interests_entries = dados.get("audience_followers", {}).get("data", {}).get("audience_interests", [])
            if not isinstance(interests_entries, list):
                continue

            # Ordenar por peso e pegar top 5
            top_interests = sorted(interests_entries, key=lambda x: x.get("weight", 0), reverse=True)[:5]

            # Montar string formatada
            interesses_formatados = "  \n".join([
                f"{interests_translation.get(entry['name'], entry['name'])} ({entry['weight'] * 100:.2f}%)" +
                ("," if idx < len(top_interests) - 1 else "")
                for idx, entry in enumerate(top_interests)
                if 'name' in entry and 'weight' in entry
            ])

            df_resultado.append({
                "influencer": nome,
                "interesses_formatados": interesses_formatados
            })

        except Exception as e:
            st.warning(f"Erro ao processar dados de {nome}: {e}")

    return pd.DataFrame(df_resultado)

def exibir_posts_comerciais_e_recentes(nome_influenciador: str, dados_influencers: dict):
    """
    Exibe os posts comerciais e recentes de um influenciador, com métricas e imagens.

    Parâmetros:
        nome_influenciador (str): nome do influenciador selecionado.
        dados_influencers (dict): dicionário com os dados JSON já carregados.
    """
    try:
        data = dados_influencers.get(nome_influenciador, {})
        perfil = data.get("user_profile", {})

        commercial_posts = perfil.get("commercial_posts", [])
        recent_posts = perfil.get("recent_posts", [])

        st.title(f"💰 Posts comerciais - {nome_influenciador}")

        # Coletar métricas
        marcas_posts = []
        likes_posts = []
        comments_posts = []
        shares_posts = []

        for post in commercial_posts:
            stat = post.get("stat", {})
            likes_posts.append(stat.get("likes", 0))
            comments_posts.append(stat.get("comments", 0))
            shares_posts.append(stat.get("shares", 0))

            sponsor = post.get("sponsor", {})
            marca = sponsor.get("usename")
            if marca:
                marcas_posts.append(marca)

        # Cálculos
        likes_total = np.mean(likes_posts) if likes_posts else 0
        comments_total = np.mean(comments_posts) if comments_posts else 0
        shares_total = np.mean(shares_posts) if shares_posts else 0
        marcas_posts = np.unique(marcas_posts)

        # Mostrar marcas
        if marcas_posts.size > 0:
            st.markdown("### Perfis no Instagram das marcas mencionadas:")
            texto_links = "\n".join([f"- [{marca}](https://www.instagram.com/{marca})" for marca in marcas_posts])
            st.markdown(texto_links)

        # Mostrar métricas
        st.markdown("### Métricas das publicações identificadas na amostra:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👍 Média de Likes", f"{int(likes_total):,}".replace(",", "."))
        with col2:
            st.metric("💬 Média de Comentários", f"{int(comments_total):,}".replace(",", "."))
        with col3:
            st.metric("🔁 Média de Shares", f"{int(shares_total):,}".replace(",", "."))

        # Exibir posts comerciais
        st.markdown("### Posts comerciais:")
        exibir_cards_de_posts(commercial_posts)

        # Exibir posts recentes
        st.title(f"⏰ Posts recentes - {nome_influenciador}")
        exibir_cards_de_posts(recent_posts)

    except Exception as e:
        st.warning(f"Erro ao buscar publicações para {nome_influenciador}: {e}")

def consolidar_resumo_influenciadores(
    dados_influencers: dict,
    perfis_e_dispersoes: dict,
    df_classes_formatado: pd.DataFrame,
    df_educacao_formatado: pd.DataFrame,
    df_top_interesses_formatado: pd.DataFrame,
    format_milhar,
    get_classes_sociais_formatadas,
    get_escolaridades_formatadas
) -> pd.DataFrame:
    """
    Consolida os dados principais de cada influenciador em um único DataFrame.

    Retorna:
        df_resultado (DataFrame): tabela pronta para exibição e exportação
    """
    lista_consolidada = []

    for nome, data in dados_influencers.items():
        try:
            perfil = data.get("user_profile", {})
            username = perfil.get("username", "N/A")
            fullname = perfil.get("fullname", "N/A")

            dispersion = int(round(perfis_e_dispersoes.get(username, 0), 0)) if username in perfis_e_dispersoes else "N/A"
            alcance = format_milhar(perfil.get("avg_reels_plays"))
            classe_social = get_classes_sociais_formatadas(df_classes_formatado, username)
            escolaridade = get_escolaridades_formatadas(df_educacao_formatado, username)

            interesses = df_top_interesses_formatado.loc[
                df_top_interesses_formatado["influencer"] == username,
                "interesses_formatados"
            ].values
            interesses = interesses[0] if len(interesses) > 0 else "N/A"

            lista_consolidada.append({
                "Influencer (Username)": username,
                "Influencer (Nome)": fullname,
                "Dispersão de interações": dispersion,
                "Alcance médio esperado por post": alcance,
                "Interesses da audiência": interesses,
                "Classe social": classe_social,
                "Escolaridade": escolaridade
            })

        except Exception as e:
            st.error(f"❌ Erro ao processar dados de {nome}: {e}")
            st.text(traceback.format_exc())

    return pd.DataFrame(lista_consolidada)
