"""
Componente Categorie — esplorazione per genere tematico.

Struttura della pagina:
1. Griglia 3 colonne di card categoria con immagine di sfondo
2. Bottone "Esplora" per ogni categoria
3. Al click: mostra gli articoli della categoria selezionata
   con card dettagliate, like/dislike e paginazione

La categoria selezionata viene salvata in
st.session_state.selected_category per persistere tra rerun.
"""
import streamlit as st
from agent.recommender import RecommenderAgent, CATEGORY_IMAGES
from feeds.source_registry import load_sources, SourceRegistry


def display_categories():
    """
    Mostra la griglia di categorie e gestisce la selezione.
    
    Per ogni categoria del SourceRegistry:
    - Mostra una card con immagine di sfondo e nome
    - Se l'utente clicca "Esplora", salva la categoria in session_state
      e chiama _show_category_articles()
    
    Le card usano CSS inline con background-image e gradient overlay
    per garantire leggibilità del testo bianco sull'immagine.
    L'hover alza la card di 4px come feedback visivo.
    """
    st.title("📂 Scegli una Categoria")
    st.caption("Seleziona un genere e scopri le notizie più in tendenza.")

    # Carica tutte le categorie dal registro fonti
    registry = SourceRegistry()
    categories = registry.get_categories()

    if not categories:
        st.error("Nessuna categoria disponibile.")
        return

    # Griglia 3 colonne con st.columns
    cols = st.columns(3)
    for i, cat in enumerate(categories):
        cat_str = str(cat)
        # Immagine Unsplash per la categoria, con fallback generico
        bg_img = CATEGORY_IMAGES.get(
            cat_str,
            "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=400&h=200&fit=crop"
        )
        with cols[i % 3]:
            # Card HTML con immagine di sfondo e gradient overlay.
            # onmouseover/onmouseout simulano un effetto hover CSS
            # (necessario perché st.markdown non supporta :hover).
            st.markdown(f"""
                <div style="
                    background-image: linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.75)), url('{bg_img}');
                    background-size: cover; background-position: center;
                    border-radius: 15px; padding: 40px 15px;
                    text-align: center; margin-bottom: 10px;
                    box-shadow: 0 4px 18px rgba(0,0,0,0.25);
                    transition: transform .25s ease;
                " onmouseover="this.style.transform='translateY(-4px)'"
                  onmouseout="this.style.transform='none'">
                    <h3 style="color:#fff; margin:0; text-shadow:2px 2px 8px rgba(0,0,0,.7); font-size:1.1em;">
                        📌 {cat_str}
                    </h3>
                </div>
            """, unsafe_allow_html=True)

            # Bottone Streamlit nativo per la selezione.
            # La key include l'indice per evitare collisioni.
            if st.button("Esplora", key=f"cat_{i}_{cat_str}", use_container_width=True):
                st.session_state.selected_category = cat_str
                st.session_state.cat_page = 0  # Reset paginazione

    # Se una categoria è selezionata, mostra i suoi articoli
    if "selected_category" in st.session_state and st.session_state.selected_category:
        _show_category_articles(st.session_state.selected_category)


def _show_category_articles(category):
    """
    Mostra gli articoli di una categoria selezionata.
    
    Renderizza:
    1. Hero banner con immagine della categoria e titolo
    2. Lista di card articoli con metadati completi
       (fonte, trend score, data, autore, riassunto)
    3. Bottoni like/dislike per ogni articolo
    4. Bottone "Carica altre notizie" per paginazione
    
    Args:
        category (str): Nome della categoria selezionata
    """
    # Hero banner con immagine di sfondo e gradient
    bg_img = CATEGORY_IMAGES.get(
        category,
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=600&h=300&fit=crop"
    )

    st.markdown(f"""
        <div style="
            background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.7)), url('{bg_img}');
            background-size: cover; background-position: center;
            border-radius: 16px; padding: 55px 20px;
            text-align: center; margin: 22px 0;
            box-shadow: 0 8px 28px rgba(0,0,0,0.3);
        ">
            <h1 style="color:#fff; text-shadow:2px 2px 12px rgba(0,0,0,.8); margin:0;">
                📰 {category}
            </h1>
        </div>
    """, unsafe_allow_html=True)

    # Crea l'agente con fonti e preferenze correnti
    sources = load_sources()
    recommender = RecommenderAgent(sources, st.session_state.user_preferences)

    # Paginazione: cat_page traccia le pagine caricate
    if "cat_page" not in st.session_state:
        st.session_state.cat_page = 0

    per_page = 10
    total_pages = st.session_state.cat_page + 1

    with st.spinner(f"Caricamento '{category}'…"):
        all_articles = recommender.get_articles_by_category(
            category, max_results=per_page * total_pages
        )

    if all_articles.empty:
        st.warning(f"Nessun articolo per '{category}'. I feed potrebbero non essere raggiungibili.")
        return

    # Renderizza ogni articolo come card HTML + bottoni Streamlit
    for _, article in all_articles.iterrows():
        pub = article.get("published", "")
        author = article.get("author", "")
        date_html = f'<span style="color:#94a3b8;">📅 {pub}</span>' if pub else ""
        author_html = f'<span style="color:#ccd6f6;">✍️ {author}</span>' if author else ""

        st.markdown(f"""
        <div style="
            background: #111827; border-radius: 16px; overflow: hidden;
            margin-bottom: 20px; border: 1px solid rgba(255,255,255,.04);
            box-shadow: 0 8px 30px rgba(0,0,0,.35);
            transition: transform .25s ease, box-shadow .25s ease;
        ">
            <img src="{article['image']}" style="width:100%; max-height:300px; object-fit:cover;"
                 onerror="this.style.display='none'">
            <div style="padding: 20px 22px 18px;">
                <h3 style="margin:0 0 6px; font-size:1.12rem; color:#e2e8f0;">
                    {article['title']}
                </h3>
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;
                            font-size:.8rem; color:#64748b;">
                    <span style="background:rgba(100,255,218,.12); color:#64ffda;
                                 padding:2px 10px; border-radius:10px; font-weight:700;">
                        {article['source']}
                    </span>
                    <span style="background:rgba(251,191,36,.12); color:#fbbf24;
                                 padding:2px 9px; border-radius:8px; font-weight:700;">
                        🔥 {article['trend_score']:.0f}
                    </span>
                    {date_html}
                    {author_html}
                </div>
                <p style="color:#94a3b8; font-size:.9rem; line-height:1.6; margin-bottom:14px;">
                    {article.get('summary', '')}
                </p>
                <a href="{article['link']}" target="_blank" style="
                    display:inline-block; background:linear-gradient(135deg,#64ffda,#00bfa5);
                    color:#0a192f !important; padding:9px 22px; border-radius:10px;
                    text-decoration:none; font-weight:700; font-size:.86rem;
                ">🔗 Leggi l'articolo completo</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Bottoni like/dislike Streamlit nativi
        c1, c2, c3 = st.columns([1, 1, 6])
        with c1:
            if st.button("👍", key=f"cat_like_{article['id']}"):
                recommender.update_preference(article["id"], "like")
                st.session_state.user_preferences = recommender.user_preferences
                st.toast("👍 Like!")
        with c2:
            if st.button("👎", key=f"cat_dislike_{article['id']}"):
                recommender.update_preference(article["id"], "dislike")
                st.session_state.user_preferences = recommender.user_preferences
                st.toast("👎 Dislike!")

    # Paginazione: bottone "Carica altre notizie"
    total_available = recommender.get_total_articles_count(category)
    loaded = len(all_articles)

    if loaded < total_available:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(
                f"⬇️ Carica altre notizie ({loaded}/{total_available})",
                use_container_width=True,
                key="cat_load_more"
            ):
                st.session_state.cat_page += 1
                st.rerun()
    else:
        st.info(f"✅ Tutti i {loaded} articoli per '{category}'.")