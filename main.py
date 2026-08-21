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
from func import interests_translation, consolidar_resumo_influenciadores, exibir_posts_comerciais_e_recentes, extrair_top_interesses_formatados, calcular_distribuicao_educacao, carregar_planilhas_estaticas, calcular_distribuicao_classes_sociais, exibir_cidades_por_influencer, exibir_analise_individual, consolidar_dados_de_perfil, format_milhar, get_classes_sociais_formatadas, get_escolaridades_formatadas, calcular_dispersao_likes_comentarios

# Reset para não acumular uploads anteriores
try:
    st.session_state.influencers_dados.clear()
    st.session_state.influencers_nomes.clear()
    st.session_state.df_cidades = pd.DataFrame()
except:
    pass

# Bloco de inicialização único no início do main.py
ESTADOS_INICIAIS = {
    "influencers_nomes": [],
    "influencers_dados": {},
    "perfis_e_dispersoes": {},
    "df_classes_formatado": pd.DataFrame(),
    "df_educacao_formatado": pd.DataFrame(),
    "df_top_interesses": pd.DataFrame(),           # <- Adicionado
    "df_top_interesses_formatado": pd.DataFrame()  # <- Adicionado por precaução
}

for chave, valor_padrao in ESTADOS_INICIAIS.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor_padrao

for key, val in keys_default.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Inicialização no session_state
carregar_planilhas_estaticas()

abas = st.tabs(["Página Inicial 🏠", "Resumo 📄", "Influencer 👤", "Audiência 📊", "Publicações 📝"])

############ Página Inicial ###############
with abas[0]:
    st.title("Análise de influenciadores")
    st.markdown("### Introdução")
    st.markdown('''Este app tem a função de consolidar o processo de extração de dados de influenciadores anteriormente 
	            implementado manualmente, caso a caso. O resumo tradicionalmente disponibilizado está disponível na aba
	            Resumo, com a opção de download direto de um arquivo Excel. Separamos e adicionamos, ainda, dados e visualizações
	            relativas ao Influencer, à Audiência e às Publicações às outras abas.''')

    st.markdown("### Como utilizar")
    st.markdown('''Os arquivos de input devem ser arquivos .json extraídos
	            diretamente do IMAI. Para o processo ser bem-sucedido, os arquivos devem ser nomeados no formato
	            json_{perfil do influenciador}.json. Para já, apenas a análise dos perfis do Instagram é funcional.''')

    # Upload de múltiplos arquivos JSON
    st.markdown("### Uploader")
    uploaded_files = st.file_uploader("Carregue os arquivos JSON dos influencers", type="json", accept_multiple_files=True)

if uploaded_files:
    # Inicializa os objetos no session_state apenas uma vez
    if "influencers_dados" not in st.session_state:
        st.session_state.influencers_dados = {}
        st.session_state.influencers_nomes = []
        st.session_state.df_cidades = pd.DataFrame()

    for file in uploaded_files:
        filename = file.name
        partes = filename.split("_")

        if len(partes) > 1:
            nome = partes[1][:-5]  # remove .json
            try:
                dados = json.load(file)
                st.session_state.influencers_dados[nome] = dados
                st.session_state.influencers_nomes.append(nome)

                # Processar cidades
                try:
                    cities_entries = dados["audience_followers"]["data"]["audience_geo"]["cities"]
                    df_temp = pd.json_normalize(cities_entries)
                    df_temp["influencer"] = nome
                    st.session_state.df_cidades = pd.concat(
                        [st.session_state.df_cidades, df_temp],
                        ignore_index=True
                    )
                except Exception as e:
                    st.warning(f"Sem registro de cidades para '{nome}': {e}")

            except Exception as e:
                st.error(f"Erro ao carregar '{filename}': {e}")
        else:
            st.warning(f"O arquivo '{filename}' não segue o padrão esperado.")

    # Renomear coluna **dentro** do bloco upload_files
    if not st.session_state.df_cidades.empty:
        st.session_state.df_cidades.rename(columns={"name": "Cidade"}, inplace=True)

else:
    st.info("Por favor, carregue arquivos JSON para começar.")

############ Informações sobre o Influenciador ###############
with abas[2]:
    st.markdown("## Análise Geral 👨‍💻")
    
    if "influencers_nomes" in st.session_state and st.session_state.influencers_nomes:
        st.markdown("### Dispersão de Likes e Comments, por Influencer 🧐")
        
    influencers_dispersao = {}

    # Extração segura e robusta dos nomes
    raw_nomes = st.session_state.get("influencers_nomes", [])
    st.write(raw_nomes)

# Caso seja pandas.Series ou outro objeto estranho
    try:
    # Tenta converter para lista de strings
        influencers_nomes = list(map(str, list(raw_nomes.values)))  # caso seja Series
    except AttributeError:
    # Se não tiver .values, tenta iterar diretamente
        if isinstance(raw_nomes, list):
            influencers_nomes = [str(item) for item in raw_nomes]
        else:
            influencers_nomes = [str(raw_nomes)]
    
    for nome in influencers_nomes:
                try:
                    influencers_dispersao[nome] = calcular_dispersao_likes_comentarios(nome)
                except Exception as e:
                    st.warning(f"Erro ao calcular dispersão para {nome}: {e}")
    
    st.session_state.perfis_e_dispersoes = influencers_dispersao
        
        # Criar apresentação dos dados
    try:
    	# Transformar o dicionário em uma lista de dicionários
        dist_list = [{'Perfil': k, 'Dispersão': v} for k, v in influencers_dispersao.items()]
        
        # Criar DataFrame a partir da lista
        dist_df = pd.DataFrame(dist_list)
    
        # Exibir no Streamlit
        st.dataframe(dist_df)
    
    except Exception as e:
        st.warning(f"Ocorreu um erro ao criar o DataFrame: {e}")
        
        # ============================
        # SEÇÃO: Extração da credibilidade da audiência 👫
        # ============================
    	# st.subheader("Score da Audiência 👫")
    	# A desenvolver - precisamos identificar uma forma de calcular o Score a partir dos dados disponíveis
    
        # ============================
        # SEÇÃO: Estatísticas básicas (visualizações, engajamento, etc)
        # ============================
    st.markdown("### Dados Básicos por Influencer 📊")
    df_consolidado = consolidar_dados_de_perfil()
        
    if not df_consolidado.empty:
        st.dataframe(df_consolidado)
        
        # ============================
        # SEÇÃO: Análise Individual, por Influ 📈
        # ============================
    st.markdown("## Análise Individual, por Influenciador 🔍")
    
    # Dropdown para seleção do influenciador
    influenciador_selecionado = st.selectbox("Selecione um influenciador:", st.session_state.influencers_nomes)
        
    # Exibição dos dados
    if influenciador_selecionado:
        exibir_analise_individual(influenciador_selecionado)
    else:
        st.warning("Por favor, faça o upload dos arquivos na aba 1 antes de prosseguir.")
############ Informações sobre a audiência ###############
with abas[3]:
    st.markdown("## Dados relativos à audiência 👨‍💻")
    if "influencers_dados" in st.session_state and st.session_state.influencers_dados:
        # ============================
        # SEÇÃO: Dispersão geográfica da audiência
        # ============================
        st.markdown("### Cidades da audiência, por Influencer 🧐")
        exibir_cidades_por_influencer(st.session_state.df_cidades)
    
        # ============================
        # SEÇÃO: Classes Sociais por Influencer
        # ============================
        df_classes_formatado = calcular_distribuicao_classes_sociais(st.session_state.df_cidades, "./dados/classes_sociais_por_cidade.xlsx")
    
        if not df_classes_formatado.empty:
            st.markdown("### Distribuição de Classes Sociais 🎯")
            st.table(df_classes_formatado)
    
        st.session_state.df_classes_formatado = df_classes_formatado
        
        # ============================
        # SEÇÃO: Educação por Influencer
        # ============================
        st.subheader("Análise de Educação por Influencer 📚")
    
        df_educacao_formatado = calcular_distribuicao_educacao(
            df_cidades=st.session_state.df_cidades,
            df_dados=st.session_state.influencers_dados
        )
    
        if not df_educacao_formatado.empty:
            st.table(df_educacao_formatado)
    
        st.session_state.df_educacao_formatado = df_educacao_formatado
    	
        # ============================
        # SEÇÃO: Extração de interesses da audiência 👫
        # ============================
        st.markdown("### Interesses da Audiência 👫")
        df_top_interesses = extrair_top_interesses_formatados(
        dados_influencers=st.session_state.influencers_dados,
        interests_translation=interests_translation
        )
    
        st.session_state.df_top_interesses = df_top_interesses

    else:
        st.warning("Por favor, faça o upload dos arquivos na aba 1 antes de prosseguir.")

############ Publicações feitas pelo influenciador ###############
with abas[4]:
    if "influencers_dados" in st.session_state and st.session_state.influencers_dados:
        st.subheader("Selecione um influenciador para ver os posts 📸")
    
        influenciador_selecionado = st.selectbox(
            "Influenciador:", 
            st.session_state.influencers_nomes, 
            key="select_influencer_posts"
        )
    
        if influenciador_selecionado:
            exibir_posts_comerciais_e_recentes(
                nome_influenciador=influenciador_selecionado,
                dados_influencers=st.session_state.influencers_dados
            )
    else:
        st.warning("Por favor, faça o upload dos arquivos na aba 1 antes de prosseguir.")

############ Resumo dos Influenciadores ###############
with abas[1]:
    if "influencers_dados" not in st.session_state:
        st.warning("⚠️ Nenhum arquivo foi carregado. Volte para a aba 1 e envie os arquivos JSON.")
        st.stop()  # evita execução do restante
    
    df_resumo = consolidar_resumo_influenciadores(
    dados_influencers=st.session_state.influencers_dados,
    perfis_e_dispersoes=st.session_state.perfis_e_dispersoes,
    df_classes_formatado=st.session_state.df_classes_formatado,
    df_educacao_formatado=st.session_state.df_educacao_formatado,
    df_top_interesses_formatado=st.session_state.get("df_top_interesses", pd.DataFrame()),,
    format_milhar=format_milhar,
    get_classes_sociais_formatadas=get_classes_sociais_formatadas,
    get_escolaridades_formatadas=get_escolaridades_formatadas
    )


    if not df_resumo.empty:
        st.title("Consolidação de Influenciadores")
        st.table(df_resumo)

        file_name = "resumo_defesa_influenciadores.xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_resumo.to_excel(writer, index=False, sheet_name='Defesa Influenciadores')
        output.seek(0)

        st.download_button(
            label="📥 Baixar tabela de resumo como Excel",
            data=output,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
