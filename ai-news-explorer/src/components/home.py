"""
Componente Home — pagina principale dell'aggregatore.

Struttura della pagina:
1. Header con titolo e sottotitolo
2. Barra di ricerca (filtra articoli per query testuale)
3. Trending strip   (5-6 notizie top in card orizzontali scrollabili)
4. Feed articoli    (card verticali con paginazione "load more")

Ogni card mostra: titolo, fonte, categoria, trend score, data,
autore, immagine, riassunto e link all'articolo originale.
L'utente può dare like/dislike per influenzare l'algoritmo.
"""
import streamlit as st
import hashlib
import random
from agent.recommender import RecommenderAgent, CATEGORY_IMAGES
from feeds.source_registry import load_sources
from components.world_map import render_world_map_section


# ── Lingue disponibili per traduzione sintetica ──────────────────────
AVAILABLE_LANGUAGES = {
    "🇮🇹 Italiano (originale)": "",
    "🇬🇧 English": "en",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇪🇸 Español": "es",
    "🇵🇹 Português": "pt",
    "🇯🇵 日本語": "ja",
    "🇨🇳 中文": "zh",
}

_LANG_TEMPLATES = {
    "en": {
        "intro": ["This article discusses", "This report covers", "An in-depth look at"],
        "source": "Published by",
        "category": "Category",
        "closing": [
            "Read the full article for more details.",
            "This topic is generating significant attention.",
            "Stay updated on this developing story.",
        ],
    },
    "fr": {
        "intro": ["Cet article traite de", "Ce rapport couvre", "Un regard approfondi sur"],
        "source": "Publié par",
        "category": "Catégorie",
        "closing": [
            "Lisez l'article complet pour plus de détails.",
            "Ce sujet génère une attention considérable.",
            "Restez informé sur cette histoire en développement.",
        ],
    },
    "de": {
        "intro": ["Dieser Artikel behandelt", "Dieser Bericht befasst sich mit", "Ein detaillierter Blick auf"],
        "source": "Veröffentlicht von",
        "category": "Kategorie",
        "closing": [
            "Lesen Sie den vollständigen Artikel für weitere Details.",
            "Dieses Thema erregt erhebliche Aufmerksamkeit.",
            "Bleiben Sie über diese Entwicklung informiert.",
        ],
    },
    "es": {
        "intro": ["Este artículo trata sobre", "Este informe cubre", "Una mirada en profundidad a"],
        "source": "Publicado por",
        "category": "Categoría",
        "closing": [
            "Lea el artículo completo para más detalles.",
            "Este tema está generando una atención significativa.",
            "Manténgase informado sobre esta historia en desarrollo.",
        ],
    },
    "pt": {
        "intro": ["Este artigo discute", "Este relatório cobre", "Um olhar aprofundado sobre"],
        "source": "Publicado por",
        "category": "Categoria",
        "closing": [
            "Leia o artigo completo para mais detalhes.",
            "Este tema está gerando atenção significativa.",
            "Fique atualizado sobre esta história em desenvolvimento.",
        ],
    },
    "ja": {
        "intro": ["この記事は次について論じています", "このレポートは次をカバーしています", "詳細な分析"],
        "source": "発行元",
        "category": "カテゴリ",
        "closing": [
            "詳細については記事全文をお読みください。",
            "このトピックは大きな注目を集めています。",
            "この展開中のニュースの最新情報をお見逃しなく。",
        ],
    },
    "zh": {
        "intro": ["本文讨论了", "本报告涵盖了", "深入分析"],
        "source": "发布者",
        "category": "类别",
        "closing": [
            "阅读全文了解更多详情。",
            "该话题正在引起广泛关注。",
            "请持续关注这一发展中的事件。",
        ],
    },
}


def _generate_translation(title, summary, source, category, lang_code):
    """Genera una traduzione sintetica dell'articolo nella lingua target."""
    if not lang_code or lang_code not in _LANG_TEMPLATES:
        return ""
    tmpl = _LANG_TEMPLATES[lang_code]
    h = int(hashlib.md5((title + lang_code).encode()).hexdigest()[:8], 16)
    rng = random.Random(h)
    intro = rng.choice(tmpl["intro"])
    closing = rng.choice(tmpl["closing"])
    title_brief = title[:100]
    return (
        f'{intro}: "{title_brief}". '
        f'{tmpl["source"]}: {source} · {tmpl["category"]}: {category}. '
        f'{closing}'
    )


def _translate_title(title, lang_code):
    """Genera una traduzione sintetica del titolo nella lingua target."""
    if not lang_code or lang_code not in _LANG_TEMPLATES:
        return ""
    tmpl = _LANG_TEMPLATES[lang_code]
    h = int(hashlib.md5((title + lang_code + "title").encode()).hexdigest()[:8], 16)
    rng = random.Random(h)
    intro = rng.choice(tmpl["intro"])
    return f'{intro}: "{title[:120]}"'


# ── CSS globale ──────────────────────────────────────────────────────
# Variabili CSS custom (--var) per coerenza cromatica.
# Il tema è dark con accent teal (#64ffda) ispirato a Brittany Chiang.
# Importato una sola volta all'inizio della pagina con unsafe_allow_html.
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Variabili colore (dark theme) ────────────────── */
:root {
    --bg-page: #0a0f1a;
    --bg-card: #111827;
    --bg-card-hover: #1a2332;
    --bg-glass: rgba(17,24,39,.72);
    --accent: #64ffda;
    --accent-dim: rgba(100,255,218,.10);
    --accent-glow: rgba(100,255,218,.18);
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --gold: #fbbf24;
    --radius: 18px;
    --radius-sm: 12px;
    --shadow: 0 8px 32px rgba(0,0,0,.4);
    --shadow-lg: 0 16px 48px rgba(0,0,0,.55);
    --border: rgba(255,255,255,.06);
    --transition: .3s cubic-bezier(.4,0,.2,1);
}

/* ── Base ─────────────────────────────────────────── */
body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background: var(--bg-page) !important;
    color: var(--text-primary) !important;
}
.stApp > header { background: transparent !important; }

/* ── Scrollbar globale ────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(100,255,218,.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100,255,218,.4); }

/* ── Card articolo ────────────────────────────────── */
.news-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 22px;
    box-shadow: var(--shadow);
    transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition);
}
.news-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent-glow);
}
.news-card-img {
    width: 100%;
    max-height: 280px;
    object-fit: cover;
    display: block;
}
.news-card-body {
    padding: 22px 24px 20px;
}
.news-card-body h3 {
    margin: 0 0 8px;
    font-size: 1.12rem;
    font-weight: 600;
    line-height: 1.5;
    color: var(--text-primary);
    letter-spacing: -.01em;
}

/* ── Riga metadati ────────────────────────────────── */
.news-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: .78rem;
    color: var(--text-muted);
}

.badge-source {
    background: var(--accent-dim);
    color: var(--accent);
    padding: 3px 11px;
    border-radius: 20px;
    font-weight: 600;
    font-size: .76rem;
    letter-spacing: .02em;
    border: 1px solid rgba(100,255,218,.12);
}

.badge-paid {
    background: linear-gradient(135deg,#f59e0b,#ef4444);
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: .72rem;
    font-weight: 700;
}

.badge-trend {
    background: rgba(251,191,36,.10);
    color: var(--gold);
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 700;
    font-size: .76rem;
    border: 1px solid rgba(251,191,36,.12);
}

.news-card-summary {
    color: var(--text-secondary);
    font-size: .88rem;
    line-height: 1.7;
    margin-bottom: 14px;
}

/* ── Bottone "Leggi l'articolo" ───────────────────── */
.btn-read {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent), #00bfa5);
    color: #0a192f !important;
    padding: 10px 24px;
    border-radius: var(--radius-sm);
    text-decoration: none;
    font-weight: 700;
    font-size: .84rem;
    letter-spacing: .02em;
    transition: transform var(--transition), box-shadow var(--transition);
    box-shadow: 0 2px 12px rgba(100,255,218,.15);
}
.btn-read:hover {
    transform: translateY(-1px) scale(1.03);
    box-shadow: 0 6px 24px rgba(100,255,218,.3);
}

/* ── Trending strip ───────────────────────────────── */
.trending-row {
    display: flex;
    gap: 18px;
    overflow-x: auto;
    padding-bottom: 10px;
    margin-bottom: 12px;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
}
.trending-row::-webkit-scrollbar { height: 5px; }
.trending-row::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }

.trend-hero {
    flex: 0 0 330px;
    height: 220px;
    position: relative;
    border-radius: var(--radius);
    overflow: hidden;
    cursor: pointer;
    scroll-snap-align: start;
    box-shadow: var(--shadow);
    transition: transform var(--transition), box-shadow var(--transition);
    text-decoration: none !important;
    border: 1px solid var(--border);
}
.trend-hero:hover {
    transform: scale(1.03);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent-glow);
}
.trend-hero img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
}

.trend-hero .grad {
    position: absolute;
    inset: 0;
    background: linear-gradient(0deg, rgba(0,0,0,.85) 0%, rgba(0,0,0,.10) 60%);
}

.trend-hero .caption {
    position: absolute;
    bottom: 0;
    left: 0; right: 0;
    padding: 18px 20px;
}
.trend-hero .caption h4 {
    margin: 0 0 8px;
    color: #fff;
    font-size: .95rem;
    font-weight: 600;
    line-height: 1.4;
    text-shadow: 0 2px 8px rgba(0,0,0,.7);
}
.trend-hero .caption .info {
    display: flex;
    gap: 10px;
    align-items: center;
}
.trend-hero .caption .info span {
    font-size: .74rem;
    font-weight: 600;
}
.trend-hero .caption .info .src { color: var(--accent); }
.trend-hero .caption .info .score {
    background: rgba(255,255,255,.12);
    backdrop-filter: blur(6px);
    color: var(--gold);
    padding: 2px 9px;
    border-radius: 8px;
    font-size: .72rem;
}

/* ── Section headers ──────────────────────────────── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 36px 0 20px;
}
.sec-head h2 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -.02em;
}
.sec-head .bar {
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), rgba(100,255,218,.08));
    border-radius: 2px;
}

/* ── Search input ─────────────────────────────────── */
.stTextInput > div > div > input {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid rgba(100,255,218,.15) !important;
    background: rgba(17,24,39,.6) !important;
    padding: 14px 20px !important;
    font-size: 1rem !important;
    color: var(--text-primary) !important;
    transition: all var(--transition) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(100,255,218,.08) !important;
    background: rgba(17,24,39,.8) !important;
}

/* ── Card container (st.container border=True) ────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow) !important;
    padding: 0 !important;
    overflow: hidden !important;
    margin-bottom: 20px !important;
    transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: var(--shadow-lg) !important;
    border-color: var(--accent-glow) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: transparent !important;
    gap: 0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div > div {
    background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    padding: 6px 20px 16px !important;
    background: transparent !important;
}

/* ── Bottoni Streamlit (like/dislike/AI) ──────────── */
[data-testid="stVerticalBlockBorderWrapper"] button {
    border-radius: var(--radius-sm) !important;
    border: 1px solid rgba(255,255,255,.08) !important;
    background: rgba(255,255,255,.04) !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] button:hover {
    background: var(--accent-dim) !important;
    border-color: var(--accent-glow) !important;
    color: var(--accent) !important;
}

/* ── Sidebar ──────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(10,15,26,.95) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    transition: color var(--transition) !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--accent) !important;
}

/* ── Bottone "Carica altre notizie" ───────────────── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all var(--transition) !important;
}

/* ── Toast e messaggi ─────────────────────────────── */
[data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--accent-glow) !important;
    border-radius: var(--radius-sm) !important;
}
</style>
"""


def home_page():
    """
    Renderizza la pagina Home dell'aggregatore.
    
    Flusso:
    1. Inietta il CSS globale (dark theme con card, trending, ecc.)
    2. Crea il RecommenderAgent con le fonti e le preferenze utente
    3. Se l'utente ha digitato una query → mostra risultati di ricerca
    4. Altrimenti → mostra trending strip + feed articoli paginato
    
    La paginazione usa st.session_state per tenere traccia della "pagina"
    corrente. Ogni click su "Carica altre notizie" incrementa il contatore
    e forza un rerun con st.rerun().
    """
    st.title("🌐 AI News Trend Explorer")
    st.caption("Il tuo aggregatore intelligente di notizie · powered by AI")

    # Inizializza l'agente con tutte le fonti e le preferenze correnti
    sources = load_sources()
    recommender = RecommenderAgent(sources, st.session_state.user_preferences)

    # ── Barra di ricerca ──────────────────────────────
    # st.text_input con placeholder. Se l'utente preme Invio,
    # Streamlit esegue un rerun e query conterrà il testo.
    query = st.text_input(
        "🔍 Cerca un argomento:",
        placeholder="es. Intelligenza Artificiale, Champions League, Politica…"
    )

    # ── Modalità ricerca ──────────────────────────────
    if query and query.strip():
        st.markdown("---")
        st.markdown(
            f'<div class="sec-head"><h2>🔎 Risultati per "{query}"</h2>'
            f'<div class="bar"></div></div>',
            unsafe_allow_html=True
        )

        # Paginazione ricerca: incrementa search_page per caricare più risultati
        if "search_page" not in st.session_state:
            st.session_state.search_page = 0
        per_page = 10
        total = per_page * (st.session_state.search_page + 1)

        with st.spinner("Ricerca in corso…"):
            results = recommender.get_recommendations(query=query, max_results=total)

        if results.empty:
            st.warning("Nessun risultato. Prova un altro termine.")
        else:
            # Renderizza ogni articolo come card
            for _, art in results.iterrows():
                _render_card(art, "search", recommender)

            # Bottone "Carica altri" centrato
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button("⬇️ Carica altri risultati",
                             key="search_more", use_container_width=True):
                    st.session_state.search_page += 1
                    st.rerun()
        return  # Esci: non mostrare trending + feed quando si cerca

    # ── Trending strip ────────────────────────────────
    # Le 6 notizie con trend score più alto, mostrate come
    # hero cards orizzontali scrollabili (simili a Netflix).
    st.markdown(
        '<div class="sec-head"><h2>🔥 Notizie di Tendenza</h2>'
        '<div class="bar"></div></div>',
        unsafe_allow_html=True
    )

    with st.spinner("Caricamento trending…"):
        trending = recommender.get_recommendations(query="", max_results=6)

    if trending.empty:
        st.warning("Nessuna notizia disponibile al momento.")
        return

    _render_trending_strip(trending)

    # ── Mappa del mondo con trending topics ────────────
    render_world_map_section()

    # ── Feed articoli con paginazione ─────────────────
    st.markdown(
        '<div class="sec-head"><h2>📰 Articoli in Evidenza</h2>'
        '<div class="bar"></div></div>',
        unsafe_allow_html=True
    )

    # home_page_num traccia quante "pagine" l'utente ha caricato.
    # total = per_page * (pagina_corrente + 1)
    if "home_page_num" not in st.session_state:
        st.session_state.home_page_num = 0
    per_page = 10
    total = per_page * (st.session_state.home_page_num + 1)

    with st.spinner("Caricamento articoli…"):
        articles = recommender.get_recommendations(query="", max_results=total)

    if not articles.empty:
        for _, art in articles.iterrows():
            _render_card(art, "home", recommender)

        # Mostra "Carica altre" solo se ci sono ancora articoli disponibili
        available = recommender.get_total_articles_count()
        loaded = len(articles)
        if loaded < available:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button(
                    f"⬇️ Carica altre notizie ({loaded}/{available})",
                    key="home_load_more",
                    use_container_width=True
                ):
                    st.session_state.home_page_num += 1
                    st.rerun()
        else:
            st.info(f"✅ Hai visto tutti i {loaded} articoli.")


def _render_trending_strip(df):
    """
    Renderizza la strip orizzontale di trending news.
    
    Ogni card è un tag <a> nativo che apre il link dell'articolo
    in una nuova tab al click. L'immagine ha un gradient overlay
    scuro per garantire la leggibilità del titolo bianco.
    
    Se l'immagine non si carica (onerror), viene nascosta e il
    colore di sfondo della card (gradient) rimane visibile.
    
    Args:
        df (DataFrame): Articoli trending con colonne title, link,
                        source, image, trend_score
    """
    # Palette colori per le card (ciclica)
    colors = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#8b5cf6", "#ef4444"]

    cards_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        color = colors[i % len(colors)]
        img = row.get("image", "")
        title = row["title"][:85] + ("…" if len(row["title"]) > 85 else "")
        title_safe = title.replace('"', '&quot;')  # Escape per attributo HTML title

        # Tag <img> con onerror per nascondersi se il caricamento fallisce
        img_tag = (
            f'<img src="{img}" onerror="this.style.display=\'none\'">'
            if img else ""
        )

        cards_html += f"""
        <a class="trend-hero" href="{row['link']}" target="_blank"
           style="background:{color};" title="{title_safe}">
            {img_tag}
            <div class="grad"></div>
            <div class="caption">
                <h4>{title}</h4>
                <div class="info">
                    <span class="src">📰 {row['source']}</span>
                    <span class="score">🔥 {row['trend_score']:.0f}</span>
                </div>
            </div>
        </a>"""

    # Wrappa tutte le card in un container flex scrollabile
    st.markdown(f'<div class="trending-row">{cards_html}</div>', unsafe_allow_html=True)


def _render_card(article, prefix, recommender=None):
    """
    Renderizza una card articolo con metadati, immagine e bottoni interazione.
    
    La card ha due parti:
    1. HTML (st.markdown unsafe_allow_html) — immagine, titolo, metadati,
       riassunto e link "Leggi l'articolo"
    2. Widget Streamlit (st.button) — bottoni like/dislike che aggiornano
       le preferenze dell'utente e forzano un rerun
    
    Args:
        article (Series/dict): Dati dell'articolo con campi title, link,
            source, category, image, summary, published, author, trend_score, paid
        prefix (str): Prefisso per le key dei bottoni (evita collisioni
            tra card di pagine diverse, es. "home", "search", "cat")
        recommender (RecommenderAgent, optional): Se fornito, i bottoni
            like/dislike aggiornano le preferenze tramite l'agente
    """
    # Badge "Premium" per fonti a pagamento
    paid = '<span class="badge-paid">💳 Premium</span>' if article.get("paid") else ""

    # Metadati opzionali: mostrati solo se disponibili nel feed
    pub = article.get("published", "")
    author = article.get("author", "")
    date_html = f'<span>📅 {pub}</span>' if pub else ""
    author_html = f'<span>✍️ {author}</span>' if author else ""

    # Traduzione titolo (se lingua selezionata)
    title_display = article["title"]
    translated_title_html = ""
    lang_label = st.session_state.get("translation_lang", "🇮🇹 Italiano (originale)")
    lang_code = AVAILABLE_LANGUAGES.get(lang_label, "")
    if lang_code:
        translated_title = _translate_title(article["title"], lang_code)
        if translated_title:
            translated_title_html = (
                f'<p style="color:#38bdf8; font-size:0.85rem; margin:2px 0 6px; font-style:italic;">'
                f'🌐 {translated_title}</p>'
            )

    # Card HTML — costruita senza indentazione per evitare blocchi codice Markdown
    with st.container(border=True):
        card_html = (
            f'<img class="news-card-img" src="{article["image"]}"'
            ' onerror="this.style.display=\'none\'"'
            ' style="display:block;">'
            '<div class="news-card-body">'
            f'<h3>{title_display} {paid}</h3>'
            f'{translated_title_html}'
            '<div class="news-meta">'
            f'<span class="badge-source">{article["source"]}</span>'
            f'<span>📂 {article["category"]}</span>'
            f'<span class="badge-trend">🔥 {article["trend_score"]:.0f}</span>'
            f'{date_html}{author_html}'
            '</div>'
            f'<a class="btn-read" href="{article["link"]}" target="_blank">'
            '🔗 Leggi l\'articolo completo</a>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # Bottoni inside card container
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("👍", key=f"{prefix}_l_{article['id']}"):
                if recommender:
                    recommender.update_preference(article["id"], "like")
                    st.session_state.user_preferences = recommender.user_preferences
                st.toast("👍 Ti piace!")
        with c2:
            if st.button("👎", key=f"{prefix}_d_{article['id']}"):
                if recommender:
                    recommender.update_preference(article["id"], "dislike")
                    st.session_state.user_preferences = recommender.user_preferences
                st.toast("👎 Non ti piace!")
        with c3:
            show_key = f"show_{prefix}_ai_{article['id']}"
            if st.button("🤖 Riassunto AI", key=f"btn_{prefix}_ai_{article['id']}"):
                st.session_state[show_key] = not st.session_state.get(show_key, False)
                st.rerun()

        # Mostra riassunto AI on-demand
        show_key = f"show_{prefix}_ai_{article['id']}"
        if st.session_state.get(show_key, False):
            summary_text = article.get("summary", "")
            if summary_text:
                st.markdown(
                    f'<div style="background:rgba(100,255,218,0.05); border-left:3px solid #64ffda;'
                    f' border-radius:0 12px 12px 0; padding:12px 16px; margin:0 0 8px;">'
                    f'<span style="font-size:0.72rem; font-weight:700; color:#64ffda;'
                    f' text-transform:uppercase; letter-spacing:1px;">🤖 Riassunto AI</span>'
                    f'<p style="color:#94a3b8; font-size:0.88rem; line-height:1.6; margin:6px 0 0;">'
                    f'{summary_text}</p></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("Nessun riassunto disponibile per questo articolo.")