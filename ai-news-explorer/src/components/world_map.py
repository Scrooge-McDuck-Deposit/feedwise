"""
Componente Mappa del Mondo — trending topics per paese.

Mostra una mappa interattiva del mondo con i topic di tendenza
di Google Trends per ogni paese selezionato. L'analisi AI
spiega perché ogni topic è in tendenza.
"""
import streamlit as st
import plotly.graph_objects as go
import feedparser
import requests
import re
import random
import hashlib
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
#  CSS — Stili per la sezione mappa e le card dei topic
# ══════════════════════════════════════════════════════════════════════

MAP_SECTION_CSS = """
<style>
/* ── Container principale della sezione mappa ──────── */
.world-map-section {
    background: linear-gradient(160deg, #0a0f1f 0%, #111827 40%, #0d1b2a 100%);
    border-radius: 24px;
    padding: 36px 32px 28px;
    margin: 36px 0 28px;
    border: 1px solid rgba(100,255,218,0.08);
    box-shadow:
        0 24px 80px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(100,255,218,0.06);
    position: relative;
    overflow: hidden;
}
.world-map-section::before {
    content: '';
    position: absolute;
    top: -120px; right: -120px;
    width: 340px; height: 340px;
    background: radial-gradient(circle, rgba(100,255,218,0.06) 0%, transparent 70%);
    pointer-events: none;
}

/* ── Header sezione ────────────────────────────────── */
.map-header {
    text-align: center;
    margin-bottom: 28px;
    position: relative;
}
.map-header h2 {
    font-size: 1.7rem;
    color: #e2e8f0;
    margin: 0 0 6px;
    letter-spacing: 0.5px;
}
.map-header p {
    color: #64748b;
    font-size: 0.92rem;
    margin: 0;
}
.map-header .accent-line {
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, #64ffda, #00bfa5);
    border-radius: 2px;
    margin: 12px auto 0;
}

/* ── Country header ────────────────────────────────── */
.country-trending-header {
    background: linear-gradient(135deg, rgba(100,255,218,0.08), rgba(0,191,165,0.04));
    border: 1px solid rgba(100,255,218,0.12);
    border-radius: 16px;
    padding: 22px 28px;
    margin: 20px 0 24px;
    text-align: center;
}
.country-trending-header h3 {
    color: #64ffda;
    font-size: 1.35rem;
    margin: 0 0 4px;
}
.country-trending-header p {
    color: #94a3b8;
    font-size: 0.85rem;
    margin: 0;
}

/* ── Topic card con glassmorphism ──────────────────── */
.topic-card {
    background: rgba(17, 24, 39, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(100,255,218,0.07);
    border-radius: 18px;
    padding: 0;
    margin-bottom: 18px;
    transition: all 0.35s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
}
.topic-card:hover {
    transform: translateY(-4px);
    border-color: rgba(100,255,218,0.2);
    box-shadow:
        0 12px 40px rgba(0,0,0,0.3),
        0 0 30px rgba(100,255,218,0.06);
}

/* Glow per le prime 3 posizioni */
.topic-card.rank-1 { border-color: rgba(251,191,36,0.25); }
.topic-card.rank-1:hover { box-shadow: 0 12px 40px rgba(251,191,36,0.12); }
.topic-card.rank-2 { border-color: rgba(148,163,184,0.2); }
.topic-card.rank-3 { border-color: rgba(167,139,250,0.2); }

/* ── Layout interno card ───────────────────────────── */
.topic-card-inner {
    display: flex;
    gap: 20px;
    padding: 22px 24px;
    align-items: flex-start;
}

/* ── Badge posizione ───────────────────────────────── */
.rank-badge {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 14px;
    font-weight: 800;
    font-size: 1.05rem;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.rank-badge.gold   { background: linear-gradient(135deg, #fbbf24, #f59e0b); }
.rank-badge.silver { background: linear-gradient(135deg, #cbd5e1, #94a3b8); }
.rank-badge.bronze { background: linear-gradient(135deg, #c084fc, #7c3aed); }
.rank-badge.base   { background: linear-gradient(135deg, #374151, #1f2937); }

/* ── Contenuto topic ───────────────────────────────── */
.topic-content {
    flex: 1;
    min-width: 0;
}
.topic-title {
    font-size: 1.12rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0 0 8px;
    line-height: 1.35;
}

/* ── Indicatori traffico ───────────────────────────── */
.traffic-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.traffic-badge {
    background: rgba(251,191,36,0.1);
    color: #fbbf24;
    padding: 3px 12px;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: 700;
}
.date-badge {
    color: #64748b;
    font-size: 0.78rem;
}
.traffic-bar-container {
    width: 100%;
    height: 3px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 14px;
}
.traffic-bar {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #64ffda, #00bfa5, #38bdf8);
    animation: pulse-bar 2.5s ease-in-out infinite;
}
@keyframes pulse-bar {
    0%, 100% { opacity: 0.55; }
    50% { opacity: 1; }
}

/* ── Box analisi AI ────────────────────────────────── */
.ai-analysis-box {
    background: linear-gradient(135deg,
        rgba(100,255,218,0.04) 0%,
        rgba(56,189,248,0.03) 100%);
    border-left: 3px solid #64ffda;
    border-radius: 0 14px 14px 0;
    padding: 16px 18px;
    margin: 0 24px 18px;
}
.ai-analysis-box .ai-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #64ffda;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
}
.ai-analysis-box .ai-label .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #64ffda;
    animation: blink-dot 1.5s ease-in-out infinite;
}
@keyframes blink-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.ai-analysis-box p {
    color: #ccd6f6;
    font-size: 0.88rem;
    line-height: 1.75;
    margin: 0;
}

/* ── Articoli correlati ────────────────────────────── */
.related-articles {
    padding: 0 24px 18px;
    border-top: 1px solid rgba(255,255,255,0.04);
}
.related-articles h4 {
    font-size: 0.78rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 14px 0 10px;
}
.related-article-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}
.related-article-item:last-child { border-bottom: none; }
.related-article-item .bullet {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #64ffda;
    flex-shrink: 0;
}
.related-article-item a {
    color: #94a3b8;
    text-decoration: none;
    font-size: 0.84rem;
    line-height: 1.45;
    transition: color 0.2s;
}
.related-article-item a:hover { color: #64ffda; }
.related-article-item .src-tag {
    color: #475569;
    font-size: 0.72rem;
    flex-shrink: 0;
}

/* ── Immagine topic hero (grande, centrata in alto) ──── */
.topic-picture-wrap {
    width: 100%;
    max-height: 260px;
    overflow: hidden;
    border-radius: 18px 18px 0 0;
}
.topic-picture {
    width: 100%;
    height: 260px;
    object-fit: cover;
    display: block;
    transition: transform 0.4s ease;
}
.topic-card:hover .topic-picture {
    transform: scale(1.04);
}

/* ── Responsive ────────────────────────────────────── */
@media (max-width: 640px) {
    .topic-card-inner { flex-direction: column; gap: 12px; }
    .topic-picture { height: 180px; }
    .world-map-section { padding: 20px 16px; }
    .ai-analysis-box { margin: 0 16px 16px; }
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════
#  DATI — Paesi raggruppati per continente con codici ISO
# ══════════════════════════════════════════════════════════════════════

COUNTRIES_BY_CONTINENT = {
    "🌍 Europa": {
        "Italia":             {"a2": "IT", "a3": "ITA"},
        "Francia":            {"a2": "FR", "a3": "FRA"},
        "Germania":           {"a2": "DE", "a3": "DEU"},
        "Spagna":             {"a2": "ES", "a3": "ESP"},
        "Regno Unito":        {"a2": "GB", "a3": "GBR"},
        "Paesi Bassi":        {"a2": "NL", "a3": "NLD"},
        "Polonia":            {"a2": "PL", "a3": "POL"},
        "Portogallo":         {"a2": "PT", "a3": "PRT"},
        "Svezia":             {"a2": "SE", "a3": "SWE"},
        "Svizzera":           {"a2": "CH", "a3": "CHE"},
        "Austria":            {"a2": "AT", "a3": "AUT"},
        "Belgio":             {"a2": "BE", "a3": "BEL"},
        "Norvegia":           {"a2": "NO", "a3": "NOR"},
        "Danimarca":          {"a2": "DK", "a3": "DNK"},
        "Irlanda":            {"a2": "IE", "a3": "IRL"},
        "Grecia":             {"a2": "GR", "a3": "GRC"},
        "Rep. Ceca":          {"a2": "CZ", "a3": "CZE"},
        "Romania":            {"a2": "RO", "a3": "ROU"},
        "Ungheria":           {"a2": "HU", "a3": "HUN"},
        "Finlandia":          {"a2": "FI", "a3": "FIN"},
        "Ucraina":            {"a2": "UA", "a3": "UKR"},
    },
    "🌎 Americhe": {
        "Stati Uniti":        {"a2": "US", "a3": "USA"},
        "Canada":             {"a2": "CA", "a3": "CAN"},
        "Messico":            {"a2": "MX", "a3": "MEX"},
        "Brasile":            {"a2": "BR", "a3": "BRA"},
        "Argentina":          {"a2": "AR", "a3": "ARG"},
        "Colombia":           {"a2": "CO", "a3": "COL"},
        "Cile":               {"a2": "CL", "a3": "CHL"},
        "Perù":               {"a2": "PE", "a3": "PER"},
    },
    "🌏 Asia": {
        "Giappone":           {"a2": "JP", "a3": "JPN"},
        "Corea del Sud":      {"a2": "KR", "a3": "KOR"},
        "India":              {"a2": "IN", "a3": "IND"},
        "Indonesia":          {"a2": "ID", "a3": "IDN"},
        "Thailandia":         {"a2": "TH", "a3": "THA"},
        "Vietnam":            {"a2": "VN", "a3": "VNM"},
        "Filippine":          {"a2": "PH", "a3": "PHL"},
        "Taiwan":             {"a2": "TW", "a3": "TWN"},
        "Malesia":            {"a2": "MY", "a3": "MYS"},
        "Singapore":          {"a2": "SG", "a3": "SGP"},
    },
    "🕌 Medio Oriente": {
        "Turchia":            {"a2": "TR", "a3": "TUR"},
        "Arabia Saudita":     {"a2": "SA", "a3": "SAU"},
        "Emirati Arabi":      {"a2": "AE", "a3": "ARE"},
        "Israele":            {"a2": "IL", "a3": "ISR"},
        "Egitto":             {"a2": "EG", "a3": "EGY"},
    },
    "🌍 Africa": {
        "Sudafrica":          {"a2": "ZA", "a3": "ZAF"},
        "Nigeria":            {"a2": "NG", "a3": "NGA"},
        "Kenya":              {"a2": "KE", "a3": "KEN"},
    },
    "🌊 Oceania": {
        "Australia":          {"a2": "AU", "a3": "AUS"},
        "Nuova Zelanda":      {"a2": "NZ", "a3": "NZL"},
    },
    "🏔️ Eurasia": {
        "Russia":             {"a2": "RU", "a3": "RUS"},
    },
}

# Flat lookup: alpha3 -> country_name (per il map hover)
_ALL_COUNTRIES_A3 = {}
for _cont, _countries in COUNTRIES_BY_CONTINENT.items():
    for _name, _codes in _countries.items():
        _ALL_COUNTRIES_A3[_codes["a3"]] = _name

# Reverse lookup: alpha3 → {name, a2, continent}
_A3_TO_INFO = {}
for _cont2, _countries2 in COUNTRIES_BY_CONTINENT.items():
    for _name2, _codes2 in _countries2.items():
        _A3_TO_INFO[_codes2["a3"]] = {
            "name": _name2, "a2": _codes2["a2"], "continent": _cont2
        }


# ══════════════════════════════════════════════════════════════════════
#  PATTERN per inferenza tematica dei topic  (analisi AI)
# ══════════════════════════════════════════════════════════════════════

_CATEGORY_PATTERNS = {
    "sport": re.compile(
        r"(?i)\b(calcio|soccer|football|serie ?a|champions|nba|tennis|"
        r"f1|formula|gol|partita|match|league|cup|olimp|world\s?cup|"
        r"gp|gran\s?premio|basket|rugby|ciclismo|tour|giro)\b"
    ),
    "politica": re.compile(
        r"(?i)\b(governo|elezioni|parlamento|voto|president|ministr|"
        r"legge|riforma|senato|congresso|election|summit|nato|"
        r"democrat|republic|sanzioni|geopolitic)\b"
    ),
    "tech": re.compile(
        r"(?i)\b(apple|google|ai|artificial|iphone|samsung|tech|"
        r"software|app|robot|cyber|chatgpt|openai|meta|microsoft|"
        r"startup|blockchain|crypto|bitcoin)\b"
    ),
    "intrattenimento": re.compile(
        r"(?i)\b(film|serie ?tv|netflix|concerto|sanremo|oscar|grammy|"
        r"festival|attore|attrice|album|musica|cinema|disney|"
        r"celebrity|star|reality|show)\b"
    ),
    "economia": re.compile(
        r"(?i)\b(borsa|mercato|inflazione|pil|gdp|euro|dollaro|"
        r"prezzo|costo|banca|econom|wall\s?street|nasdaq|fed|"
        r"tassi|interest\s?rate|recession)\b"
    ),
    "scienza": re.compile(
        r"(?i)\b(spazio|nasa|scoperta|ricerca|vaccin|studio|"
        r"scienziato|medic|salut|pianeta|clima|dna|genoma|"
        r"satellite|asteroide|mars|moon)\b"
    ),
    "cronaca": re.compile(
        r"(?i)\b(incidente|terremoto|alluvione|emergenza|mort[ei]|"
        r"vittime|arresto|polizia|uragano|sisma|esplosione|"
        r"frana|inondazione|disastro|scompar)\b"
    ),
}


# ══════════════════════════════════════════════════════════════════════
#  FUNZIONE PRINCIPALE — entry point chiamato dalla home page
# ══════════════════════════════════════════════════════════════════════

def render_world_map_section():
    """Renderizza la sezione mappa del mondo con trending topics.

    La mappa è cliccabile: l'utente seleziona un paese cliccando
    direttamente sulla mappa (marcatori Scattergeo). I trending
    topics vengono mostrati sotto la mappa per il paese selezionato.
    """

    # Inietta CSS
    st.markdown(MAP_SECTION_CSS, unsafe_allow_html=True)

    # ── Header sezione ──
    st.markdown("""
    <div class="world-map-section">
        <div class="map-header">
            <h2>🌍 Trending nel Mondo</h2>
            <p>Clicca su un paese per scoprire gli argomenti più cercati</p>
            <div class="accent-line"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stato selezione corrente ──
    sel_a3 = st.session_state.get("map_clicked_a3", "")

    # ── Mappa del mondo cliccabile ──
    all_a3 = list(_ALL_COUNTRIES_A3.keys())
    fig = _create_world_map(sel_a3)

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
        on_select="rerun",
        selection_mode="points",
        key="world_map_click",
    )

    # ── Gestione click sulla mappa ──
    if event and event.selection and event.selection.points:
        for pt in event.selection.points:
            # Prova ad ottenere il codice ISO-3 direttamente
            loc = pt.get("location", "")
            if not loc:
                # Fallback: usa l'indice del punto nel trace Scattergeo
                idx = pt.get("point_index", pt.get("pointNumber", None))
                if idx is not None and 0 <= idx < len(all_a3):
                    loc = all_a3[idx]
            if loc and loc in _A3_TO_INFO:
                st.session_state["map_clicked_a3"] = loc
                sel_a3 = loc
                break

    # ── Trending topics per il paese selezionato ──
    if sel_a3 and sel_a3 in _A3_TO_INFO:
        info = _A3_TO_INFO[sel_a3]
        country_name = info["name"]
        selected_a2 = info["a2"]

        # Bottone per deselezionare
        if st.button("🔄 Deseleziona paese", key="map_reset"):
            st.session_state["map_clicked_a3"] = ""
            st.rerun()

        st.markdown(f"""
        <div class="country-trending-header">
            <h3>📊 Trending in {country_name}</h3>
            <p>I topic più cercati nelle ultime 24 ore</p>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner(f"Analisi dei trend per {country_name}…"):
            topics = _fetch_trending_topics(selected_a2)

        if topics:
            _render_topic_cards(topics, country_name)
        else:
            st.info(
                f"Nessun dato di tendenza disponibile per **{country_name}** "
                "al momento. Prova un altro paese!"
            )
    else:
        st.markdown("""
        <div style="text-align:center; color:#64748b; padding:24px 0 8px;">
            <span style="font-size:1.5rem;">👆</span><br>
            <span style="font-size:0.92rem;">
                Clicca su un punto sulla mappa per esplorare i trending topics
            </span>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  MAPPA — Choropleth Plotly con tema dark
# ══════════════════════════════════════════════════════════════════════

def _create_world_map(selected_a3):
    """Costruisce la mappa choropleth con marcatori cliccabili."""

    all_a3 = list(_ALL_COUNTRIES_A3.keys())
    all_names = [_ALL_COUNTRIES_A3[c] for c in all_a3]

    # Valore visivo: 0.3 = paesi supportati, 1 = selezionato
    values = [1 if c == selected_a3 else 0.3 for c in all_a3]

    fig = go.Figure()

    # Layer base: choropleth per colorazione geografica
    fig.add_trace(go.Choropleth(
        locations=all_a3,
        z=values,
        text=all_names,
        locationmode="ISO-3",
        colorscale=[
            [0, "#1e293b"],
            [0.3, "#1e3a4f"],
            [1, "#64ffda"],
        ],
        showscale=False,
        marker_line_color="rgba(100,255,218,0.18)",
        marker_line_width=0.6,
        hoverinfo="skip",
    ))

    # Layer interattivo: marcatori Scattergeo cliccabili
    marker_colors = [
        "#64ffda" if c == selected_a3 else "rgba(100,255,218,0.55)"
        for c in all_a3
    ]
    marker_sizes = [14 if c == selected_a3 else 7 for c in all_a3]

    fig.add_trace(go.Scattergeo(
        locations=all_a3,
        locationmode="ISO-3",
        text=all_names,
        mode="markers",
        marker=dict(
            size=marker_sizes,
            color=marker_colors,
            line=dict(width=1, color="rgba(100,255,218,0.25)"),
        ),
        hovertemplate="<b>%{text}</b><br>📊 Clicca per i trending<extra></extra>",
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="#64ffda",
            font=dict(color="#e2e8f0", size=13),
        ),
        showlegend=False,
    ))

    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(100,255,218,0.12)",
            projection_type="natural earth",
            bgcolor="rgba(0,0,0,0)",
            landcolor="#0f172a",
            oceancolor="#060d18",
            showocean=True,
            showlakes=False,
            showcountries=True,
            countrycolor="rgba(100,255,218,0.1)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
#  FETCH — Google Trends RSS per paese
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_trending_topics(country_code):
    """
    Scarica i trending topics da Google Trends RSS.

    Args:
        country_code: Codice ISO alpha-2 del paese (es. "IT", "US")

    Returns:
        list[dict]: Lista di topic con title, traffic, picture,
                    news_items, pub_date, link
    """
    url = f"https://trends.google.com/trending/rss?geo={country_code}"

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        raw_xml = resp.text
    except Exception:
        return []

    feed = feedparser.parse(raw_xml)
    if not feed.entries:
        return []

    # Pre-parse: estrai blocchi <item>...</item> dal raw XML
    # per poter estrarre i news_item multipli (feedparser li appiattisce)
    item_blocks = re.findall(r"<item>(.*?)</item>", raw_xml, re.DOTALL)

    topics = []
    for i, entry in enumerate(feed.entries[:20]):
        title = re.sub(r"<[^>]+>", "", entry.get("title", "")).strip()
        if not title:
            continue

        # Traffico
        traffic = re.sub(r"<[^>]+>", "", str(entry.get("ht_approx_traffic", ""))).strip()

        # Immagine
        picture = str(entry.get("ht_picture", "")).strip()

        # Data pubblicazione
        pub_date = entry.get("published", entry.get("updated", ""))

        # Link
        link = entry.get("link", "")

        # News items: parse dal blocco XML grezzo corrispondente
        news_items = []
        if i < len(item_blocks):
            news_items = _parse_news_items_xml(item_blocks[i])

        topics.append({
            "title": title,
            "traffic": traffic,
            "picture": picture,
            "news_items": news_items,
            "pub_date": pub_date,
            "link": link,
        })

    return topics


def _parse_news_items_xml(item_xml):
    """Estrae i singoli ht:news_item da un blocco <item> XML grezzo."""
    items = []
    blocks = re.findall(
        r"<ht:news_item>(.*?)</ht:news_item>", item_xml, re.DOTALL
    )
    for block in blocks[:5]:
        title = _xml_tag(block, "ht:news_item_title")
        url = _xml_tag(block, "ht:news_item_url")
        source = _xml_tag(block, "ht:news_item_source")
        items.append({"title": title, "url": url, "source": source})
    return items


def _xml_tag(xml, tag):
    """Estrae il contenuto testuale di un tag XML."""
    m = re.search(rf"<{re.escape(tag)}>(.*?)</{re.escape(tag)}>", xml, re.DOTALL)
    if m:
        text = m.group(1).strip()
        # Decode HTML entities
        text = text.replace("&amp;", "&").replace("&apos;", "'")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = re.sub(r"<[^>]+>", "", text).strip()
        return text
    return ""


def _parse_news_from_html(html):
    """Estrae articoli correlati dall'HTML della description di Google Trends."""
    if not html:
        return []

    items = []
    # Pattern: <a href="url">Titolo</a> ... <font ...>Fonte</font>
    link_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>')
    source_pattern = re.compile(r'<font[^>]*color=["\']#6f6f6f["\'][^>]*>([^<]+)</font>')

    links = link_pattern.findall(html)
    sources = source_pattern.findall(html)

    for i, (url, title) in enumerate(links):
        title_clean = re.sub(r"<[^>]+>", "", title).strip()
        if not title_clean:
            continue
        source = sources[i].strip() if i < len(sources) else ""
        items.append({
            "title": title_clean,
            "url": url,
            "source": source,
        })

    return items[:5]


# ══════════════════════════════════════════════════════════════════════
#  ANALISI AI — Genera spiegazione del perché un topic è di tendenza
# ══════════════════════════════════════════════════════════════════════

def _generate_ai_analysis(topic, rank, country_name):
    """
    Genera un'analisi AI che spiega perché il topic è di tendenza.

    Combina dati strutturati (traffico, notizie correlate, ranking)
    con template linguistici per produrre un testo descrittivo.
    """
    title = topic["title"]
    traffic = topic["traffic"]
    news_items = topic.get("news_items", [])

    # ── Parse del volume di traffico ──
    traffic_num = 0
    if traffic:
        cleaned = re.sub(r"[^\d]", "", traffic)
        if cleaned:
            traffic_num = int(cleaned)

    # ── Inferenza categoria tematica ──
    category = _infer_category(title, news_items)

    # ── Costruzione dell'analisi ──
    parts = []

    # Parte 1: Intensità del trend
    if traffic_num >= 1_000_000:
        parts.append(
            f"Questo argomento sta generando un'ondata eccezionale di interesse "
            f"con oltre **{traffic}** ricerche nelle ultime 24 ore, "
            f"posizionandosi come uno dei topic più discussi in {country_name}."
        )
    elif traffic_num >= 500_000:
        parts.append(
            f"Un volume di ricerca molto elevato con **{traffic}** query indica "
            f"che l'argomento ha catturato l'attenzione di massa in {country_name}."
        )
    elif traffic_num >= 100_000:
        parts.append(
            f"Con circa **{traffic}** ricerche, questo topic mostra un forte "
            f"coinvolgimento del pubblico e una crescita significativa di interesse."
        )
    elif traffic:
        parts.append(
            f"L'argomento registra **{traffic}** ricerche, segnalando un "
            f"interesse crescente tra gli utenti."
        )
    else:
        parts.append(
            f"Questo argomento si è posizionato al **#{rank}** tra i topic "
            f"più cercati in {country_name} nelle ultime ore."
        )

    # Parte 2: Contesto tematico
    category_insights = {
        "sport": (
            "Il mondo dello sport sta catalizzando l'attenzione: "
            "eventi, risultati o trasferimenti stanno alimentando il dibattito tra gli appassionati."
        ),
        "politica": (
            "Le dinamiche politiche sono al centro dell'attenzione pubblica. "
            "Decisioni istituzionali o dichiarazioni stanno generando un acceso confronto."
        ),
        "tech": (
            "Il settore tecnologico è in fermento. Lanci di prodotti, aggiornamenti AI "
            "o novità dal mondo digitale stanno guidando questo trend."
        ),
        "intrattenimento": (
            "Il mondo dello spettacolo sta dominando le conversazioni. "
            "Uscite, premi o gossip stanno attirando l'interesse del pubblico."
        ),
        "economia": (
            "I mercati finanziari e le dinamiche economiche sono sotto i riflettori. "
            "Dati macroeconomici o movimenti di borsa stanno influenzando le ricerche."
        ),
        "scienza": (
            "Una scoperta scientifica o un evento legato al mondo della ricerca "
            "sta stimolando la curiosità e l'interesse collettivo."
        ),
        "cronaca": (
            "Un evento di cronaca rilevante sta concentrando l'attenzione del pubblico, "
            "generando forte risonanza mediatica e sociale."
        ),
    }
    if category in category_insights:
        parts.append(category_insights[category])

    # Parte 2b: Analisi impatto di mercato (solo per topic economici)
    if category == "economia":
        market_impacts = [
            f"📈 **Impatto di mercato**: questo topic potrebbe influenzare gli indici "
            f"azionari e i mercati valutari di {country_name}. I trader e gli investitori "
            f"monitorano attentamente questo tipo di notizie per anticipare movimenti di prezzo.",
            f"💹 **Analisi di mercato**: le implicazioni economiche di questo trend "
            f"potrebbero riflettersi sugli spread obbligazionari e sulle quotazioni "
            f"delle principali blue chip. Attenzione alla volatilità nelle prossime sedute.",
            f"🏦 **Prospettiva finanziaria**: l'elevato interesse per questo argomento "
            f"suggerisce possibili ripercussioni sui tassi di cambio e sulla fiducia "
            f"degli investitori nel mercato di {country_name}.",
        ]
        h = int(hashlib.md5(title.encode()).hexdigest()[:8], 16)
        parts.append(market_impacts[h % len(market_impacts)])

    # Parte 3: Fonti e copertura mediatica
    if news_items:
        unique_sources = list({
            item["source"] for item in news_items if item.get("source")
        })
        if unique_sources:
            if len(unique_sources) >= 3:
                parts.append(
                    f"La notizia è trattata da molteplici testate tra cui "
                    f"**{unique_sources[0]}**, **{unique_sources[1]}** e "
                    f"**{unique_sources[2]}**, confermando una copertura "
                    f"mediatica ampia e trasversale."
                )
            elif len(unique_sources) >= 1:
                parts.append(
                    f"Fonti come **{', '.join(unique_sources)}** stanno "
                    f"dando copertura all'argomento."
                )

        # Contesto dalla prima notizia
        if news_items[0].get("title"):
            first_title = news_items[0]["title"][:120]
            parts.append(f'Tra le notizie correlate: *"{first_title}"*.')

    # Parte 4: Conclusione basata sul rank
    if rank == 1:
        parts.append(
            "🏆 **Topic #1** — l'argomento più cercato del momento, "
            "segno di un impatto sociale e mediatico di primo piano."
        )
    elif rank <= 3:
        parts.append(
            "Un topic ai vertici della classifica, destinato a rimanere "
            "al centro dell'attenzione nelle prossime ore."
        )

    return " ".join(parts)


def _infer_category(title, news_items):
    """Inferisce la categoria tematica da titolo e articoli correlati."""
    # Combina titolo + titoli notizie per avere più contesto
    corpus = title
    for item in news_items[:3]:
        corpus += " " + item.get("title", "")

    for cat_name, pattern in _CATEGORY_PATTERNS.items():
        if pattern.search(corpus):
            return cat_name
    return ""


# ══════════════════════════════════════════════════════════════════════
#  RENDER — Card dei trending topics
# ══════════════════════════════════════════════════════════════════════

def _render_topic_cards(topics, country_name):
    """Renderizza le card dei topic di tendenza con analisi AI."""

    for i, topic in enumerate(topics):
        rank = i + 1
        title = topic["title"]
        traffic = topic["traffic"]
        picture = topic.get("picture", "")
        news_items = topic.get("news_items", [])
        link = topic.get("link", "")

        # ── Badge rank ──
        if rank == 1:
            rank_class = "gold"
            card_class = "rank-1"
        elif rank == 2:
            rank_class = "silver"
            card_class = "rank-2"
        elif rank == 3:
            rank_class = "bronze"
            card_class = "rank-3"
        else:
            rank_class = "base"
            card_class = ""

        # ── Traffic bar width (proporzionale al max) ──
        traffic_num = 0
        if traffic:
            cleaned = re.sub(r"[^\d]", "", traffic)
            if cleaned:
                traffic_num = int(cleaned)
        # Normalizza: max ragionevole 2M di ricerche
        bar_width = min(traffic_num / 20000, 100) if traffic_num else 15

        # ── Immagine hero centrata ──
        picture_html = ""
        if picture:
            picture_html = (
                '<div class="topic-picture-wrap">'
                f'<img class="topic-picture" src="{picture}" onerror="this.parentElement.style.display=\'none\'">'
                '</div>'
            )

        # ── Traffic badge ──
        traffic_html = ""
        if traffic:
            traffic_html = f'<span class="traffic-badge">🔥 {traffic} ricerche</span>'

        # ── Data ──
        pub_date = topic.get("pub_date", "")
        date_html = ""
        if pub_date:
            date_html = f'<span class="date-badge">📅 {pub_date[:22]}</span>'

        # ── Analisi AI ──
        analysis = _generate_ai_analysis(topic, rank, country_name)
        # Converti markdown bold/italic in HTML
        analysis_html = analysis.replace("**", "<b>", 1)
        # Alterna apertura/chiusura bold
        while "**" in analysis_html:
            analysis_html = analysis_html.replace("**", "</b>", 1)
            if "**" in analysis_html:
                analysis_html = analysis_html.replace("**", "<b>", 1)
        analysis_html = analysis_html.replace("*", "<em>", 1)
        while "*" in analysis_html:
            analysis_html = analysis_html.replace("*", "</em>", 1)
            if "*" in analysis_html:
                analysis_html = analysis_html.replace("*", "<em>", 1)

        # ── Articoli correlati HTML ──
        related_html = ""
        if news_items:
            items_html = ""
            for item in news_items[:4]:
                item_title = item.get("title", "")
                item_url = item.get("url", "#")
                item_source = item.get("source", "")
                src_tag = f'<span class="src-tag">— {item_source}</span>' if item_source else ""
                items_html += (
                    '<div class="related-article-item">'
                    '<div class="bullet"></div>'
                    f'<a href="{item_url}" target="_blank" rel="noopener">{item_title}</a>'
                    f'{src_tag}'
                    '</div>'
                )
            related_html = (
                '<div class="related-articles">'
                '<h4>📰 Notizie Correlate</h4>'
                f'{items_html}'
                '</div>'
            )

        # ── Link al topic ──
        link_html = ""
        if link:
            link_html = (
                f'<a href="{link}" target="_blank" rel="noopener" '
                f'style="color:#64ffda; font-size:0.78rem; text-decoration:none; '
                f'font-weight:600;">Esplora su Google Trends →</a>'
            )

        # ── Analisi AI HTML ──
        ai_html = (
            '<div class="ai-analysis-box">'
            '<div class="ai-label"><div class="dot"></div>Analisi AI</div>'
            f'<p>{analysis_html}</p>'
            '</div>'
        )

        # ── Render card completa ──
        # Layout: immagine grande in alto → titolo+traffic → notizie correlate → analisi AI
        card_html = (
            f'<div class="topic-card {card_class}">'
            f'{picture_html}'
            f'<div class="topic-card-inner">'
            f'<div class="rank-badge {rank_class}">#{rank}</div>'
            f'<div class="topic-content">'
            f'<div class="topic-title">{title}</div>'
            f'<div class="traffic-row">{traffic_html}{date_html}{link_html}</div>'
            f'<div class="traffic-bar-container"><div class="traffic-bar" style="width: {bar_width}%;"></div></div>'
            f'</div>'
            f'</div>'
            f'{related_html}'
            f'{ai_html}'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)
