"""
Chatbot Guida — assistente virtuale che spiega le sezioni dell'app.

Usa st.chat_message / st.chat_input per offrire un'interfaccia
conversazionale. Risponde a domande sull'utilizzo delle varie
sezioni di AI News Trend Explorer.
"""
import streamlit as st

# ── Knowledge base: risposte per argomento ───────────────────────────
_SECTIONS = {
    "home": {
        "keywords": ["home", "pagina principale", "homepage", "inizio"],
        "title": "🏠 Home",
        "answer": (
            "La **Home** è la pagina principale dell'app. Trovi:\n\n"
            "- **Trending strip** — le notizie più calde del momento in card "
            "orizzontali scorrevoli.\n"
            "- **Mappa mondiale** — clicca su un Paese per vedere i trending "
            "topic di Google Trends con un'analisi AI dell'impatto economico.\n"
            "- **Feed articoli** — tutti gli articoli ordinati per trend score, "
            "con like/dislike per personalizzare il feed.\n"
            "- **Ricerca** — usa la barra in alto per filtrare gli articoli."
        ),
    },
    "categorie": {
        "keywords": ["categorie", "categoria", "categorie di notizie", "topics"],
        "title": "📂 Categorie",
        "answer": (
            "La sezione **Categorie** ti permette di sfogliare le notizie "
            "per argomento (Tecnologia, Finanza, Sport, ecc.).\n\n"
            "- Clicca su una card per aprire la categoria.\n"
            "- Ogni card mostra il numero di articoli disponibili.\n"
            "- All'interno trovi un'immagine hero, gli articoli con trend score, "
            "fonte, autore, data e un riassunto AI."
        ),
    },
    "sezioni": {
        "keywords": ["sezioni", "le mie sezioni", "sezioni personalizzate", "custom"],
        "title": "⭐ Le Mie Sezioni",
        "answer": (
            "In **Le Mie Sezioni** puoi creare raccolte personalizzate.\n\n"
            "- Vai in **Preferenze → Crea sezione personalizzata** per aggiungerne una.\n"
            "- Scegli un nome, seleziona le fonti che vuoi includere.\n"
            "- La sezione apparirà qui con gli articoli filtrati dalle fonti scelte."
        ),
    },
    "brainless": {
        "keywords": ["brainless", "meme", "humor", "divertente", "relax"],
        "title": "🧠 Brainless",
        "answer": (
            "**Brainless** è la sezione relax: meme, curiosità e contenuti "
            "leggeri per staccare dalle notizie serie.\n\n"
            "- Feed automatico da fonti di intrattenimento.\n"
            "- Perfetto per una pausa caffè!"
        ),
    },
    "preferenze": {
        "keywords": ["preferenze", "impostazioni", "settings", "configurazione"],
        "title": "⚙️ Preferenze",
        "answer": (
            "Nelle **Preferenze** puoi personalizzare la tua esperienza:\n\n"
            "- **Fonti preferite** — attiva/disattiva le fonti nel feed.\n"
            "- **Fonti escluse** — rimuovi fonti che non ti interessano.\n"
            "- **Sezioni personalizzate** — crea raccolte con le fonti che vuoi.\n"
            "- **Feed RSS personalizzati** — aggiungi qualsiasi feed RSS esterno.\n"
            "- **Reset** — ripristina tutto ai valori di default."
        ),
    },
    "mappa": {
        "keywords": ["mappa", "mondo", "world map", "google trends", "paesi", "nazioni"],
        "title": "🗺️ Mappa Mondiale",
        "answer": (
            "La **Mappa Mondiale** nella Home mostra i trending topic per Paese.\n\n"
            "- Clicca su un Paese per vederne i topic di tendenza.\n"
            "- Per ogni topic trovi: volume di ricerca, categoria, articoli correlati "
            "e un'analisi AI sull'impatto economico.\n"
            "- I dati arrivano da Google Trends in tempo reale."
        ),
    },
    "trend_score": {
        "keywords": ["trend score", "punteggio", "score", "classifica"],
        "title": "🔥 Trend Score",
        "answer": (
            "Il **Trend Score** è un punteggio da 0 a 100 che indica quanto "
            "una notizia è rilevante e di tendenza.\n\n"
            "- Tiene conto di: freschezza dell'articolo, popolarità della fonte "
            "e rilevanza del tema.\n"
            "- Più è alto, più la notizia è 'calda'."
        ),
    },
    "traduzione": {
        "keywords": ["traduzione", "lingua", "tradurre", "language", "translate"],
        "title": "🌐 Traduzione",
        "answer": (
            "Puoi tradurre i riassunti degli articoli in 7 lingue.\n\n"
            "- Usa il selettore **🌐 Lingua traduzione** nella sidebar.\n"
            "- Lingue disponibili: Italiano, English, Français, Deutsch, "
            "Español, Português, 日本語, 中文.\n"
            "- La traduzione è sintetica e si applica ai riassunti nel feed."
        ),
    },
}

_WELCOME = (
    "Ciao! 👋 Sono la tua guida per **AI News Trend Explorer**.\n\n"
    "Chiedimi qualsiasi cosa sull'app, ad esempio:\n"
    '- *"Come funziona la Home?"*\n'
    '- *"Cos\'è il Trend Score?"*\n'
    '- *"Come creo una sezione personalizzata?"*\n'
    '- *"Come traduco gli articoli?"*\n\n'
    "Oppure scrivi **aiuto** per vedere tutte le sezioni."
)

_HELP_TEXT = (
    "Ecco le sezioni di cui posso parlarti:\n\n"
    "| # | Sezione |\n"
    "|---|---|\n"
    "| 1 | 🏠 Home |\n"
    "| 2 | 📂 Categorie |\n"
    "| 3 | ⭐ Le Mie Sezioni |\n"
    "| 4 | 🧠 Brainless |\n"
    "| 5 | ⚙️ Preferenze |\n"
    "| 6 | 🗺️ Mappa Mondiale |\n"
    "| 7 | 🔥 Trend Score |\n"
    "| 8 | 🌐 Traduzione |\n\n"
    "Scrivi il nome di una sezione o fai una domanda!"
)

_FALLBACK = (
    "Non ho capito bene la domanda. 🤔\n\n"
    "Prova a chiedermi di una sezione specifica oppure scrivi "
    "**aiuto** per vedere l'elenco completo."
)


def _match_section(user_input: str) -> str | None:
    """Trova la sezione più pertinente al messaggio dell'utente."""
    text = user_input.lower().strip()
    if text in ("aiuto", "help", "?", "menu"):
        return "__help__"
    for key, section in _SECTIONS.items():
        for kw in section["keywords"]:
            if kw in text:
                return key
    return None


def render_chatbot():
    """Renderizza il chatbot nella sidebar come expander."""
    with st.sidebar.expander("💬 Guida interattiva", expanded=False):
        # Inizializza cronologia chat
        if "chatbot_history" not in st.session_state:
            st.session_state.chatbot_history = [
                {"role": "assistant", "content": _WELCOME}
            ]

        # Mostra messaggi precedenti
        for msg in st.session_state.chatbot_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="text-align:right; background:#1e3a5f; color:#e2e8f0;'
                    f' border-radius:12px; padding:8px 14px; margin:4px 0;'
                    f' display:inline-block; float:right; clear:both;'
                    f' max-width:85%; font-size:.88rem;">{msg["content"]}</div>'
                    '<div style="clear:both;"></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(msg["content"])

        # Input utente
        user_input = st.text_input(
            "Scrivi qui…",
            key="chatbot_input",
            label_visibility="collapsed",
            placeholder="Chiedimi qualcosa sull'app…",
        )

        if user_input:
            # Aggiungi messaggio utente
            st.session_state.chatbot_history.append(
                {"role": "user", "content": user_input}
            )

            # Genera risposta
            match = _match_section(user_input)
            if match == "__help__":
                reply = _HELP_TEXT
            elif match:
                section = _SECTIONS[match]
                reply = f"**{section['title']}**\n\n{section['answer']}"
            else:
                reply = _FALLBACK

            st.session_state.chatbot_history.append(
                {"role": "assistant", "content": reply}
            )
            st.rerun()
