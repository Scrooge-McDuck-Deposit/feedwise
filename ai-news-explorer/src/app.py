"""
Entry point dell'applicazione AI News Trend Explorer.

Questo modulo:
1. Configura la pagina Streamlit (titolo, icona, layout)
2. Inizializza lo stato della sessione (preferenze utente)
3. Renderizza la sidebar con il menu di navigazione
4. Instrada la navigazione verso il componente corretto
   (Home, Categorie, Brainless, Preferenze)

Streamlit esegue questo file dall'alto verso il basso ad ogni
interazione dell'utente (click, input, ecc.). Lo stato persiste
tra i rerun grazie a st.session_state.
"""
import streamlit as st
from components.home import home_page
from components.categories import display_categories
from components.brainless import brainless_page
from components.preferences import preferences_page
from components.custom_sections import custom_section_page


# ── Configurazione pagina ────────────────────────────────────────────
# st.set_page_config DEVE essere la prima chiamata Streamlit nel file.
# Se qualsiasi altro st.* viene chiamato prima, Streamlit lancia errore.
#
# Parametri:
#   page_title   → testo mostrato nella tab del browser
#   page_icon    → emoji o URL dell'icona nella tab
#   layout       → "wide" usa tutta la larghezza dello schermo
#                   "centered" limita a ~700px (default)
#   initial_sidebar_state → "expanded" mostra la sidebar aperta
#                           "collapsed" la nasconde (utile su mobile)
st.set_page_config(
    page_title="AI News Trend Explorer",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ── Inizializzazione stato sessione ──────────────────────────────────
# st.session_state è un dizionario che persiste tra i rerun.
# Qui inizializziamo user_preferences con valori di default
# SOLO se non esiste già (primo accesso dell'utente).
#
# Struttura user_preferences:
#   likes                → lista di ID articoli piaciuti
#   dislikes             → lista di ID articoli non piaciuti
#   excluded_sources     → nomi fonti escluse dal feed
#   excluded_reasons     → motivazioni per ogni esclusione
#   category_time        → {categoria: secondi_permanenza}
#   enabled_paid_sources → fonti premium abilitate dall'utente
#   custom_sources       → feed RSS aggiunti manualmente
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {
        "likes": [],
        "dislikes": [],
        "excluded_sources": [],
        "excluded_reasons": {},
        "category_time": {},
        "enabled_paid_sources": [],
        "custom_sources": [],
        "custom_sections": []
    }


# ── Sidebar: Navigazione ────────────────────────────────────────────
# La sidebar è il pannello laterale sinistro di Streamlit.
# st.sidebar.* posiziona i widget al suo interno.
# st.sidebar.radio crea un gruppo di bottoni radio per la navigazione.
with st.sidebar:
    st.title("🌐 AI News Explorer")
    st.markdown("---")

    # Radio button per navigazione a 5 voci.
    # Il valore selezionato viene salvato automaticamente in session_state
    # e letto ad ogni rerun per decidere quale pagina mostrare.
    page = st.radio(
        "📍 Navigazione",
        ["🏠 Home", "📂 Categorie", "⭐ Le Mie Sezioni", "🧠 Brainless", "⚙️ Preferenze"],
        index=0,    # Pagina di default: Home
        label_visibility="collapsed"   # Nasconde l'etichetta "📍 Navigazione"
    )

    st.markdown("---")

    # Selettore lingua per traduzione sintetica degli articoli
    st.selectbox(
        "🌐 Lingua traduzione",
        [
            "🇮🇹 Italiano (originale)",
            "🇬🇧 English",
            "🇫🇷 Français",
            "🇩🇪 Deutsch",
            "🇪🇸 Español",
            "🇵🇹 Português",
            "🇯🇵 日本語",
            "🇨🇳 中文",
        ],
        index=0,
        key="translation_lang",
    )

    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")


# ── Router: instrada verso la pagina selezionata ────────────────────
# Ogni condizione chiama la funzione del componente corrispondente.
# Le funzioni sono importate dai moduli in components/.
if page == "🏠 Home":
    home_page()
elif page == "📂 Categorie":
    display_categories()
elif page == "⭐ Le Mie Sezioni":
    custom_section_page()
elif page == "🧠 Brainless":
    brainless_page()
elif page == "⚙️ Preferenze":
    preferences_page()