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
        "Filodiritto": {"url": "https://www.filodiritto.com/rss.xml", "type": "rss", "paid": False},
        "Diritto.it": {"url": "https://www.diritto.it/feed/", "type": "rss", "paid": False},
        "Studio Cataldi": {"url": "https://www.studiocataldi.it/rss.asp", "type": "rss", "paid": False},
        "Lexology": {"url": "https://www.lexology.com/rss/AllRSS.xml", "type": "rss", "paid": False},
    },

    # ── Medicina e Sanità ──
    "Medicina e Sanità": {
        "The Lancet": {"url": "https://www.thelancet.com/rssfeed/lancet_online.xml", "type": "rss", "paid": False},
        "BMJ": {"url": "https://www.bmj.com/rss/recent.xml", "type": "rss", "paid": False},
        "Quotidiano Sanità": {"url": "https://www.quotidianosanita.it/feed/", "type": "rss", "paid": False},
        "Medical News Today": {"url": "https://www.medicalnewstoday.com/newsfeeds/rss", "type": "rss", "paid": False},
        "NEJM": {"url": "https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss", "type": "rss", "paid": False},
        "JAMA Network": {"url": "https://jamanetwork.com/rss/site_3/67.xml", "type": "rss", "paid": False},
        "Medscape": {"url": "https://www.medscape.com/cx/rssfeeds/2702.xml", "type": "rss", "paid": False},
        "Pharmastar": {"url": "https://www.pharmastar.it/feed/rss", "type": "rss", "paid": False},
        "Dottnet": {"url": "https://www.dottnet.it/feed/", "type": "rss", "paid": False},
        "Nurse24": {"url": "https://www.nurse24.it/feed/", "type": "rss", "paid": False},
        "Univadis IT": {"url": "https://www.univadis.it/rss", "type": "rss", "paid": False},
    },

    # ── Ingegneria e Costruzioni ──
    "Ingegneria e Costruzioni": {
        "Edilportale": {"url": "https://www.edilportale.com/rss/news.xml", "type": "rss", "paid": False},
        "The Engineer": {"url": "https://www.theengineer.co.uk/feed/", "type": "rss", "paid": False},
        "Engineering.com": {"url": "https://www.engineering.com/feed/", "type": "rss", "paid": False},
        "IEEE Spectrum": {"url": "https://spectrum.ieee.org/feeds/feed.rss", "type": "rss", "paid": False},
        "Ingegneri.info": {"url": "https://www.ingegneri.info/feed/", "type": "rss", "paid": False},
        "Ingenio Web": {"url": "https://www.ingenio-web.it/feed/", "type": "rss", "paid": False},
        "New Civil Engineer": {"url": "https://www.newcivilengineer.com/feed/", "type": "rss", "paid": False},
        "Engineering News-Record": {"url": "https://www.enr.com/rss", "type": "rss", "paid": False},
        "Ediltecnico": {"url": "https://www.ediltecnico.it/feed/", "type": "rss", "paid": False},
    },

    # ── Informatica e Data Science ──
    "Informatica e Data Science": {
        "InfoQ": {"url": "https://feed.infoq.com/", "type": "rss", "paid": False},
        "Dev.to": {"url": "https://dev.to/feed", "type": "rss", "paid": False},
        "The Register": {"url": "https://www.theregister.com/headlines.atom", "type": "rss", "paid": False},
        "Towards Data Science": {"url": "https://towardsdatascience.com/feed", "type": "rss", "paid": False},
        "KDnuggets": {"url": "https://www.kdnuggets.com/feed", "type": "rss", "paid": False},
        "Analytics Vidhya": {"url": "https://www.analyticsvidhya.com/feed/", "type": "rss", "paid": False},
        "DataCamp Blog": {"url": "https://www.datacamp.com/blog/rss.xml", "type": "rss", "paid": False},
        "Machine Learning Mastery": {"url": "https://machinelearningmastery.com/feed/", "type": "rss", "paid": False},
        "CSS-Tricks": {"url": "https://css-tricks.com/feed/", "type": "rss", "paid": False},
        "Smashing Magazine": {"url": "https://www.smashingmagazine.com/feed/", "type": "rss", "paid": False},
        "Real Python": {"url": "https://realpython.com/atom.xml", "type": "rss", "paid": False},
        "HTML.it": {"url": "https://www.html.it/feed/", "type": "rss", "paid": False},
    },

    # ── Contabilità e Fiscalità ──
    "Contabilità e Fiscalità": {
        "FiscoOggi": {"url": "https://www.fiscooggi.it/rss.xml", "type": "rss", "paid": False},
        "Informazione Fiscale": {"url": "https://www.informazionefiscale.it/feed", "type": "rss", "paid": False},
        "Commercialista Telematico": {"url": "https://www.commercialistatelematico.com/feed", "type": "rss", "paid": False},
        "Ipsoa Quotidiano": {"url": "https://www.ipsoa.it/rss", "type": "rss", "paid": False},
        "Ecnews": {"url": "https://www.ecnews.it/feed/", "type": "rss", "paid": False},
        "Fiscal Focus": {"url": "https://www.fiscal-focus.it/feed/", "type": "rss", "paid": False},
        "Accounting Today": {"url": "https://www.accountingtoday.com/feed", "type": "rss", "paid": False},
        "Journal of Accountancy": {"url": "https://www.journalofaccountancy.com/rss.xml", "type": "rss", "paid": False},
    },

    # ── Architettura e Urbanistica ──
    "Architettura e Urbanistica": {
        "ArchDaily": {"url": "https://www.archdaily.com/feed", "type": "rss", "paid": False},
        "Dezeen": {"url": "https://www.dezeen.com/feed/", "type": "rss", "paid": False},
        "Architetto.info": {"url": "https://www.architetto.info/feed/", "type": "rss", "paid": False},
        "Domus": {"url": "https://www.domusweb.it/en.feed.xml", "type": "rss", "paid": False},
        "Archiportale": {"url": "https://www.archiportale.com/rss/news.xml", "type": "rss", "paid": False},
        "Abitare": {"url": "https://www.abitare.it/feed/", "type": "rss", "paid": False},
        "Arch2o": {"url": "https://www.arch2o.com/feed/", "type": "rss", "paid": False},
        "Architettura Italiana": {"url": "https://www.architettura-italiana.com/feed/", "type": "rss", "paid": False},
        "Designboom Architecture": {"url": "https://www.designboom.com/architecture/feed/", "type": "rss", "paid": False},
    },

    # ── Marketing e Comunicazione ──
    "Marketing e Comunicazione": {
        "Ninja Marketing": {"url": "https://www.ninjamarketing.it/feed/", "type": "rss", "paid": False},
        "HubSpot Blog": {"url": "https://blog.hubspot.com/rss.xml", "type": "rss", "paid": False},
        "Search Engine Journal": {"url": "https://www.searchenginejournal.com/feed/", "type": "rss", "paid": False},
        "Marketing Land": {"url": "https://martech.org/feed/", "type": "rss", "paid": False},
        "Content Marketing Institute": {"url": "https://contentmarketinginstitute.com/feed/", "type": "rss", "paid": False},
        "Social Media Today": {"url": "https://www.socialmediatoday.com/rss.xml", "type": "rss", "paid": False},
        "Moz Blog": {"url": "https://moz.com/blog/feed", "type": "rss", "paid": False},
        "Inside Marketing": {"url": "https://www.insidemarketing.it/feed/", "type": "rss", "paid": False},
        "Engage.it": {"url": "https://www.engage.it/feed/", "type": "rss", "paid": False},
    },

    # ── Risorse Umane e Lavoro ──
    "Risorse Umane e Lavoro": {
        "AIDP": {"url": "https://www.aidp.it/feed/", "type": "rss", "paid": False},
        "Il Sole 24 Ore Lavoro": {"url": "https://www.ilsole24ore.com/rss/norme-e-tributi.xml", "type": "rss", "paid": True},
        "HR Morning": {"url": "https://www.hrmorning.com/feed/", "type": "rss", "paid": False},
        "SHRM": {"url": "https://www.shrm.org/rss/pages/rss.aspx", "type": "rss", "paid": False},
        "HR Online": {"url": "https://www.hronline.it/feed/", "type": "rss", "paid": False},
        "Lavoro e Diritti": {"url": "https://www.lavoroediritti.com/feed", "type": "rss", "paid": False},
        "Indeed Blog": {"url": "https://www.indeed.com/lead/feed", "type": "rss", "paid": False},
        "Randstad Blog": {"url": "https://www.randstad.it/blog/feed/", "type": "rss", "paid": False},
    },

    # ── Ricerca Accademica e Paper ──
    "Ricerca Accademica": {
        "arXiv CS": {"url": "https://rss.arxiv.org/rss/cs", "type": "rss", "paid": False},
        "arXiv AI": {"url": "https://rss.arxiv.org/rss/cs.AI", "type": "rss", "paid": False},
        "arXiv Machine Learning": {"url": "https://rss.arxiv.org/rss/cs.LG", "type": "rss", "paid": False},
        "arXiv Physics": {"url": "https://rss.arxiv.org/rss/physics", "type": "rss", "paid": False},
        "arXiv Math": {"url": "https://rss.arxiv.org/rss/math", "type": "rss", "paid": False},
        "arXiv Quantitative Biology": {"url": "https://rss.arxiv.org/rss/q-bio", "type": "rss", "paid": False},
        "arXiv Economics": {"url": "https://rss.arxiv.org/rss/econ", "type": "rss", "paid": False},
        "arXiv Statistics": {"url": "https://rss.arxiv.org/rss/stat", "type": "rss", "paid": False},
        "PubMed": {"url": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1/?term=science&format=abstract", "type": "rss", "paid": False},
        "PLOS ONE": {"url": "https://journals.plos.org/plosone/feed/atom", "type": "rss", "paid": False},
        "Nature News": {"url": "https://www.nature.com/nature.rss", "type": "rss", "paid": False},
        "Science Magazine": {"url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science", "type": "rss", "paid": False},
        "SSRN": {"url": "https://papers.ssrn.com/sol3/Jeljour_results.cfm?form_name=journalBrowse&journal_id=&Network=no&lim=false&npage=1&SortOrder=ab_approval_date&stype=rn&feedtype=rss", "type": "rss", "paid": False},
        "Frontiers": {"url": "https://www.frontiersin.org/feeds/allnews.xml", "type": "rss", "paid": False},
        "Cell": {"url": "https://www.cell.com/cell/rss", "type": "rss", "paid": False},
        "IEEE Xplore": {"url": "https://ieeexplore.ieee.org/rss/TOC7433297.XML", "type": "rss", "paid": False},
        "ACM TechNews": {"url": "https://technews.acm.org/rss.xml", "type": "rss", "paid": False},
        "Springer Open": {"url": "https://www.springeropen.com/latest.rss", "type": "rss", "paid": False},
    },

    # ── Psicologia e Scienze Sociali ──
    "Psicologia e Scienze Sociali": {
        "Psychology Today": {"url": "https://www.psychologytoday.com/intl/blog/feed", "type": "rss", "paid": False},
        "British Psychological Society": {"url": "https://www.bps.org.uk/feeds/research-digest", "type": "rss", "paid": False},
        "State of Mind": {"url": "https://www.stateofmind.it/feed/", "type": "rss", "paid": False},
        "PsyPost": {"url": "https://www.psypost.org/feed/", "type": "rss", "paid": False},
        "APA Monitor": {"url": "https://www.apa.org/monitor/rss", "type": "rss", "paid": False},
    },

    # ── Farmacia e Biotecnologie ──
    "Farmacia e Biotecnologie": {
        "Pharmastar": {"url": "https://www.pharmastar.it/feed/rss", "type": "rss", "paid": False},
        "FiercePharma": {"url": "https://www.fiercepharma.com/rss.xml", "type": "rss", "paid": False},
        "GEN - Genetic Engineering News": {"url": "https://www.genengnews.com/feed/", "type": "rss", "paid": False},
        "BioPharma Dive": {"url": "https://www.biopharmadive.com/feeds/news/", "type": "rss", "paid": False},
        "STAT News": {"url": "https://www.statnews.com/feed/", "type": "rss", "paid": False},
    },

    # ── Veterinaria e Scienze Animali ──
    "Veterinaria": {
        "La Settimana Veterinaria": {"url": "https://www.lasettimanavet.it/feed/", "type": "rss", "paid": False},
        "Anmvi Oggi": {"url": "https://www.anmvioggi.it/rss.xml", "type": "rss", "paid": False},
        "Veterinary Record": {"url": "https://bvajournals.onlinelibrary.wiley.com/action/showFeed?jc=20427670&type=etoc&feed=rss", "type": "rss", "paid": False},
    },

    # ── Agraria e Scienze Alimentari ──
    "Agraria e Alimentazione": {
        "AgroNotizie": {"url": "https://agronotizie.imagelinenetwork.com/rss/", "type": "rss", "paid": False},
        "Informatore Agrario": {"url": "https://www.informatoreagrario.it/feed/", "type": "rss", "paid": False},
        "Food Navigator": {"url": "https://www.foodnavigator.com/rss/", "type": "rss", "paid": False},
        "Alimentazione e Salute": {"url": "https://www.alimentazionesana.it/feed/", "type": "rss", "paid": False},
        "AgriCentral": {"url": "https://www.agricentral.it/feed/", "type": "rss", "paid": False},
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