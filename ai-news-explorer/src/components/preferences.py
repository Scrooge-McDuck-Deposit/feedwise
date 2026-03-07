import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from feeds.source_registry import SourceRegistry


def preferences_page():
    """
    Pagina principale delle preferenze utente.
    
    Questa funzione orchestra l'intera UI della sezione Preferenze,
    suddivisa in 5 macro-sezioni:
      1. Profilo AI         — mostra statistiche, grafici e descrizione del profilo
      2. Fonti a pagamento  — toggle per abilitare/disabilitare fonti premium
      3. Fonti personalizzate — form per aggiungere nuovi feed RSS custom
      4. Escludi fonti      — checkbox per escludere fonti dal feed
      5. Reset              — bottone per azzerare tutte le preferenze
    
    Tutti i dati sono letti e scritti in `st.session_state.user_preferences`,
    un dizionario persistente nella sessione Streamlit corrente con questa struttura:
    {
        "likes": [id1, id2, ...],              # ID articoli piaciuti
        "dislikes": [id1, id2, ...],           # ID articoli non piaciuti
        "excluded_sources": ["fonte1", ...],   # Nomi fonti escluse dal feed
        "excluded_reasons": {"fonte1": "motivo", ...},  # Motivi esclusione
        "category_time": {"Tecnologia": 120, ...},      # Secondi per categoria
        "enabled_paid_sources": ["fonte1", ...],        # Fonti premium attivate
        "custom_sources": [{name, url, category, ...}]  # Fonti RSS aggiunte dall'utente
    }
    """
    st.title("⚙️ Gestione Fonti e Preferenze")

    # Inizializza la lista fonti personalizzate se manca
    # (necessario per utenti alla prima visita)
    if "custom_sources" not in st.session_state.user_preferences:
        st.session_state.user_preferences["custom_sources"] = []

    # Carica il registro fonti (DEFAULT_SOURCES + eventuale sources.json)
    registry = SourceRegistry()
    sources = registry.get_sources()

    # ===========================================================
    # SEZIONE 1: PROFILO UTENTE AI
    # Mostra all'utente come l'algoritmo lo "vede":
    # - Metriche numeriche (like, dislike, fonti escluse, premium, custom)
    # - Grafico a barre orizzontali degli interessi per categoria
    # - Radar chart (se ci sono almeno 3 categorie con dati)
    # - Descrizione testuale del profilo (delegata a _render_profile_description)
    # ===========================================================
    st.header("🤖 Il tuo Profilo AI")
    st.caption("Ecco come l'algoritmo ti vede in base alle tue interazioni.")

    prefs = st.session_state.user_preferences

    # --- Metriche principali ---
    # 5 colonne affiancate con i contatori delle interazioni dell'utente.
    # st.metric mostra il valore numerico con etichetta.
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👍 Like", len(prefs["likes"]))
    col2.metric("👎 Dislike", len(prefs["dislikes"]))
    col3.metric("🚫 Escluse", len(prefs["excluded_sources"]))
    col4.metric("💳 Premium", len(prefs["enabled_paid_sources"]))
    col5.metric("📡 Custom", len(prefs.get("custom_sources", [])))

    # --- Grafico interessi per categoria ---
    # category_time è un dict {categoria: secondi_di_permanenza}
    # che viene aggiornato man mano che l'utente esplora le categorie.
    # Qui lo convertiamo in un DataFrame per Plotly.
    cat_time = prefs.get("category_time", {})
    if cat_time:
        st.subheader("📊 I tuoi Interessi per Categoria")

        # Costruisce un DataFrame con:
        # - Tempo in minuti (per leggibilità)
        # - Punteggio Interesse: secondi * 2, cap a 100
        #   (più tempo = più interesse, ma mai oltre 100)
        cat_df = pd.DataFrame([
            {"Categoria": cat, "Tempo (min)": secs / 60, "Punteggio Interesse": min(secs * 2, 100)}
            for cat, secs in cat_time.items()
        ]).sort_values("Punteggio Interesse", ascending=True)

        # Grafico a barre orizzontali con scala colori Viridis.
        # L'orientamento orizzontale (orientation="h") rende le etichette
        # delle categorie più leggibili.
        fig_bar = px.bar(
            cat_df,
            x="Punteggio Interesse",
            y="Categoria",
            orientation="h",
            color="Punteggio Interesse",
            color_continuous_scale="Viridis",
            labels={"Punteggio Interesse": "Livello Interesse"},
        )
        fig_bar.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",      # sfondo trasparente
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- Radar chart degli interessi ---
        # Necessita di almeno 3 vertici per formare un poligono sensato.
        # Scatterpolar con fill='toself' disegna un'area colorata
        # che rappresenta il "profilo" dell'utente.
        if len(cat_time) >= 3:
            st.subheader("🕸️ Mappa dei tuoi Interessi")
            categories_radar = list(cat_time.keys())
            values_radar = [min(cat_time[c] * 2, 100) for c in categories_radar]
            # Chiudi il poligono: il primo punto viene ripetuto alla fine
            values_radar.append(values_radar[0])
            categories_radar.append(categories_radar[0])

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values_radar,
                theta=categories_radar,
                fill='toself',
                fillcolor='rgba(52, 152, 219, 0.3)',   # azzurro semitrasparente
                line=dict(color='#3498db', width=2),
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=400,
                margin=dict(l=40, r=40, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        # L'utente non ha ancora esplorato categorie:
        # mostra un messaggio informativo che lo invita a navigare.
        st.info(
            "📈 Non hai ancora abbastanza dati di navigazione. "
            "Esplora le categorie e leggi articoli per vedere il tuo profilo AI!"
        )

    # --- Descrizione testuale del profilo ---
    # Delega la generazione di un "ritratto" testuale dell'utente
    # basato su like, dislike, tempo di permanenza ecc.
    st.subheader("🧬 Descrizione del tuo Profilo")
    _render_profile_description(prefs)

    st.markdown("---")

    # ===========================================================
    # SEZIONE 2: FONTI A PAGAMENTO
    # Scorre tutte le fonti del registro e filtra quelle con paid=True.
    # Per ciascuna mostra un checkbox: se attivato, la fonte viene
    # aggiunta a enabled_paid_sources e il recommender la includerà
    # nei risultati (altrimenti viene saltata).
    # ===========================================================
    st.header("💳 Fonti a Pagamento")
    st.caption("Di default solo le fonti gratuite sono attive. Attiva qui i tuoi abbonamenti.")

    # Raccogli tutte le fonti con paid=True dal registro.
    # Il registro può avere struttura dict-di-dict o dict-di-list,
    # quindi gestiamo entrambi i casi.
    paid_sources = []
    for category, source_list in sources.items():
        if isinstance(source_list, list):
            for s in source_list:
                if s.get("paid", False):
                    paid_sources.append((s["name"], category))
        elif isinstance(source_list, dict):
            for name, info in source_list.items():
                if info.get("paid", False):
                    paid_sources.append((name, category))

    if paid_sources:
        for name, cat in paid_sources:
            is_enabled = name in prefs["enabled_paid_sources"]
            # Ogni checkbox ha key unica "paid_{nome}" per evitare collisioni
            if st.checkbox(f"✅ {name} ({cat})", value=is_enabled, key=f"paid_{name}"):
                if name not in prefs["enabled_paid_sources"]:
                    prefs["enabled_paid_sources"].append(name)
            else:
                if name in prefs["enabled_paid_sources"]:
                    prefs["enabled_paid_sources"].remove(name)
    else:
        st.info("Nessuna fonte a pagamento trovata nel registro.")

    st.markdown("---")

    # ===========================================================
    # SEZIONE 3: FONTI PERSONALIZZATE
    # Un form Streamlit (st.form) raccoglie nome, categoria e URL
    # di un feed RSS che l'utente vuole aggiungere.
    # 
    # st.form raggruppa i widget e invia i dati solo quando si
    # preme il submit button, evitando rerun ad ogni keystroke.
    # clear_on_submit=True svuota i campi dopo l'invio.
    #
    # Il form ha key "add_custom_source_form" — deve essere unica
    # in tutta la pagina, altrimenti Streamlit lancia errore.
    # ===========================================================
    st.header("➕ Aggiungi Fonte Personalizzata")
    st.caption("Inserisci l'URL di un feed RSS/Atom di una fonte che vuoi aggiungere.")

    with st.form("add_custom_source_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            custom_name = st.text_input("Nome della fonte", placeholder="es. Il mio blog preferito")
        with col2:
            # Dropdown con tutte le categorie possibili + "Altro" come fallback
            custom_category = st.selectbox("Categoria", [
                "Notizie Generaliste", "Notizie Internazionali", "Tecnologia",
                "Scienza", "Economia e Finanza", "Sport", "Intrattenimento",
                "Salute e Benessere", "Viaggi e Lifestyle", "Politica",
                "Gaming", "Ambiente", "Auto e Motori", "Moda e Design",
                "Cucina e Food", "Meme e Humor", "Altro"
            ])
        custom_url = st.text_input("URL del feed RSS", placeholder="https://esempio.com/feed/rss")

        # Submit button — obbligatorio dentro st.form,
        # altrimenti Streamlit mostra "Missing Submit Button"
        submitted = st.form_submit_button("➕ Aggiungi Fonte")

        if submitted:
            if custom_name and custom_url:
                # Crea un dizionario con le info della nuova fonte
                new_source = {
                    "name": custom_name,
                    "url": custom_url,
                    "category": custom_category,
                    "type": "rss",
                    "paid": False,
                }
                if "custom_sources" not in st.session_state.user_preferences:
                    st.session_state.user_preferences["custom_sources"] = []
                # Aggiunge la fonte alla lista e forza un rerun
                # affinché la lista aggiornata venga visualizzata
                st.session_state.user_preferences["custom_sources"].append(new_source)
                st.success(f"✅ Fonte '{custom_name}' aggiunta!")
                st.rerun()
            else:
                st.error("Compila nome e URL.")

    # --- Lista fonti personalizzate già aggiunte ---
    # Per ciascuna mostra nome, categoria, URL e un bottone 🗑️ per rimuoverla.
    custom_sources = prefs.get("custom_sources", [])
    if custom_sources:
        st.markdown("**📡 Le tue fonti personalizzate:**")
        for i, cs in enumerate(custom_sources):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📡 **{cs['name']}** ({cs.get('category', 'Altro')}) — `{cs['url']}`")
            with col2:
                if st.button("🗑️", key=f"remove_custom_{i}"):
                    # Rimuove la fonte dall'indice i e forza rerun
                    prefs["custom_sources"].pop(i)
                    st.toast(f"Fonte '{cs['name']}' rimossa.")
                    st.rerun()

    st.markdown("---")

    # ===========================================================
    # SEZIONE 4: ESCLUDI FONTI
    # Elenca tutte le fonti (dal registro + custom) con un checkbox
    # per escluderle. Se esclusa, la fonte non apparirà nel feed.
    # Opzionalmente l'utente può specificare un motivo di esclusione,
    # salvato in excluded_reasons.
    # ===========================================================
    st.header("🚫 Escludi Fonti")
    st.caption("Seleziona le fonti che vuoi rimuovere dal tuo feed.")

    # Raccogli tutti i nomi delle fonti (registro + custom)
    all_source_names = []
    for category, source_list in sources.items():
        if isinstance(source_list, list):
            for s in source_list:
                all_source_names.append(s["name"])
        elif isinstance(source_list, dict):
            for name in source_list.keys():
                all_source_names.append(name)

    # Aggiungi anche le fonti personalizzate dell'utente
    for cs in custom_sources:
        all_source_names.append(cs["name"])

    excluded = prefs["excluded_sources"]

    for name in all_source_names:
        col1, col2 = st.columns([3, 2])
        is_excluded = name in excluded
        with col1:
            # Checkbox con key unica "excl_{nome}"
            # Se selezionato → aggiunge alla lista escluse
            # Se deselezionato → rimuove dalla lista
            if st.checkbox(f"❌ {name}", value=is_excluded, key=f"excl_{name}"):
                if name not in excluded:
                    excluded.append(name)
            else:
                if name in excluded:
                    excluded.remove(name)
        with col2:
            # Campo motivo visibile solo se la fonte è esclusa
            if name in excluded:
                reason = st.text_input(
                    "Motivo (opzionale)",
                    value=prefs["excluded_reasons"].get(name, ""),
                    key=f"reason_{name}"
                )
                prefs["excluded_reasons"][name] = reason

    # Salva la lista aggiornata nelle preferenze
    prefs["excluded_sources"] = excluded

    st.markdown("---")

    # ===========================================================
    # SEZIONE 5: RESET COMPLETO
    # Un unico bottone che ripristina tutte le preferenze ai valori
    # di default, cancellando like, dislike, esclusioni, fonti custom
    # e tempi di permanenza per categoria.
    # ===========================================================
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🗑️ Reset Tutte le Preferenze", type="secondary", use_container_width=True):
            st.session_state.user_preferences = {
                "likes": [], "dislikes": [], "excluded_sources": [],
                "excluded_reasons": {}, "category_time": {},
                "enabled_paid_sources": [], "custom_sources": []
            }
            st.toast("Preferenze resettate!")
            st.rerun()


def _render_profile_description(prefs):
    """
    Genera e visualizza una descrizione testuale del profilo utente.
    
    Analizza le preferenze per determinare:
    - Livello di engagement (da "Nuovo utente" a "Maestro dei Feed")
      basato sul numero totale di interazioni (like + dislike)
    - Umore del feed (positivo/equilibrato/selettivo/critico)
      basato sul rapporto like/dislike
    - Categoria preferita (quella con più tempo di permanenza)
    - Conteggi di fonti personalizzate e fonti escluse
    
    Il risultato viene mostrato come un card HTML con sfondo scuro
    e gradiente, usando st.markdown con unsafe_allow_html=True.
    
    Args:
        prefs (dict): Dizionario delle preferenze utente da session_state.
    """
    cat_time = prefs.get("category_time", {})
    likes_count = len(prefs.get("likes", []))
    dislikes_count = len(prefs.get("dislikes", []))
    excluded_count = len(prefs.get("excluded_sources", []))
    custom_count = len(prefs.get("custom_sources", []))

    # Trova la categoria con più tempo di permanenza
    if cat_time:
        top_cat = max(cat_time, key=cat_time.get)
        top_time = cat_time[top_cat]
    else:
        top_cat = None
        top_time = 0

    # Determina il livello di engagement in base alle interazioni totali.
    # Più interazioni = utente più attivo = algoritmo più preciso.
    total_interactions = likes_count + dislikes_count
    if total_interactions == 0:
        engagement = "Nuovo utente"
        emoji = "🌱"
        desc = "Non hai ancora interagito con nessun articolo. Inizia a esplorare!"
    elif total_interactions < 10:
        engagement = "Esploratore"
        emoji = "🔭"
        desc = "Stai iniziando a scoprire i tuoi interessi."
    elif total_interactions < 30:
        engagement = "Lettore Attivo"
        emoji = "📖"
        desc = "L'algoritmo sta imparando i tuoi gusti."
    elif total_interactions < 100:
        engagement = "Power User"
        emoji = "⚡"
        desc = "Il tuo feed è molto personalizzato."
    else:
        engagement = "Maestro dei Feed"
        emoji = "🏆"
        desc = "L'AI ti conosce molto bene!"

    # Determina l'"umore" del feed basato sul rapporto like/totale.
    # Un utente con 90% like è "positivo", uno con 20% like è "critico".
    if total_interactions > 0:
        like_ratio = likes_count / total_interactions * 100
        if like_ratio > 80:
            mood = "😊 Molto positivo — ti piace quasi tutto!"
        elif like_ratio > 50:
            mood = "🙂 Equilibrato — sai cosa ti piace."
        elif like_ratio > 20:
            mood = "🤔 Selettivo — hai gusti precisi."
        else:
            mood = "😤 Critico — poche cose ti convincono."
    else:
        mood = "❓ Non ancora definito"

    # Renderizza il card HTML con tutte le informazioni raccolte.
    # Le righe opzionali (categoria preferita, fonti custom, escluse)
    # vengono mostrate solo se i dati sono disponibili, usando
    # l'operatore ternario inline di Python nelle f-string.
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 15px;
        padding: 25px;
        color: white;
        margin: 10px 0 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    ">
        <h3 style="color: #4fc3f7; margin-top: 0;">{emoji} Livello: {engagement}</h3>
        <p style="color: #ccc;">{desc}</p>
        <hr style="border-color: rgba(255,255,255,0.1);">
        <p>🎯 <b>Umore del feed:</b> {mood}</p>
        <p>📊 <b>Interazioni totali:</b> {total_interactions} (👍 {likes_count} / 👎 {dislikes_count})</p>
        {"<p>🏅 <b>Categoria preferita:</b> " + top_cat + f" ({top_time/60:.1f} min)</p>" if top_cat else ""}
        {"<p>📡 <b>Fonti personalizzate:</b> " + str(custom_count) + "</p>" if custom_count > 0 else ""}
        {"<p>🚫 <b>Fonti escluse:</b> " + str(excluded_count) + "</p>" if excluded_count > 0 else ""}
    </div>
    """, unsafe_allow_html=True)


def main():
    """Entry point per esecuzione diretta del modulo (debug/test)."""
    preferences_page()


if __name__ == "__main__":
    main()