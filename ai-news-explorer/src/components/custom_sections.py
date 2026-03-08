"""
Componente Sezioni Personalizzate — visualizzazione articoli
delle sezioni create dall'utente con fonti scelte.
"""
import streamlit as st
from agent.recommender import RecommenderAgent, CATEGORY_IMAGES
from feeds.source_registry import load_sources


def custom_section_page():
    """
    Mostra la lista delle sezioni personalizzate e permette
    all'utente di selezionarne una per visualizzare gli articoli.
    """
    st.title("⭐ Le Mie Sezioni")
    st.caption("Le tue raccolte personalizzate di fonti preferite.")

    prefs = st.session_state.user_preferences
    sections = prefs.get("custom_sections", [])

    if not sections:
        st.info(
            "Non hai ancora creato sezioni personalizzate.\n\n"
            "Vai in **⚙️ Preferenze → ⭐ Crea Sezione Personalizzata** "
            "per crearne una scegliendo le fonti che preferisci!"
        )
        return

    # Griglia di card per le sezioni
    cols = st.columns(3)
    for i, section in enumerate(sections):
        with cols[i % 3]:
            n_sources = len(section.get("sources", []))
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1a1a2e, #16213e);
                    border-radius: 15px; padding: 30px 15px;
                    text-align: center; margin-bottom: 10px;
                    box-shadow: 0 4px 18px rgba(0,0,0,0.25);
                    border: 1px solid rgba(100,255,218,0.15);
                    transition: transform .25s ease;
                " onmouseover="this.style.transform='translateY(-4px)'"
                  onmouseout="this.style.transform='none'">
                    <h3 style="color:#64ffda; margin:0 0 8px; font-size:1.1em;">
                        ⭐ {section['name']}
                    </h3>
                    <p style="color:#94a3b8; margin:0; font-size:.85em;">
                        {n_sources} fonte{"" if n_sources == 1 else "i"} selezionate
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Esplora", key=f"cs_{i}_{section['name']}", use_container_width=True):
                st.session_state.selected_custom_section = i
                st.session_state.cs_page = 0

    # Se una sezione è selezionata, mostra i suoi articoli
    if "selected_custom_section" in st.session_state and st.session_state.selected_custom_section is not None:
        idx = st.session_state.selected_custom_section
        if 0 <= idx < len(sections):
            _show_custom_section_articles(sections[idx])


def _show_custom_section_articles(section):
    """
    Mostra gli articoli di una sezione personalizzata.
    """
    section_name = section["name"]
    source_names = section.get("sources", [])

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(100,255,218,0.15), rgba(0,191,165,0.1));
            border-radius: 16px; padding: 45px 20px;
            text-align: center; margin: 22px 0;
            box-shadow: 0 8px 28px rgba(0,0,0,0.3);
            border: 1px solid rgba(100,255,218,0.2);
        ">
            <h1 style="color:#e2e8f0; text-shadow:2px 2px 12px rgba(0,0,0,.8); margin:0;">
                ⭐ {section_name}
            </h1>
            <p style="color:#94a3b8; margin:8px 0 0; font-size:.9rem;">
                {', '.join(source_names)}
            </p>
        </div>
    """, unsafe_allow_html=True)

    sources = load_sources()
    recommender = RecommenderAgent(sources, st.session_state.user_preferences)

    if "cs_page" not in st.session_state:
        st.session_state.cs_page = 0

    per_page = 10
    total_pages = st.session_state.cs_page + 1

    with st.spinner(f"Caricamento '{section_name}'…"):
        all_articles = recommender.get_articles_by_sources(
            source_names, max_results=per_page * total_pages
        )

    if all_articles.empty:
        st.warning(
            f"Nessun articolo disponibile per la sezione '{section_name}'. "
            "I feed potrebbero non essere raggiungibili."
        )
        return

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

        c1, c2, c3 = st.columns([1, 1, 6])
        with c1:
            if st.button("👍", key=f"cs_like_{article['id']}"):
                recommender.update_preference(article["id"], "like")
                st.session_state.user_preferences = recommender.user_preferences
                st.toast("👍 Like!")
        with c2:
            if st.button("👎", key=f"cs_dislike_{article['id']}"):
                recommender.update_preference(article["id"], "dislike")
                st.session_state.user_preferences = recommender.user_preferences
                st.toast("👎 Dislike!")

    loaded = len(all_articles)
    if loaded >= per_page * total_pages:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(
                "⬇️ Carica altre notizie",
                use_container_width=True,
                key="cs_load_more"
            ):
                st.session_state.cs_page += 1
                st.rerun()
