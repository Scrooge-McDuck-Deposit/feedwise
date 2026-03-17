"""
Componente Sezioni Personalizzate — visualizzazione articoli
delle sezioni create dall'utente con fonti scelte.
"""
import streamlit as st
import hashlib
import pandas as pd
from agent.recommender import RecommenderAgent, CATEGORY_IMAGES, _parse_feed_cached
from feeds.source_registry import load_sources
from components.home import _render_card


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
    rss_feeds = section.get("rss_feeds", [])

    # Descrizione sottotitolo
    sub_parts = []
    if source_names:
        sub_parts.append(", ".join(source_names))
    if rss_feeds:
        sub_parts.append(f"{len(rss_feeds)} feed RSS manuali")
    sub_text = " · ".join(sub_parts) if sub_parts else ""

    hero_html = (
        '<div style="'
        'background: linear-gradient(135deg, rgba(100,255,218,0.15), rgba(0,191,165,0.1));'
        ' border-radius:16px; padding:45px 20px;'
        ' text-align:center; margin:22px 0;'
        ' box-shadow:0 8px 28px rgba(0,0,0,0.3);'
        ' border:1px solid rgba(100,255,218,0.2);">'
        f'<h1 style="color:#e2e8f0; text-shadow:2px 2px 12px rgba(0,0,0,.8); margin:0;">'
        f'⭐ {section_name}</h1>'
        f'<p style="color:#94a3b8; margin:8px 0 0; font-size:.9rem;">{sub_text}</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

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

        # Fetch articoli dai feed RSS manuali
        if rss_feeds:
            rss_articles = []
            for rss_url in rss_feeds:
                try:
                    entries = _parse_feed_cached(rss_url)
                    for entry in entries[:8]:
                        article_id = hashlib.md5(
                            (entry.get("link", "") + entry.get("title", "")).encode()
                        ).hexdigest()
                        image = recommender._extract_image_from_entry(entry)
                        summary = RecommenderAgent._summarize_text(
                            entry.get("summary", ""), entry.get("title", ""), max_words=300
                        )
                        rss_articles.append({
                            "id": article_id,
                            "title": entry.get("title", "Senza titolo"),
                            "link": entry.get("link", "#"),
                            "source": rss_url.split("/")[2] if "/" in rss_url else "RSS",
                            "category": section_name,
                            "image": image or "",
                            "summary": summary,
                            "published": recommender._format_date(entry.get("published", "")),
                            "author": recommender._extract_author(entry),
                            "paid": False,
                            "trend_score": recommender.calculate_trend_score(entry),
                        })
                except Exception:
                    pass
            if rss_articles:
                rss_df = pd.DataFrame(rss_articles)
                if all_articles.empty:
                    all_articles = rss_df
                else:
                    all_articles = pd.concat([all_articles, rss_df], ignore_index=True)

    if all_articles.empty:
        st.warning(
            f"Nessun articolo disponibile per la sezione '{section_name}'. "
            "I feed potrebbero non essere raggiungibili."
        )
        return

    for _, article in all_articles.iterrows():
        _render_card(article, "cs", recommender)
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
