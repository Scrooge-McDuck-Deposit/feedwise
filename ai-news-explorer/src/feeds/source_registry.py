"""
Registro centralizzato delle fonti RSS.

Questo modulo gestisce l'elenco completo delle fonti di notizie
disponibili nell'applicazione. Le fonti possono provenire da:

1. DEFAULT_SOURCES (hardcoded) — fonti integrate nel codice sorgente,
   sempre disponibili come fallback
2. sources.json (opzionale) — file JSON nella cartella data/,
   che permette di aggiungere/modificare fonti senza toccare il codice

La classe SourceRegistry unifica le due sorgenti: prima carica il JSON
(se esiste), poi integra le fonti di default che mancano.

Ogni fonte è un dizionario con:
    url  (str)  — URL del feed RSS/Atom
    type (str)  — tipo di feed (sempre "rss" per ora)
    paid (bool) — True se richiede abbonamento (disabilitata di default)
"""
import json
import os


# ── Fonti RSS di default ─────────────────────────────────────────────
# Dizionario annidato: {categoria: {nome_fonte: {url, type, paid}}}
# Organizzato per categoria tematica per facilitare la navigazione.
#
# Le URL Unsplash in CATEGORY_IMAGES (in recommender.py) corrispondono
# a queste stesse categorie per fornire immagini di fallback coerenti.
#
# Le fonti con paid=True non vengono scaricate a meno che l'utente
# non le abiliti esplicitamente nelle Preferenze.
DEFAULT_SOURCES = {
    # ── Notizie italiane generaliste ──
    # Principali testate e agenzie di stampa italiane.
    # ANSA è l'agenzia di stampa nazionale, Repubblica e Corriere
    # sono i quotidiani più letti online in Italia.
    "Notizie Generaliste": {
        "ANSA": {"url": "https://www.ansa.it/sito/ansait_rss.xml", "type": "rss", "paid": False},
        "Repubblica": {"url": "https://www.repubblica.it/rss/homepage/rss2.0.xml", "type": "rss", "paid": False},
        "Corriere della Sera": {"url": "https://xml2.corriereobjects.it/rss/homepage.xml", "type": "rss", "paid": False},
        "Il Fatto Quotidiano": {"url": "https://www.ilfattoquotidiano.it/feed/", "type": "rss", "paid": False},
        "Il Post": {"url": "https://www.ilpost.it/feed/", "type": "rss", "paid": False},
        "Sky TG24": {"url": "https://tg24.sky.it/rss/tg24_homepage.xml", "type": "rss", "paid": False},
        "AGI": {"url": "https://www.agi.it/rss", "type": "rss", "paid": False},
    },

    # ── Testate internazionali ──
    # Mix di testate anglofone, europee e mediorientali
    # per una copertura globale diversificata.
    "Notizie Internazionali": {
        "BBC News": {"url": "https://feeds.bbci.co.uk/news/rss.xml", "type": "rss", "paid": False},
        "CNN": {"url": "http://rss.cnn.com/rss/edition.rss", "type": "rss", "paid": False},
        "Reuters": {"url": "https://www.reutersagency.com/feed/", "type": "rss", "paid": False},
        "Al Jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "rss", "paid": False},
        "The Guardian": {"url": "https://www.theguardian.com/world/rss", "type": "rss", "paid": False},
        "France 24": {"url": "https://www.france24.com/en/rss", "type": "rss", "paid": False},
        "DW News": {"url": "https://rss.dw.com/rdf/rss-en-all", "type": "rss", "paid": False},
    },

    # ── Tecnologia ──
    # Fonti tech italiane e internazionali.
    # MIT Technology Review è premium (paywall).
    "Tecnologia": {
        "TechCrunch": {"url": "https://techcrunch.com/feed/", "type": "rss", "paid": False},
        "The Verge": {"url": "https://www.theverge.com/rss/index.xml", "type": "rss", "paid": False},
        "Ars Technica": {"url": "https://feeds.arstechnica.com/arstechnica/index", "type": "rss", "paid": False},
        "Wired IT": {"url": "https://www.wired.it/feed/rss", "type": "rss", "paid": False},
        "Tom's Hardware IT": {"url": "https://www.tomshw.it/feed", "type": "rss", "paid": False},
        "Hacker News": {"url": "https://hnrss.org/frontpage", "type": "rss", "paid": False},
        "MIT Technology Review": {"url": "https://www.technologyreview.com/feed/", "type": "rss", "paid": True},
    },

    # ── Scienza ──
    # Riviste scientifiche e divulgazione, sia internazionali
    # (Nature, Science Daily) che italiane (Le Scienze).
    "Scienza": {
        "Nature News": {"url": "https://www.nature.com/nature.rss", "type": "rss", "paid": False},
        "Science Daily": {"url": "https://www.sciencedaily.com/rss/all.xml", "type": "rss", "paid": False},
        "New Scientist": {"url": "https://www.newscientist.com/feed/home/", "type": "rss", "paid": False},
        "Phys.org": {"url": "https://phys.org/rss-feed/", "type": "rss", "paid": False},
        "Le Scienze": {"url": "https://www.lescienze.it/rss/all/rss2.0.xml", "type": "rss", "paid": False},
    },

    # ── Economia e Finanza ──
    # Include fonti premium (Il Sole 24 Ore, Bloomberg, FT)
    # che richiedono abbonamento per il contenuto completo.
    "Economia e Finanza": {
        "Il Sole 24 Ore": {"url": "https://www.ilsole24ore.com/rss/homepage.xml", "type": "rss", "paid": True},
        "Bloomberg": {"url": "https://feeds.bloomberg.com/markets/news.rss", "type": "rss", "paid": True},
        "CNBC": {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "type": "rss", "paid": False},
        "Financial Times": {"url": "https://www.ft.com/?format=rss", "type": "rss", "paid": True},
        "Milano Finanza": {"url": "https://www.milanofinanza.it/rss/", "type": "rss", "paid": False},
    },

    # ── Sport ──
    # Quotidiani sportivi italiani + fonti internazionali.
    "Sport": {
        "Gazzetta dello Sport": {"url": "https://www.gazzetta.it/rss/home.xml", "type": "rss", "paid": False},
        "Tuttosport": {"url": "https://www.tuttosport.com/rss/home.xml", "type": "rss", "paid": False},
        "ESPN": {"url": "https://www.espn.com/espn/rss/news", "type": "rss", "paid": False},
        "BBC Sport": {"url": "https://feeds.bbci.co.uk/sport/rss.xml", "type": "rss", "paid": False},
        "Sky Sport": {"url": "https://sport.sky.it/rss/sport_homepage.xml", "type": "rss", "paid": False},
        "Corriere Sport": {"url": "https://www.corrieredellosport.it/rss/", "type": "rss", "paid": False},
    },

    # ── Intrattenimento ──
    # Cinema, musica, videogiochi, cultura pop.
    "Intrattenimento": {
        "Movieplayer": {"url": "https://movieplayer.it/rss/", "type": "rss", "paid": False},
        "Variety": {"url": "https://variety.com/feed/", "type": "rss", "paid": False},
        "Rolling Stone IT": {"url": "https://www.rollingstone.it/feed/", "type": "rss", "paid": False},
        "IGN": {"url": "https://feeds.feedburner.com/ign/all", "type": "rss", "paid": False},
        "Everyeye": {"url": "https://www.everyeye.it/feed_rss.asp", "type": "rss", "paid": False},
    },

    # ── Salute e Benessere ──
    "Salute e Benessere": {
        "Medical News Today": {"url": "https://www.medicalnewstoday.com/newsfeeds/rss", "type": "rss", "paid": False},
        "WebMD": {"url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSFeedID=RSS_Main", "type": "rss", "paid": False},
        "Corriere Salute": {"url": "https://www.corriere.it/salute/rss/", "type": "rss", "paid": False},
    },

    # ── Viaggi e Lifestyle ──
    "Viaggi e Lifestyle": {
        "Lonely Planet": {"url": "https://www.lonelyplanet.com/blog/feed", "type": "rss", "paid": False},
        "SiViaggia": {"url": "https://siviaggia.it/feed/", "type": "rss", "paid": False},
        "TuristiPerCaso": {"url": "https://www.turistipercaso.it/rss/", "type": "rss", "paid": False},
    },

    # ── Politica ──
    "Politica": {
        "Politico EU": {"url": "https://www.politico.eu/feed/", "type": "rss", "paid": False},
        "Open Online": {"url": "https://www.open.online/feed/", "type": "rss", "paid": False},
        "Fanpage Politica": {"url": "https://www.fanpage.it/feed/", "type": "rss", "paid": False},
    },

    # ── Gaming ──
    "Gaming": {
        "Eurogamer IT": {"url": "https://www.eurogamer.it/feed", "type": "rss", "paid": False},
        "Multiplayer.it": {"url": "https://multiplayer.it/feed/rss/", "type": "rss", "paid": False},
        "PC Gamer": {"url": "https://www.pcgamer.com/rss/", "type": "rss", "paid": False},
        "Kotaku": {"url": "https://kotaku.com/rss", "type": "rss", "paid": False},
    },

    # ── Ambiente ──
    "Ambiente": {
        "GreenMe": {"url": "https://www.greenme.it/feed/", "type": "rss", "paid": False},
        "Rinnovabili.it": {"url": "https://www.rinnovabili.it/feed/", "type": "rss", "paid": False},
        "LifeGate": {"url": "https://www.lifegate.it/feed", "type": "rss", "paid": False},
    },

    # ── Auto e Motori ──
    "Auto e Motori": {
        "Quattroruote": {"url": "https://www.quattroruote.it/rss.xml", "type": "rss", "paid": False},
        "AlVolante": {"url": "https://www.alvolante.it/rss.xml", "type": "rss", "paid": False},
        "Motor1 IT": {"url": "https://it.motor1.com/rss/news/", "type": "rss", "paid": False},
    },

    # ── Moda e Design ──
    "Moda e Design": {
        "Vogue IT": {"url": "https://www.vogue.it/feed/rss", "type": "rss", "paid": False},
        "Elle IT": {"url": "https://www.elle.com/it/feed/", "type": "rss", "paid": False},
        "Designboom": {"url": "https://www.designboom.com/feed/", "type": "rss", "paid": False},
    },

    # ── Cucina e Food ──
    "Cucina e Food": {
        "GialloZafferano": {"url": "https://www.giallozafferano.it/feed", "type": "rss", "paid": False},
        "Gambero Rosso": {"url": "https://www.gamberorosso.it/feed/", "type": "rss", "paid": False},
        "Dissapore": {"url": "https://www.dissapore.com/feed/", "type": "rss", "paid": False},
    },

    # ── Cybersecurity ──
    # Fonti specializzate in sicurezza informatica e hacking.
    "Cybersecurity": {
        "The Hacker News": {"url": "https://feeds.feedburner.com/TheHackersNews", "type": "rss", "paid": False},
        "Krebs on Security": {"url": "https://krebsonsecurity.com/feed/", "type": "rss", "paid": False},
        "BleepingComputer": {"url": "https://www.bleepingcomputer.com/feed/", "type": "rss", "paid": False},
        "Dark Reading": {"url": "https://www.darkreading.com/rss.xml", "type": "rss", "paid": False},
        "SecurityWeek": {"url": "https://www.securityweek.com/feed/", "type": "rss", "paid": False},
        "Threatpost": {"url": "https://threatpost.com/feed/", "type": "rss", "paid": False},
    },

    # ── Energia e Risorse ──
    "Energia e Risorse": {
        "Rinnovabili.it Energia": {"url": "https://www.rinnovabili.it/energia/feed/", "type": "rss", "paid": False},
        "QualEnergia": {"url": "https://www.qualenergia.it/feed/", "type": "rss", "paid": False},
        "Energy Monitor": {"url": "https://www.energymonitor.ai/feed/", "type": "rss", "paid": False},
    },

    # ── Educazione ──
    "Educazione": {
        "Orizzonte Scuola": {"url": "https://www.orizzontescuola.it/feed/", "type": "rss", "paid": False},
        "Tecnica della Scuola": {"url": "https://www.tecnicadellascuola.it/feed", "type": "rss", "paid": False},
        "Inside Higher Ed": {"url": "https://www.insidehighered.com/rss/feed", "type": "rss", "paid": False},
    },

    # ── Spazio e Astronomia ──
    "Spazio e Astronomia": {
        "Space.com": {"url": "https://www.space.com/feeds/all", "type": "rss", "paid": False},
        "NASA Breaking News": {"url": "https://www.nasa.gov/news-release/feed/", "type": "rss", "paid": False},
        "SpaceNews": {"url": "https://spacenews.com/feed/", "type": "rss", "paid": False},
        "ESA News": {"url": "https://www.esa.int/rssfeed/Our_Activities/Space_News", "type": "rss", "paid": False},
    },

    # ── Startup e Innovazione ──
    "Startup e Innovazione": {
        "StartupItalia": {"url": "https://startupitalia.eu/feed", "type": "rss", "paid": False},
        "EU-Startups": {"url": "https://www.eu-startups.com/feed/", "type": "rss", "paid": False},
        "TechStartups": {"url": "https://techstartups.com/feed/", "type": "rss", "paid": False},
    },

    # ── Diritto e Legge ──
    "Diritto e Legge": {
        "Altalex": {"url": "https://www.altalex.com/documents/rss", "type": "rss", "paid": False},
        "Il Quotidiano Giuridico": {"url": "https://www.quotidianogiuridico.it/feed/", "type": "rss", "paid": False},
    },
}


class SourceRegistry:
    """
    Registro fonti RSS con caricamento da file JSON + fallback su DEFAULT_SOURCES.
    
    Flusso di inizializzazione:
    1. Se viene passato un json_path, carica le fonti da quel file
    2. Altrimenti cerca data/sources.json nella root del progetto
    3. In ogni caso, integra le fonti di DEFAULT_SOURCES che mancano
       (merge non distruttivo: le fonti dal JSON hanno priorità)
    
    Attributi:
        sources (dict): {categoria: {nome: {url, type, paid}}}
    """

    def __init__(self, json_path=None):
        """
        Inizializza il registro fonti.
        
        Args:
            json_path (str, optional): Percorso a un file JSON con fonti
                aggiuntive. Se None, cerca data/sources.json automaticamente.
        """
        self.sources = {}

        # Carica da JSON se specificato esplicitamente
        if json_path:
            self._load_from_json(json_path)
        else:
            # Calcola il percorso di default: risale di 2 livelli dal
            # file corrente (src/feeds/ → progetto/) e cerca data/sources.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            default_json = os.path.join(base_dir, "data", "sources.json")
            if os.path.exists(default_json):
                self._load_from_json(default_json)

            # Merge con DEFAULT_SOURCES: aggiunge solo le categorie/fonti
            # che non sono già presenti nel JSON, per non sovrascrivere
            # eventuali personalizzazioni dell'utente nel file JSON.
            for cat, cat_sources in DEFAULT_SOURCES.items():
                if cat not in self.sources:
                    # Categoria completamente assente → aggiungi tutto
                    self.sources[cat] = cat_sources
                elif isinstance(self.sources[cat], dict):
                    # Categoria presente → aggiungi solo le fonti mancanti
                    for name, info in cat_sources.items():
                        if name not in self.sources[cat]:
                            self.sources[cat][name] = info

    def _load_from_json(self, path):
        """
        Carica fonti da un file JSON.
        
        Supporta due formati:
        - Dizionario {categoria: {nome: info}} → formato nativo
        - Lista [{name, category, url, ...}]   → formato piatto (legacy)
        
        In caso di errore (file corrotto, permessi, ecc.) fallisce
        silenziosamente: le fonti di default saranno comunque disponibili.
        
        Args:
            path (str): Percorso assoluto al file JSON.
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Formato nativo: usa direttamente
                self.sources = data
            elif isinstance(data, list):
                # Formato piatto: raggruppa per categoria
                for item in data:
                    cat = item.get("category", "Altro")
                    name = item.get("name", "Unknown")
                    if cat not in self.sources:
                        self.sources[cat] = {}
                    self.sources[cat][name] = item
        except Exception:
            # Fallisce silenziosamente: le fonti di default compenseranno
            pass

    def get_sources(self):
        """
        Restituisce tutte le fonti organizzate per categoria.
        
        Returns:
            dict: {categoria: {nome_fonte: {url, type, paid}}}
        """
        return self.sources

    def get_categories(self):
        """
        Restituisce la lista di tutte le categorie disponibili.
        
        Returns:
            list: ["Notizie Generaliste", "Tecnologia", ...]
        """
        return list(self.sources.keys())

    def get_sources_by_category(self, category):
        """
        Restituisce le fonti di una specifica categoria.
        
        Args:
            category (str): Nome della categoria (es. "Tecnologia")
        
        Returns:
            dict: {nome_fonte: {url, type, paid}} o {} se la categoria non esiste
        """
        return self.sources.get(category, {})

    def get_source_types(self):
        """
        Alias di get_categories() per compatibilità.
        
        Returns:
            list: Lista delle categorie (stesso risultato di get_categories)
        """
        return list(self.sources.keys())


def load_sources():
    """
    Funzione helper di convenienza per caricare le fonti.
    
    Crea un SourceRegistry temporaneo e restituisce il dizionario fonti.
    Usata nei componenti che necessitano solo del dizionario fonti
    senza dover istanziare esplicitamente SourceRegistry.
    
    Returns:
        dict: {categoria: {nome_fonte: {url, type, paid}}}
    
    Esempio di utilizzo:
        from feeds.source_registry import load_sources
        sources = load_sources()
        # sources["Tecnologia"]["TechCrunch"]["url"] → "https://techcrunch.com/feed/"
    """
    registry = SourceRegistry()
    return registry.get_sources()