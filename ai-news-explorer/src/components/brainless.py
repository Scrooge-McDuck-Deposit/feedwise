"""
Componente Brainless — feed meme con auto-scroll.

Mostra meme da subreddit Reddit in un layout ispirato a Instagram:
- Header con avatar e nome subreddit
- Immagine del meme (cliccabile → apre su Reddit)
- Footer con azioni e titolo
- Auto-load via JavaScript IntersectionObserver quando
  l'utente arriva in fondo alla pagina

L'auto-scroll funziona iniettando uno script JS tramite
streamlit.components.v1.html che:
1. Crea un elemento "sentinel" invisibile in fondo alla pagina
2. Un IntersectionObserver monitora quando il sentinel diventa visibile
3. Quando diventa visibile, clicca programmaticamente il bottone
   "Carica altri meme" di Streamlit, che incrementa il contatore
   e fa rerun
"""
import streamlit as st
import streamlit.components.v1 as stc
from agent.recommender import RecommenderAgent
from feeds.source_registry import load_sources


def brainless_page():
    """
    Renderizza il feed meme con layout Instagram-like e auto-scroll.
    
    Flusso:
    1. Inietta CSS per le card meme (stile social media)
    2. Carica i meme dal RecommenderAgent (scaricati da Reddit RSS)
    3. Per ogni meme renderizza una card HTML con header/image/footer
    4. Inietta JavaScript per auto-load al raggiungimento del fondo
    5. Mostra bottone "Carica altri meme" (cliccabile anche manualmente)
    
    Il contatore brainless_count in session_state traccia quanti
    meme caricare. Ad ogni "load more" viene incrementato di 10.
    """
    st.title("🧠 Brainless Mode")
    st.caption("Scroll infinito di meme. Rilassati e scorri.")

    # ── CSS card meme ─────────────────────────────────
    # Layout ispirato a Instagram:
    # - Container con bordo arrotondato e sfondo scuro
    # - Header con avatar gradiente (come IG Stories) e nome subreddit
    # - Immagine centrata con sfondo nero e object-fit: contain
    # - Footer con icone azione e titolo del post
    st.markdown("""
    <style>
    /* Container principale del meme (max 500px, centrato) */
    .meme-container {
        max-width: 500px;
        margin: 0 auto 22px auto;
        background: #111827;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 6px 24px rgba(0,0,0,.35);
        border: 1px solid rgba(255,255,255,.05);
        transition: transform .2s ease;
    }
    .meme-container:hover { transform: translateY(-3px); }

    /* Header con avatar e nome (stile Instagram) */
    .meme-header {
        display: flex; align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255,255,255,.06);
    }

    /* Avatar circolare con gradiente Instagram (arancio→rosa→viola) */
    .meme-avatar {
        width: 38px; height: 38px; border-radius: 50%;
        background: linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 16px; font-weight: 700; margin-right: 12px;
    }

    .meme-src-name { font-weight: 700; font-size: .9rem; color: #e2e8f0; }
    .meme-src-sub  { font-size: .72rem; color: #64748b; }

    /* Wrapper immagine con sfondo nero per meme non quadrati */
    .meme-img-wrap {
        width: 100%; background: #0a0f1a;
        display: flex; justify-content: center; min-height: 200px;
    }
    /* Immagine: contiene (non ritaglia) per mostrare il meme intero */
    .meme-img-wrap img {
        width: 100%; max-height: 650px; object-fit: contain; cursor: pointer;
    }

    /* Footer con azioni e titolo */
    .meme-footer { padding: 14px 16px; }
    .meme-actions { display: flex; gap: 16px; margin-bottom: 8px; font-size: 22px; }
    .meme-actions a {
        text-decoration: none; color: #e2e8f0;
        transition: transform .2s;
    }
    .meme-actions a:hover { transform: scale(1.25); }

    .meme-title {
        font-size: .88rem; color: #cbd5e1;
        margin: 0; line-height: 1.5;
    }

    /* Link "Apri su Reddit" */
    .meme-link {
        display: inline-block; margin-top: 8px;
        font-size: .82rem; color: #64ffda;
        text-decoration: none; font-weight: 600;
    }
    .meme-link:hover { text-decoration: underline; }
    </style>
    """, unsafe_allow_html=True)

    # Crea l'agente per scaricare i meme
    sources = load_sources()
    recommender = RecommenderAgent(sources, st.session_state.user_preferences)

    # Contatore meme: parte da 10, incrementa di 10 ad ogni "load more"
    if "brainless_count" not in st.session_state:
        st.session_state.brainless_count = 10

    with st.spinner("🔄 Caricamento meme…"):
        memes = recommender.get_meme_feed(max_results=st.session_state.brainless_count)

    if not memes:
        st.warning("😕 Nessun meme trovato. Reddit potrebbe limitare le richieste.")
        if st.button("🔄 Riprova", use_container_width=True):
            st.rerun()
        return

    st.success(f"🎉 {len(memes)} meme caricati!")

    # ── Renderizza ogni meme come card Instagram-like ──
    for meme in memes:
        src = meme.get("source", "unknown")
        initial = src[0].upper() if src else "?"  # Prima lettera per avatar

        # Sanitizza il titolo per attributi HTML (previene XSS)
        title = meme.get("title", "").replace('"', '&quot;').replace("'", "&#39;")
        short = (title[:120] + "…") if len(title) > 120 else title

        st.markdown(f"""
        <div class="meme-container">
            <div class="meme-header">
                <div class="meme-avatar">{initial}</div>
                <div>
                    <div class="meme-src-name">r/{src}</div>
                    <div class="meme-src-sub">Reddit · Meme</div>
                </div>
            </div>
            <div class="meme-img-wrap">
                <a href="{meme['link']}" target="_blank">
                    <img src="{meme['image']}" alt="{short}" loading="lazy"
                         onerror="this.parentElement.parentElement.innerHTML=
                         '<p style=\\'padding:40px;text-align:center;color:#64748b;\\'>🖼️ Immagine non disponibile</p>'">
                </a>
            </div>
            <div class="meme-footer">
                <div class="meme-actions">
                    <a href="{meme['link']}" target="_blank">❤️</a>
                    <a href="{meme['link']}" target="_blank">💬</a>
                    <a href="{meme['link']}" target="_blank">📤</a>
                </div>
                <p class="meme-title"><b>r/{src}</b> {short}</p>
                <a class="meme-link" href="{meme['link']}" target="_blank">Apri su Reddit ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Auto-scroll con IntersectionObserver ──────────
    # Inietta JavaScript che:
    # 1. Crea un div "sentinel" invisibile (1px) in fondo al container Streamlit
    # 2. Un IntersectionObserver lo monitora
    # 3. Quando l'utente scrolla fino al sentinel (diventa visibile),
    #    lo script cerca il bottone "Carica altri meme" e lo clicca
    # 4. Il click del bottone incrementa brainless_count e fa st.rerun()
    #
    # Il setTimeout(1500ms) dà tempo a Streamlit di renderizzare il DOM.
    # L'observer si disconnette dopo il click per evitare loop infiniti.
    stc.html("""
    <script>
    const SENTINEL_ID = 'brainless-sentinel';
    // Rimuovi sentinel precedenti (da rerun precedenti)
    const old = parent.document.getElementById(SENTINEL_ID);
    if (old) old.remove();

    // Crea sentinel invisibile (1px di altezza)
    const sentinel = document.createElement('div');
    sentinel.id = SENTINEL_ID;
    sentinel.style.height = '1px';

    // Inserisci alla fine del container principale Streamlit
    // (parent.document perché lo script è in un iframe)
    const main = parent.document.querySelector('section.main .block-container');
    if (main) main.appendChild(sentinel);

    // IntersectionObserver: trigga quando il sentinel entra nel viewport
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Cerca il bottone Streamlit con testo "Carica altri meme"
                const buttons = parent.document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.innerText.includes('Carica altri meme')) {
                        btn.click();           // Simula il click
                        observer.disconnect(); // Evita doppi trigger
                        break;
                    }
                }
            }
        });
    }, { threshold: 0.1 });  // Trigga quando il 10% del sentinel è visibile

    // Attendi che il DOM sia pronto prima di osservare
    setTimeout(() => {
        const el = parent.document.getElementById(SENTINEL_ID);
        if (el) observer.observe(el);
    }, 1500);
    </script>
    """, height=0)  # height=0: l'iframe JS è invisibile

    # Bottone "Carica altri meme" — cliccabile manualmente
    # e anche programmaticamente dal JS sopra.
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("⬇️ Carica altri meme", use_container_width=True,
                      key="load_more_memes"):
            st.session_state.brainless_count += 10
            st.rerun()