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
import streamlit.components.v1 as stc
from agent.recommender import RecommenderAgent, CATEGORY_IMAGES
from feeds.source_registry import load_sources


# ── CSS globale ──────────────────────────────────────────────────────
# Variabili CSS custom (--var) per coerenza cromatica.
# Il tema è dark con accent teal (#64ffda) ispirato a Brittany Chiang.
# Importato una sola volta all'inizio della pagina con unsafe_allow_html.
GLOBAL_CSS = """
<style>
/* ── Variabili colore (dark theme) ────────────────── */
:root {
    --bg-card: #111827;            /* sfondo card articoli */
    --bg-card-hover: #1e293b;      /* sfondo card al hover */
    --accent: #64ffda;             /* colore primario teal */
    --accent-dim: rgba(100,255,218,.12);  /* accent con opacità per sfondi */
    --text-primary: #e2e8f0;       /* testo principale (quasi bianco) */
    --text-secondary: #94a3b8;     /* testo secondario (grigio medio) */
    --text-muted: #64748b;         /* testo disattivato (grigio scuro) */
    --gold: #fbbf24;               /* colore per trend score */
    --radius: 16px;                /* border-radius standard */
    --shadow: 0 8px 30px rgba(0,0,0,.35);  /* ombra card */
}

/* ── Card articolo ────────────────────────────────── */
/* Layout verticale: immagine in alto, corpo sotto.
   L'hover alza la card di 5px e intensifica l'ombra
   per dare feedback visivo tattile. */
.news-card {
    background: var(--bg-card);
    border: 1px solid rgba(255,255,255,.04);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 22px;
    box-shadow: var(--shadow);
    transition: transform .25s ease, box-shadow .25s ease;
}
.news-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 44px rgba(0,0,0,.5);
    border-color: rgba(100,255,218,.15);
}
.news-card-img {
    width: 100%;
    max-height: 300px;
    object-fit: cover;      /* Ritaglia l'immagine per riempire lo spazio */
    display: block;
}
.news-card-body {
    padding: 20px 22px 18px;
}
.news-card-body h3 {
    margin: 0 0 6px;
    font-size: 1.12rem;
    line-height: 1.45;
    color: var(--text-primary);
}

/* ── Riga metadati (fonte, categoria, data, autore) ─ */
.news-meta {
    display: flex;
    flex-wrap: wrap;         /* Su mobile i badge vanno a capo */
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-size: .8rem;
    color: var(--text-muted);
}

/* Badge fonte: sfondo teal semitrasparente con testo teal */
.badge-source {
    background: var(--accent-dim);
    color: var(--accent);
    padding: 2px 10px;
    border-radius: 10px;
    font-weight: 700;
    font-size: .78rem;
}

/* Badge fonte a pagamento: gradiente arancio→rosso */
.badge-paid {
    background: linear-gradient(135deg,#f59e0b,#ef4444);
    color: #fff;
    padding: 2px 9px;
    border-radius: 8px;
    font-size: .72rem;
    font-weight: 700;
}

/* Badge trend score: sfondo gold semitrasparente */
.badge-trend {
    background: rgba(251,191,36,.12);
    color: var(--gold);
    padding: 2px 9px;
    border-radius: 8px;
    font-weight: 700;
    font-size: .78rem;
}

/* Riassunto articolo */
.news-card-summary {
    color: var(--text-secondary);
    font-size: .9rem;
    line-height: 1.6;
    margin-bottom: 14px;
}

/* Bottone "Leggi l'articolo completo" con gradiente teal */
.btn-read {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent), #00bfa5);
    color: #0a192f !important;
    padding: 9px 22px;
    border-radius: 10px;
    text-decoration: none;
    font-weight: 700;
    font-size: .86rem;
    transition: transform .2s, box-shadow .2s;
}
.btn-read:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 22px rgba(100,255,218,.35);
}

/* ── Trending strip (hero cards orizzontali) ──────── */
/* Container con scroll orizzontale e snap per tocco su mobile.
   Ogni card ha altezza fissa 210px con immagine di sfondo
   e gradient overlay per leggibilità del testo. */
.trending-row {
    display: flex;
    gap: 16px;
    overflow-x: auto;            /* Scroll orizzontale */
    padding-bottom: 8px;
    margin-bottom: 10px;
    scroll-snap-type: x mandatory;  /* Snap al bordo delle card */
    -webkit-overflow-scrolling: touch;  /* Scroll fluido iOS */
}
.trending-row::-webkit-scrollbar { height: 6px; }
.trending-row::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }

/* Singola card trending */
.trend-hero {
    flex: 0 0 320px;            /* Larghezza fissa, non si comprime */
    height: 210px;
    position: relative;
    border-radius: var(--radius);
    overflow: hidden;
    cursor: pointer;
    scroll-snap-align: start;
    box-shadow: var(--shadow);
    transition: transform .3s ease;
    text-decoration: none !important;
}
.trend-hero:hover { transform: scale(1.03); }
.trend-hero img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
}

/* Gradient overlay: da trasparente in alto a nero in basso */
.trend-hero .grad {
    position: absolute;
    inset: 0;
    background: linear-gradient(0deg, rgba(0,0,0,.82) 0%, rgba(0,0,0,.15) 55%);
}

/* Caption sovrapposta all'immagine */
.trend-hero .caption {
    position: absolute;
    bottom: 0;
    left: 0; right: 0;
    padding: 16px 18px;
}
.trend-hero .caption h4 {
    margin: 0 0 6px;
    color: #fff;
    font-size: .98rem;
    line-height: 1.35;
    text-shadow: 0 2px 6px rgba(0,0,0,.6);
}
.trend-hero .caption .info {
    display: flex;
    gap: 10px;
    align-items: center;
}
.trend-hero .caption .info span {
    font-size: .75rem;
    font-weight: 600;
}
.trend-hero .caption .info .src { color: var(--accent); }
.trend-hero .caption .info .score {
    background: rgba(255,255,255,.15);
    color: var(--gold);
    padding: 1px 8px;
    border-radius: 6px;
}

/* ── Section headers (titolo + linea gradiente) ───── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 32px 0 18px;
}
.sec-head h2 { margin: 0; font-size: 1.4rem; }
.sec-head .bar {
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
    border-radius: 2px;
}

/* ── Stile search input ───────────────────────────── */
.stTextInput > div > div > input {
    border-radius: 14px !important;
    border: 2px solid rgba(100,255,218,.18) !important;
    padding: 13px 18px !important;
    font-size: 1rem !important;
    transition: border-color .3s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 24px rgba(100,255,218,.1) !important;
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
    # Inietta CSS una volta sola all'inizio della pagina
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

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

    # Card HTML con tutti i dettagli
    st.markdown(f"""
    <div class="news-card">
        <img class="news-card-img" src="{article['image']}"
             onerror="this.style.display='none'">
        <div class="news-card-body">
            <h3>{article['title']} {paid}</h3>
            <div class="news-meta">
                <span class="badge-source">{article['source']}</span>
                <span>📂 {article['category']}</span>
                <span class="badge-trend">🔥 {article['trend_score']:.0f}</span>
                {date_html}
                {author_html}
            </div>
            <p class="news-card-summary">{article.get('summary', '')}</p>
            <a class="btn-read" href="{article['link']}" target="_blank">
                🔗 Leggi l'articolo completo
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bottoni like/dislike — widget Streamlit nativi.
    # Ogni bottone ha una key univoca composta da prefix + azione + ID articolo.
    c1, c2, c3 = st.columns([1, 1, 6])
    with c1:
        if st.button("👍", key=f"{prefix}_l_{article['id']}"):
            if recommender:
                recommender.update_preference(article["id"], "like")
                # Sincronizza le preferenze aggiornate con session_state
                st.session_state.user_preferences = recommender.user_preferences
            st.toast("👍 Ti piace!")
    with c2:
        if st.button("👎", key=f"{prefix}_d_{article['id']}"):
            if recommender:
                recommender.update_preference(article["id"], "dislike")
                st.session_state.user_preferences = recommender.user_preferences
            st.toast("👎 Non ti piace!")