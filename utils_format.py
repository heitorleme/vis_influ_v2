# utils_format.py
import streamlit as st
from scipy.stats import norm
import pandas as pd
import numpy as np

def exibir_cartao(titulo, valor):
    st.markdown(f"""
    <div style="
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1a1c24;
        text-align: center;
        color: #ffffff;
    ">
        <h4 style="margin-bottom: 0.5rem;">{titulo}</h4>
        <p style="margin: 0; font-size: 0.9rem;">{valor}</p>
    </div>
    """, unsafe_allow_html=True)

def exibir_cartao_riscos(titulo, score, riscos):
    if riscos:
        risks_html = "<ul style='margin: 0; padding-left: 1rem; font-size: 0.8rem;'>"
        for risk in riscos:
            risks_html += f"<li>{risk}</li>"
        risks_html += "</ul>"
    else:
        risks_html = "<p style='margin: 0; font-size: 0.8rem;'>Sem riscos identificados</p>"

    st.markdown(f"""
    <div style="
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1a1c24;
        text-align: center;
        color: #ffffff;
    ">
        <h4 style="margin-bottom: 0.5rem;">{titulo}</h4>
        <p style="margin: 0; font-size: 1.2rem; font-weight: bold;">{score:.1f}</p>
        <div style="margin-top: 0.5rem;">{risks_html}</div>
    </div>
    """, unsafe_allow_html=True)

def formatar_tabela_classes_sociais(df_result):
    """
    Formata DataFrame com colunas de classes sociais em uma string multiline por linha.

    Retorna:
        pd.DataFrame: Com coluna 'influencer' e 'classes_sociais_formatadas'
    """
    return pd.DataFrame([
        {
            "influencer": idx,
            "classes_sociais_formatadas": "  \n".join([
                f"Classes D e E: {row['normalized_classe_de']:.2f}%",
                f"Classe C: {row['normalized_classe_c']:.2f}%",
                f"Classe B: {row['normalized_classe_b']:.2f}%",
                f"Classe A: {row['normalized_classe_a']:.2f}%"
            ])
        }
        for idx, row in df_result.iterrows()
    ])

def formatar_tabela_distribuicao_educacao(total_anos_por_influencer, std_dev=3):
    """
    Recebe uma Series com a soma total de anos de escolaridade (feminino + masculino) por influencer,
    e retorna uma tabela formatada com faixas educacionais estimadas com base em uma distribuição normal.
    """
    dist_list = []

    for influencer, mean in total_anos_por_influencer.items():
        prob_less_5 = norm.cdf(5, mean, std_dev) * 100
        prob_5_9 = (norm.cdf(9, mean, std_dev) - norm.cdf(5, mean, std_dev)) * 100
        prob_9_12 = (norm.cdf(12, mean, std_dev) - norm.cdf(9, mean, std_dev)) * 100
        prob_more_12 = (1 - norm.cdf(12, mean, std_dev)) * 100

        dist_list.append({
            "influencer": influencer,
            "educacao_formatada": "  \n".join([
                f"< 5 anos: {prob_less_5:.2f}%",
                f"5–9 anos: {prob_5_9:.2f}%",
                f"9–12 anos: {prob_9_12:.2f}%",
                f"12+ anos: {prob_more_12:.2f}%"
            ])
        })

    return pd.DataFrame(dist_list)

def exibir_cards_de_posts(lista_posts):
    """
    Exibe uma lista de posts em layout de 3 colunas com imagem, texto e métricas.
    """
    for row_start in range(0, len(lista_posts), 3):
        cols = st.columns(3)
        for i in range(3):
            if row_start + i >= len(lista_posts):
                break
            post = lista_posts[row_start + i]
            link = post.get("link", "#")
            with cols[i]:
                img_url = post.get("thumbnail") or post.get("user_picture")
                if img_url:
                    st.markdown(
                        f'<a href="{link}" target="_blank"><img src="{img_url}" style="width:100%; border-radius:10px;" /></a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.warning("Imagem não disponível para este post.")

                st.markdown(f"**{post.get('text', '')}**")

                stat = post.get("stat", {})
                st.markdown(f"👍 Likes: **{stat.get('likes', 0)}**")
                st.markdown(f"💬 Comentários: **{stat.get('comments', 0)}**")
                st.markdown(f"🔁 Compartilhamentos: **{stat.get('shares', 0)}**")
