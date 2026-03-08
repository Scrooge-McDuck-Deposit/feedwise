"""
Modulo RecommenderAgent — cuore dell'aggregatore di notizie.

Architettura a 3 fasi:
  1. FETCH   → scarica gli articoli da tutti i feed RSS configurati
  2. SCORE   → calcola un punteggio di tendenza per ogni articolo
  3. FILTER  → filtra per query, esclusioni, dislike e restituisce i risultati

Contiene anche:
  - CATEGORY_IMAGES: immagini Unsplash di fallback per categoria
  - MEME_SOURCES: subreddit RSS per la sezione Brainless
  - Metodi per estrazione immagini, autore e formattazione date dai feed RSS
"""
import pandas as pd
import feedparser
import hashlib
import random
import re
from datetime import datetime


# ── Immagini di fallback per categoria ───────────────────────────────
# Quando un articolo RSS non ha immagine incorporata, viene usata
# l'immagine Unsplash corrispondente alla sua categoria.
# Le URL usano parametri Unsplash (w=600, h=300, fit=crop) per
# ottenere immagini ottimizzate senza bisogno di resize lato client.
CATEGORY_IMAGES = {
    "Notizie Generaliste": "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=600&h=300&fit=crop",
    "Notizie Internazionali": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=300&fit=crop",
    "Tecnologia": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=300&fit=crop",
    "Scienza": "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=600&h=300&fit=crop",
    "Economia e Finanza": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&h=300&fit=crop",
    "Sport": "https://images.unsplash.com/photo-1461896836934-bd45ba8a64e0?w=600&h=300&fit=crop",
    "Intrattenimento": "https://images.unsplash.com/photo-1603190287605-e6ade32fa852?w=600&h=300&fit=crop",
    "Salute e Benessere": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=600&h=300&fit=crop",
    "Viaggi e Lifestyle": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=600&h=300&fit=crop",
    "Politica": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600&h=300&fit=crop",
    "Gaming": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600&h=300&fit=crop",
    "Ambiente": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&h=300&fit=crop",
    "Auto e Motori": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=600&h=300&fit=crop",
    "Moda e Design": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&h=300&fit=crop",
    "Cucina e Food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&h=300&fit=crop",
    "Meme e Humor": "https://images.unsplash.com/photo-1531259683007-016a7b628fc3?w=600&h=300&fit=crop",
}

# ── Fonti meme da Reddit ─────────────────────────────────────────────
# Reddit espone un feed RSS per ogni subreddit aggiungendo .rss all'URL.
# Questi subreddit sono scelti per avere contenuti prevalentemente
# image-based (meme con immagine), che vengono estratti dal parser.
MEME_SOURCES = [
    {"url": "https://www.reddit.com/r/memes/.rss", "name": "memes"},
    {"url": "https://www.reddit.com/r/dankmemes/.rss", "name": "dankmemes"},
    {"url": "https://www.reddit.com/r/me_irl/.rss", "name": "me_irl"},
    {"url": "https://www.reddit.com/r/wholesomememes/.rss", "name": "wholesomememes"},
    {"url": "https://www.reddit.com/r/ProgrammerHumor/.rss", "name": "ProgrammerHumor"},
    {"url": "https://www.reddit.com/r/funny/.rss", "name": "funny"},
    {"url": "https://www.reddit.com/r/comics/.rss", "name": "comics"},
    {"url": "https://www.reddit.com/r/memes_of_the_dank/.rss", "name": "memes_of_the_dank"},
]


class RecommenderAgent:
    """
    Agente raccomandatore di notizie RSS.
    
    Scarica articoli da fonti RSS, calcola punteggi di tendenza
    basati sulle preferenze dell'utente, e restituisce risultati
    filtrati e ordinati.
    
    Attributi:
        sources (dict): Fonti RSS dal SourceRegistry
        user_preferences (dict): Preferenze utente da session_state
        _article_cache (DataFrame|None): Cache articoli per evitare
            download multipli nella stessa sessione Streamlit.
    """

    def __init__(self, sources, user_preferences=None):
        """
        Inizializza l'agente.
        
        Args:
            sources (dict): Dizionario {categoria: {nome: {url, type, paid}}}
            user_preferences (dict, optional): Preferenze utente. Se None,
                usa valori di default (nessun like/dislike/esclusione).
        """
        self.sources = sources
        self.user_preferences = user_preferences or {
            "likes": [], "dislikes": [], "excluded_sources": [],
            "excluded_reasons": {}, "category_time": {},
            "enabled_paid_sources": [], "custom_sources": []
        }
        self._article_cache = None

    def _extract_image_from_entry(self, entry):
        """
        Estrai l'URL dell'immagine principale da un entry RSS.
        
        Cerca in ordine di priorità:
        1. media:content      — standard Media RSS (usato da molti feed)
        2. media:thumbnail    — miniatura Media RSS
        3. enclosures         — allegati con type "image/*"
        4. <img> nel summary  — cerca tag img nell'HTML del riassunto
        5. links con type img — link tipizzati come immagine
        
        Args:
            entry: Oggetto entry di feedparser
            
        Returns:
            str: URL dell'immagine, o stringa vuota se non trovata
        """
        # 1. media:content — campo più affidabile per immagini HD
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                url = media.get("url", "")
                if url and self._is_image_url(url):
                    return url

        # 2. media:thumbnail — spesso presente anche quando media_content no
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                url = thumb.get("url", "")
                if url:
                    return url

        # 3. Enclosures — usate da podcast e blog per allegati binari
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href", "")

        # 4. Cerca <img src="..."> nell'HTML del summary/content
        content = entry.get("summary", "") or ""
        if hasattr(entry, "content") and entry.content:
            content += entry.content[0].get("value", "")
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if img_match:
            img_url = img_match.group(1)
            if img_url.startswith("http"):
                return img_url

        # 5. Link con type image nel feed
        if hasattr(entry, "links"):
            for link in entry.links:
                if "image" in link.get("type", ""):
                    return link.get("href", "")

        return ""

    def _is_image_url(self, url):
        """
        Verifica se un URL punta probabilmente a un'immagine.
        
        Controlla l'estensione del file (ignorando query string)
        e la presenza della parola "image" nell'URL.
        
        Args:
            url (str): URL da verificare
            
        Returns:
            bool: True se sembra un'immagine
        """
        image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
        url_lower = url.lower().split('?')[0]  # Rimuove query string
        return any(url_lower.endswith(ext) for ext in image_exts) or 'image' in url_lower

    def _extract_author(self, entry):
        """
        Estrai il nome dell'autore da un entry RSS.
        
        Cerca in ordine:
        1. entry.author        — campo stringa diretto
        2. entry.author_detail — oggetto con campo "name" (Atom)
        3. entry.authors       — lista di autori (RSS con dc:creator multipli)
        
        I tag HTML vengono rimossi dal risultato (alcuni feed
        inseriscono link nell'autore, es. "<a href='...'>Mario Rossi</a>").
        
        Args:
            entry: Oggetto entry di feedparser
            
        Returns:
            str: Nome dell'autore, o stringa vuota se non trovato
        """
        # Campo stringa semplice (più comune)
        author = entry.get("author", "")
        if author:
            return re.sub(r'<[^>]+>', '', author).strip()

        # Oggetto author_detail (formato Atom)
        if hasattr(entry, "author_detail") and entry.author_detail:
            name = entry.author_detail.get("name", "")
            if name:
                return name

        # Lista autori (articoli con più firme)
        if hasattr(entry, "authors") and entry.authors:
            names = [a.get("name", "") for a in entry.authors if a.get("name")]
            if names:
                return ", ".join(names)

        return ""

    def _format_date(self, date_str):
        """
        Converte una data RSS in formato leggibile "dd Mmm YYYY, HH:MM".
        
        I feed RSS usano formati data eterogenei (RFC 822, ISO 8601, ecc.).
        Questa funzione prova i formati più comuni in ordine e restituisce
        la data formattata. Se nessun formato corrisponde, tronca la
        stringa originale come fallback.
        
        Args:
            date_str (str): Data grezza dal feed RSS
            
        Returns:
            str: Data formattata (es. "08 Mar 2026, 14:30") o stringa vuota
        """
        if not date_str:
            return ""

        # Formati da provare, ordinati dal più al meno comune nei feed RSS
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",    # RFC 822 con timezone (RSS 2.0)
            "%a, %d %b %Y %H:%M:%S %Z",    # RFC 822 con timezone abbreviata
            "%Y-%m-%dT%H:%M:%S%z",          # ISO 8601 con timezone (Atom)
            "%Y-%m-%dT%H:%M:%SZ",           # ISO 8601 UTC (Z = Zulu)
            "%Y-%m-%d %H:%M:%S",            # Formato semplice senza timezone
            "%Y-%m-%d",                      # Solo data, senza ora
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%d %b %Y, %H:%M")
            except ValueError:
                continue

        # Fallback: restituisci i primi 25 caratteri della stringa grezza
        return date_str[:25]

    def fetch_articles_from_rss(self, max_per_source=8):
        """
        Scarica articoli da tutti i feed RSS configurati.
        
        Per ogni fonte nel registro:
        1. Controlla se è paid e non abilitata → skip
        2. Controlla se è esclusa dall'utente → skip
        3. Scarica il feed con feedparser
        4. Estrae fino a max_per_source articoli
        5. Per ogni articolo estrai: titolo, link, immagine, riassunto,
           data, autore
        
        Poi elabora anche le fonti custom dell'utente con la stessa logica.
        
        I risultati vengono salvati in _article_cache per evitare
        download multipli nella stessa sessione Streamlit.
        
        Args:
            max_per_source (int): Max articoli per fonte (default 8).
                Valore basso per bilanciare varietà vs velocità.
        
        Returns:
            DataFrame: Colonne [id, title, link, source, category,
                       image, summary, published, author, paid]
        """
        # Ritorna la cache se già scaricato in questa sessione
        if self._article_cache is not None:
            return self._article_cache.copy()

        articles = []

        # ── Fonti dal registro ──
        for category, source_dict in self.sources.items():
            # Il registro può avere struttura dict-di-dict o dict-di-list
            if isinstance(source_dict, dict):
                items = list(source_dict.items())
            elif isinstance(source_dict, list):
                items = [(s.get("name", "Unknown"), s) for s in source_dict]
            else:
                continue

            for name, info in items:
                if not isinstance(info, dict):
                    continue

                url = info.get("url", "")
                is_paid = info.get("paid", False)

                # Fonti premium: scarica solo se l'utente le ha abilitate
                if is_paid and name not in self.user_preferences.get("enabled_paid_sources", []):
                    continue

                # Fonti escluse: l'utente ha scelto di non vederle
                if name in self.user_preferences.get("excluded_sources", []):
                    continue

                if not url:
                    continue

                try:
                    # feedparser.parse() fa la richiesta HTTP e parsa XML/Atom
                    feed = feedparser.parse(url)

                    for entry in feed.entries[:max_per_source]:
                        # ID univoco: hash MD5 di link+titolo per evitare duplicati
                        article_id = hashlib.md5(
                            (entry.get("link", "") + entry.get("title", "")).encode()
                        ).hexdigest()

                        # Estrai immagine, con fallback su immagine della categoria
                        image = self._extract_image_from_entry(entry)
                        if not image:
                            image = CATEGORY_IMAGES.get(str(category), "")

                        # Rimuovi HTML dal riassunto e tronca a 200 caratteri
                        summary_raw = entry.get("summary", "")[:500]
                        summary = re.sub(r'<[^>]+>', '', summary_raw).strip()[:200]

                        # Formatta la data di pubblicazione
                        pub_raw = entry.get("published", "")
                        pub_formatted = self._format_date(pub_raw)

                        articles.append({
                            "id": article_id,
                            "title": entry.get("title", "Senza titolo"),
                            "link": entry.get("link", "#"),
                            "source": str(name),
                            "category": str(category),
                            "image": image,
                            "summary": summary,
                            "published": pub_formatted,
                            "author": self._extract_author(entry),
                            "paid": is_paid,
                        })
                except Exception:
                    # Fonte irraggiungibile o XML malformato → ignora
                    continue

        # ── Fonti personalizzate dell'utente ──
        # Stessa logica delle fonti dal registro, ma lette da user_preferences
        for custom in self.user_preferences.get("custom_sources", []):
            if custom.get("name") in self.user_preferences.get("excluded_sources", []):
                continue
            try:
                feed = feedparser.parse(custom["url"])
                for entry in feed.entries[:max_per_source]:
                    article_id = hashlib.md5(
                        (entry.get("link", "") + entry.get("title", "")).encode()
                    ).hexdigest()

                    image = self._extract_image_from_entry(entry)
                    if not image:
                        image = CATEGORY_IMAGES.get(custom.get("category", ""), "")

                    summary_raw = entry.get("summary", "")[:500]
                    summary = re.sub(r'<[^>]+>', '', summary_raw).strip()[:200]

                    pub_raw = entry.get("published", "")
                    pub_formatted = self._format_date(pub_raw)

                    articles.append({
                        "id": article_id,
                        "title": entry.get("title", "Senza titolo"),
                        "link": entry.get("link", "#"),
                        "source": custom.get("name", "Custom"),
                        "category": custom.get("category", "Altro"),
                        "image": image,
                        "summary": summary,
                        "published": pub_formatted,
                        "author": self._extract_author(entry),
                        "paid": False,
                    })
            except Exception:
                continue

        # Salva in cache come DataFrame per query successive
        df = pd.DataFrame(articles)
        self._article_cache = df
        return df

    def calculate_trend_score(self, df):
        """
        Calcola il punteggio di tendenza per ogni articolo.
        
        Il punteggio parte da 50 (baseline) e viene modificato da:
        - Tempo in categoria: +2 per secondo, max +30
          (premia le categorie che l'utente esplora di più)
        - Like dell'utente: +20 punti
          (l'utente ha espresso interesse esplicito)
        - Dislike dell'utente: -30 punti
          (penalizzazione più forte del bonus like)
        - Random: +0-20 punti
          (elemento di serendipità per evitare filter bubble)
        
        Aggiunge anche un campo "interactions" simulato per l'UI.
        
        Args:
            df (DataFrame): Articoli da valutare
            
        Returns:
            DataFrame: Stessa struttura con colonne trend_score e interactions aggiunte
        """
        if df.empty:
            return df

        df = df.copy()
        df["trend_score"] = 50.0
        df["interactions"] = 0

        cat_time = self.user_preferences.get("category_time", {})
        likes = self.user_preferences.get("likes", [])
        dislikes = self.user_preferences.get("dislikes", [])

        for idx, row in df.iterrows():
            score = 50.0

            # Seed deterministica per articolo (stesso articolo = stesso bonus)
            article_hash = int(hashlib.md5(
                (row.get("title", "") + row.get("source", "")).encode()
            ).hexdigest()[:8], 16)
            rng = random.Random(article_hash)

            # Bonus basato sulla fonte (alcune fonti producono contenuti più virali)
            source_bonus = rng.uniform(-8, 15)
            score += source_bonus

            # Bonus lunghezza riassunto (articoli più dettagliati)
            summary = row.get("summary", "") or ""
            if len(summary) > 150:
                score += rng.uniform(3, 10)
            elif len(summary) > 80:
                score += rng.uniform(1, 5)

            # Bonus recenza dalla data di pubblicazione
            pub = row.get("published", "")
            if pub:
                recency_bonus = rng.uniform(2, 12)
                score += recency_bonus

            # Bonus per titoli "forti" (lunghezza e keywords)
            title = row.get("title", "")
            if len(title) > 60:
                score += rng.uniform(2, 8)
            elif len(title) > 30:
                score += rng.uniform(0, 4)

            interactions = rng.randint(50, 800)

            # Boost per categorie con tempo di permanenza
            if row["category"] in cat_time:
                score += min(cat_time[row["category"]] * 2, 30)
                interactions += int(cat_time[row["category"]] * 10)

            # Boost/penalizzazione per like/dislike
            if row["id"] in likes:
                score += 20
                interactions += 100
            if row["id"] in dislikes:
                score -= 30

            # Componente casuale leggero
            score += rng.uniform(0, 8)

            # Clamp tra 1 e 100
            df.at[idx, "trend_score"] = max(min(score, 100), 1)
            df.at[idx, "interactions"] = max(interactions, 1)

        return df

    def get_recommendations(self, query="", max_results=10):
        """
        Restituisce articoli raccomandati, filtrati e ordinati per trend.
        
        Pipeline:
        1. Scarica tutti gli articoli (o usa cache)
        2. Se c'è una query → filtra per corrispondenza nel titolo,
           riassunto, categoria o fonte
        3. Rimuovi fonti escluse e articoli con dislike
        4. Calcola trend score
        5. Ordina per trend score decrescente
        6. Restituisci i primi max_results
        
        Args:
            query (str): Termine di ricerca (vuoto = tutti gli articoli)
            max_results (int): Numero massimo di risultati
            
        Returns:
            DataFrame: Articoli ordinati per trend_score decrescente
        """
        df = self.fetch_articles_from_rss()
        if df.empty:
            return df

        # Filtro ricerca testuale (case-insensitive)
        if query and query.strip():
            q = re.escape(query.strip())  # Escape regex special chars
            mask = (
                df["title"].str.contains(q, case=False, na=False) |
                df["summary"].str.contains(q, case=False, na=False) |
                df["category"].str.contains(q, case=False, na=False) |
                df["source"].str.contains(q, case=False, na=False)
            )
            df = df[mask]

        if df.empty:
            return df

        # Rimuovi fonti escluse
        excluded = self.user_preferences.get("excluded_sources", [])
        if excluded:
            df = df[~df["source"].isin(excluded)]

        # Rimuovi articoli con dislike
        dislikes = self.user_preferences.get("dislikes", [])
        if dislikes:
            df = df[~df["id"].isin(dislikes)]

        # Calcola punteggi e ordina
        df = self.calculate_trend_score(df)
        df = df.sort_values("trend_score", ascending=False)

        return df.head(max_results).reset_index(drop=True)

    def get_articles_by_category(self, category, max_results=20):
        """
        Restituisce articoli di una specifica categoria.
        
        Usa match esatto prima; se non trova risultati, prova
        match parziale (case-insensitive) come fallback per gestire
        differenze di spazi o capitalizzazione.
        
        Args:
            category (str): Nome categoria (es. "Tecnologia")
            max_results (int): Max articoli da restituire
            
        Returns:
            DataFrame: Articoli della categoria, ordinati per trend_score
        """
        df = self.fetch_articles_from_rss()
        if df.empty:
            return df

        cat_str = str(category).strip()

        # Tentativo 1: match esatto
        mask = df["category"].str.strip() == cat_str
        if mask.sum() == 0:
            # Tentativo 2: match parziale (substring case-insensitive)
            cat_escaped = re.escape(cat_str)
            mask = df["category"].str.contains(cat_escaped, case=False, na=False)

        df = df[mask]
        if df.empty:
            return df

        df = self.calculate_trend_score(df)
        df = df.sort_values("trend_score", ascending=False)

        return df.head(max_results).reset_index(drop=True)

    def get_articles_by_sources(self, source_names, max_results=20):
        """
        Restituisce articoli filtrati per una lista di fonti specifiche.

        Usato dalle sezioni personalizzate dell'utente.

        Args:
            source_names (list): Lista di nomi fonti da includere
            max_results (int): Max articoli da restituire

        Returns:
            DataFrame: Articoli delle fonti selezionate, ordinati per trend_score
        """
        df = self.fetch_articles_from_rss()
        if df.empty:
            return df

        df = df[df["source"].isin(source_names)]
        if df.empty:
            return df

        excluded = self.user_preferences.get("excluded_sources", [])
        if excluded:
            df = df[~df["source"].isin(excluded)]

        dislikes = self.user_preferences.get("dislikes", [])
        if dislikes:
            df = df[~df["id"].isin(dislikes)]

        df = self.calculate_trend_score(df)
        df = df.sort_values("trend_score", ascending=False)

        return df.head(max_results).reset_index(drop=True)

    def get_total_articles_count(self, category=None):
        """
        Conta il numero totale di articoli disponibili.
        
        Usato per mostrare "Carica altri (X/Y)" nei bottoni di paginazione.
        
        Args:
            category (str, optional): Se specificato, conta solo quella categoria
            
        Returns:
            int: Numero totale di articoli
        """
        df = self.fetch_articles_from_rss()
        if df.empty:
            return 0
        if category:
            cat_str = str(category).strip()
            mask = df["category"].str.strip() == cat_str
            if mask.sum() == 0:
                cat_escaped = re.escape(cat_str)
                mask = df["category"].str.contains(cat_escaped, case=False, na=False)
            return int(mask.sum())
        return len(df)

    def get_meme_feed(self, max_results=20):
        """
        Scarica meme da subreddit Reddit tramite feed RSS.
        
        Per ogni subreddit in MEME_SOURCES:
        1. Scarica il feed RSS
        2. Per ogni entry, cerca URL di immagini nel contenuto HTML
        3. Filtra via thumbnail, avatar, icone e altre immagini inutili
        4. Preferisce immagini da i.redd.it (hosting nativo Reddit)
        5. Aggiunge solo entry che hanno almeno un'immagine
        
        I risultati vengono mescolati casualmente per varietà.
        
        Args:
            max_results (int): Max meme da restituire
            
        Returns:
            list: Lista di dict {id, title, link, image, source}
        """
        memes = []

        for source in MEME_SOURCES:
            try:
                feed = feedparser.parse(source["url"])
                for entry in feed.entries:
                    # Raccogli tutto il contenuto HTML dell'entry
                    content = entry.get("summary", "") or ""
                    if hasattr(entry, "content") and entry.content:
                        for c in entry.content:
                            content += c.get("value", "")

                    # Cerca URL con estensioni immagine nel testo
                    img_urls = re.findall(
                        r'https?://[^\s"\'<>\)]+\.(?:jpg|jpeg|png|gif|webp)(?:\?[^\s"\'<>\)]*)?',
                        content, re.IGNORECASE
                    )

                    # Cerca anche nei tag <img src="...">
                    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
                    for tag_url in img_tags:
                        if tag_url.startswith("http") and tag_url not in img_urls:
                            img_urls.append(tag_url)

                    # Cerca in media:content
                    if hasattr(entry, "media_content") and entry.media_content:
                        for media in entry.media_content:
                            u = media.get("url", "")
                            if u and u not in img_urls:
                                img_urls.append(u)

                    # Filtra immagini inutili (avatar, icone, badge, ecc.)
                    filtered = []
                    for u in img_urls:
                        u_lower = u.lower()
                        if any(skip in u_lower for skip in [
                            "thumb", "avatar", "icon", "emoji", "award",
                            "pixel", "1x1", "spacer", "blank", "badge"
                        ]):
                            continue
                        filtered.append(u)

                    # Ordina: immagini Reddit native prima (più affidabili)
                    filtered.sort(key=lambda u: (
                        0 if "i.redd.it" in u or "preview.redd.it" in u else 1
                    ))

                    # Aggiungi solo se c'è almeno un'immagine valida
                    if filtered:
                        article_id = hashlib.md5(
                            (entry.get("link", "") + entry.get("title", "")).encode()
                        ).hexdigest()

                        # Rimuovi HTML dal titolo
                        title = entry.get("title", "")
                        title = re.sub(r'<[^>]+>', '', title).strip()

                        memes.append({
                            "id": article_id,
                            "title": title,
                            "link": entry.get("link", "#"),
                            "image": filtered[0],   # Prima immagine (la migliore)
                            "source": source["name"],
                        })
            except Exception:
                # Subreddit irraggiungibile o rate-limited → ignora
                continue

        # Mescola per varietà (evita di mostrare tutti i meme della stessa fonte)
        random.shuffle(memes)
        return memes[:max_results]

    def update_preference(self, article_id, action):
        """
        Aggiorna le preferenze dell'utente per un articolo.
        
        Il like e il dislike sono mutuamente esclusivi:
        - Like → aggiunge a likes, rimuove da dislikes
        - Dislike → aggiunge a dislikes, rimuove da likes
        
        Args:
            article_id (str): Hash MD5 dell'articolo
            action (str): "like" o "dislike"
        """
        if action == "like":
            if article_id not in self.user_preferences["likes"]:
                self.user_preferences["likes"].append(article_id)
            if article_id in self.user_preferences["dislikes"]:
                self.user_preferences["dislikes"].remove(article_id)
        elif action == "dislike":
            if article_id not in self.user_preferences["dislikes"]:
                self.user_preferences["dislikes"].append(article_id)
            if article_id in self.user_preferences["likes"]:
                self.user_preferences["likes"].remove(article_id)