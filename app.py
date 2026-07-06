from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import anthropic
import stripe
import os
import re
from dotenv import load_dotenv

load_dotenv()

def supprimer_emojis(texte):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F9FF"
        u"\U00002700-\U000027BF"
        u"\U0001FA00-\U0001FA6F"
        u"\U00002500-\U00002BEF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', texte).strip()

app = Flask(__name__)
app.secret_key = "nicheai_secret_2024"

# ===== BASE DE DONNEES + AUTH =====
import os as _os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Rapport

_db_url = _os.getenv("DATABASE_URL", "sqlite:///local.db")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "connexion"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
# ===== FIN BLOC DB =====

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

def envoyer_email(destinataire, rapport):
    print(f"Email a envoyer a {destinataire}")

def generer_rapport_premium_rapide(competences, secteur, experience, client_type, objectif, missions_recentes="", tarif_actuel="", zone_geo="", contrainte_principale=""):
    cl = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    contexte_perso = ""
    if missions_recentes:
        contexte_perso += f"\n- Missions/clients recents: {missions_recentes}"
    if tarif_actuel:
        contexte_perso += f"\n- Tarif actuellement pratique: {tarif_actuel}"
    if zone_geo:
        contexte_perso += f"\n- Zone geographique: {zone_geo}"
    if contrainte_principale:
        contexte_perso += f"\n- Contrainte principale actuelle: {contrainte_principale}"

    prompt = f"""Tu es un consultant senior en positionnement freelance avec 10 ans d'experience. Tu connais parfaitement le marche freelance francais (Malt, Upwork, LinkedIn, Creem). Reponds en francais. Sans emoji. Sois ultra-precis, donne de vrais chiffres.

Tu as acces a un outil de recherche web. UTILISE-LE activement (plusieurs recherches si besoin) pour verifier ou trouver: les tarifs reels pratiques sur Malt/LinkedIn dans ce secteur, le volume de missions/demande actuel, les tendances 2025-2026 du secteur concerne, et la concurrence reelle. N'invente pas de chiffres si tu peux les verifier par une recherche.

Profil du freelance:
- Competences: {competences}
- Secteur: {secteur}
- Experience: {experience}
- Client cible: {client_type}
- Objectif mensuel: {objectif} EUR{contexte_perso}

IMPORTANT: si des missions recentes, un tarif actuel, une zone geographique ou une contrainte sont fournis ci-dessus, tu DOIS t'appuyer dessus explicitement dans tes recommandations (ex: comparer le tarif actuel au tarif recommande, adapter le plan d'action a la contrainte mentionnee, ancrer le pitch et la niche recommandee sur les missions reelles citees). Ne les ignore pas et ne les reformule pas de maniere generique.

Ne redige AUCUN titre, introduction, phrase d'accroche ou texte quelconque avant le bloc METRICS. Ta reponse doit commencer directement par "METRICS_START", sans rien avant.

Commence OBLIGATOIREMENT par ce bloc de metriques (valeurs reelles basees sur le profil):

METRICS_START
SCORE_POTENTIEL: [nombre entre 55 et 95]/100
SATURATION: [Faible | Moderee | Forte]
POTENTIEL_REVENU: [X EUR/mois realiste]
DEMANDE: [Forte | Moderee | Faible]
CONCURRENCE: [Faible | Moderee | Forte]
METRICS_END

Puis redige exactement ces sections avec ## devant chaque titre. Chaque section doit etre dense, concrete, avec des vrais chiffres:

## ANALYSE DE MARCHE
Etat reel du marche: tarifs pratiques (fourchettes precises), volume de demande, tendances 2024-2025, qui recrute vraiment dans ce secteur. Minimum 5 donnees chiffrees.

## NICHE RECOMMANDEE
Positionnement ultra-precis: "Je suis le freelance X pour Y qui veut Z". Justification avec chiffres. Sous-niches prioritaires numerotees. Avantage concurrentiel unique a mettre en avant.

## PITCH LINKEDIN
Texte complet en 5-7 phrases. Ton direct, humain, qui donne envie. Commence par un fait ou une situation que le client reconnait. Se termine par un appel a l'action clair. Pret a copier-coller.

## TARIFICATION RECOMMANDEE
TJM recommande avec fourchette basse/haute. 3 forfaits detailles avec nom, prix, contenu exact, delai de livraison. Psychologie tarifaire: comment presenter les prix pour maximiser les conversions.

## TOP 3 PLATEFORMES
Pour chaque plateforme: strategie de profil, mots-cles a utiliser, type de missions a cibler, tarif a afficher, objectif en 90 jours, temps d'investissement hebdomadaire.

## MOTS-CLES SEO
8 mots-cles reels que tes prospects tapent sur Google/Malt/LinkedIn. Classe par volume de recherche (fort/moyen/faible).

## PLAN D'ACTION 30 JOURS
Semaine 1: actions de setup. Semaine 2: premieres prises de contact. Semaine 3: follow-up et ajustements. Semaine 4: bilan et scaling. Actions tres concretes, pas de generalites.

## TEMPLATE PROSPECTION
Message complet (200-250 mots) personnalisable. Commence par [Prenom], mentionne quelque chose de specifique, propose de la valeur avant de demander quoi que ce soit. Pret a envoyer sur LinkedIn.

## SCRIPT APPEL DECOUVERTE
Deroulé complet d'un appel de 30 minutes: accueil (2 min), diagnostic besoins (10 min), presentation solution (10 min), closing (8 min). Questions exactes a poser, reponses aux objections courantes.

Sois tres precis. Evite les generalites vagues. Chaque conseil doit etre actionnable immediatement.## LIVRABLE - PROFIL MALT PRET A COPIER
Redige le profil Malt complet et pret a l'emploi: un titre accrocheur (60 caracteres max), une bio de 400-500 caracteres a la premiere personne qui vend, et 8 tags/competences. Texte fini, copier-coller direct, pas de conseils.

## LIVRABLE - BIO LINKEDIN
Redige la section "A propos" LinkedIn complete (200-250 mots), a la premiere personne, avec accroche, parcours, proposition de valeur et appel a l'action. Texte fini pret a coller.

## LIVRABLE - 5 MESSAGES DE PROSPECTION
Redige 5 messages de prospection differents, prets a envoyer, personnalises avec [Prenom] et [Entreprise] a remplacer. Chacun 60-80 mots, accroche + valeur + call to action. Numerote-les de 1 a 5.

## LIVRABLE - EMAIL DE RELANCE
Redige un email de relance pret a envoyer pour un prospect qui n'a pas repondu. 80-100 mots, ton amical mais professionnel, avec [Prenom].

## LIVRABLE - PLANNING DE CONTENU 30 JOURS
Cree un planning concret sur 4 semaines: pour chaque semaine, 3 idees de posts precises (sujet + format + objectif) adaptees au secteur du freelance. 

Actionnable immediatement."""

    try:
        r = cl.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{"role": "user", "content": prompt}]
        )
        texte_complet = ""
        for block in r.content:
            if block.type == "text":
                texte_complet += block.text
        return supprimer_emojis(texte_complet)
    except Exception as e:
        return f"Erreur generation: {str(e)}"


def md_to_html(text):
    # Parser le bloc METRICS
    metrics = {}
    metrics_match = re.search(r'METRICS_START\n(.*?)\nMETRICS_END', text, re.DOTALL)
    if metrics_match:
        for line in metrics_match.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                metrics[k.strip()] = v.strip()
        text = text.replace(metrics_match.group(0), '').strip()

    html = []

    # Dashboard metriques
    if metrics:
        score = metrics.get('SCORE_POTENTIEL', '80/100').replace('/100', '')
        sat = metrics.get('SATURATION', 'Moderee')
        rev = metrics.get('POTENTIEL_REVENU', 'N/A')
        dem = metrics.get('DEMANDE', 'Forte')
        conc = metrics.get('CONCURRENCE', 'Moderee')

        sat_color = '#4ADE80' if sat == 'Faible' else '#F59E0B' if sat == 'Moderee' else '#F87171'
        dem_color = '#4ADE80' if dem == 'Forte' else '#F59E0B' if dem == 'Moderee' else '#F87171'
        conc_color = '#F87171' if conc == 'Forte' else '#F59E0B' if conc == 'Moderee' else '#4ADE80'

        try:
            score_int = int(score)
        except:
            score_int = 80

        score_label = 'Potentiel excellent' if score_int >= 85 else 'Potentiel eleve' if score_int >= 70 else 'Potentiel correct'
        score_color = '#4ADE80' if score_int >= 85 else '#8B5CF6' if score_int >= 70 else '#F59E0B'

        def bar_width(val):
            return {'Forte': 85, 'Moderee': 55, 'Faible': 28}.get(val, 55)

        html.append(f'''<div class="report-dashboard">
  <div class="dash-header">
    <div class="dash-dots"><span style="background:#FF5F57"></span><span style="background:#FFBD2E"></span><span style="background:#28C840"></span></div>
    <span class="dash-title">NicheAI — Rapport Strategique</span>
  </div>
  <div class="dash-scores">
    <div class="dash-score-card main-score">
      <div class="dash-score-label">Score de potentiel</div>
      <div class="dash-score-value" style="color:{score_color}">{score}<span class="dash-score-denom">/100</span></div>
      <div class="dash-score-sub">{score_label}</div>
      <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{score_int}%;background:{score_color}"></div></div>
    </div>
    <div class="dash-score-card">
      <div class="dash-score-label">Saturation marche</div>
      <div class="dash-score-value sm" style="color:{sat_color}">{sat}</div>
      <div class="dash-score-sub">Niveau de competition</div>
      <div class="dash-meta-row"><span class="dash-meta-label">Potentiel revenus</span><span class="dash-meta-val" style="color:#8B5CF6">{rev}</span></div>
    </div>
  </div>
  <div class="dash-bars">
    <div class="dash-bar-row"><span>Demande marche</span><div class="dash-bar"><div class="dash-bar-fill" style="width:{bar_width(dem)}%;background:{dem_color}"></div></div><span style="color:{dem_color};font-weight:700">{dem}</span></div>
    <div class="dash-bar-row"><span>Niveau concurrence</span><div class="dash-bar"><div class="dash-bar-fill" style="width:{bar_width(conc)}%;background:{conc_color}"></div></div><span style="color:{conc_color};font-weight:700">{conc}</span></div>
  </div>
</div>''')

    # Decouper le texte en sections (titre + lignes de contenu brutes)
    raw_sections = []
    current_title = None
    current_lines = []
    for line in text.split('\n'):
        line = line.rstrip()
        if re.match(r'^#{1,3} ', line):
            if current_title is not None:
                raw_sections.append((current_title, current_lines))
            current_title = re.sub(r'^#{1,3} ', '', line).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_title is not None:
        raw_sections.append((current_title, current_lines))

    # Ignorer toute section sans contenu reel (titre parasite, section vide, etc.)
    def _has_content(lines):
        return any(l.strip() and l.strip() != '---' for l in lines)

    sections = [(t, l) for t, l in raw_sections if _has_content(l)]

    def _render_body(lines, section_type):
        body_html = []
        in_list_local = False
        for line in lines:
            if re.match(r'^[-*] |^- ', line):
                if not in_list_local:
                    body_html.append('<ul>'); in_list_local = True
                item = re.sub(r'^[-*] ', '', line)
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                item = re.sub(r'(\d+[\s]?(?:EUR|€|%|k€|K€|EUR/h|EUR/mois|EUR/an)[^\s,\.]*)', r'<span class="stat">\1</span>', item)
                body_html.append(f'<li>{item}</li>')
            elif re.match(r'^\d+\. ', line):
                if not in_list_local:
                    body_html.append('<ul class="num-list">'); in_list_local = True
                item = re.sub(r'^\d+\. ', '', line)
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                item = re.sub(r'(\d+[\s]?(?:EUR|€|%|k€|K€|EUR/h|EUR/mois)[^\s,\.]*)', r'<span class="stat">\1</span>', item)
                body_html.append(f'<li>{item}</li>')
            elif line.strip() == '' or line.strip() == '---':
                if in_list_local:
                    body_html.append('</ul>'); in_list_local = False
            else:
                if in_list_local:
                    body_html.append('</ul>'); in_list_local = False
                if line.strip():
                    line_proc = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line_proc = re.sub(r'(\d+[\s]?(?:EUR|€|%|k€|K€|EUR/h|EUR/mois)[^\s,\.]*)', r'<span class="stat">\1</span>', line_proc)
                    if section_type == 'plan' and re.match(r'^Semaine \d', line.strip()):
                        body_html.append(f'<div class="week-header">{line_proc}</div>')
                    elif section_type == 'pitch':
                        body_html.append(f'<p class="pitch-text">{line_proc}</p>')
                    elif section_type == 'template':
                        body_html.append(f'<p class="template-text">{line_proc}</p>')
                    else:
                        body_html.append(f'<p>{line_proc}</p>')
        if in_list_local:
            body_html.append('</ul>')
        return body_html

    for idx, (title, lines) in enumerate(sections):
        sec_count = idx + 1
        num = str(sec_count).zfill(2)
        is_open = (sec_count == 1)
        open_cls = ' open' if is_open else ''

        title_upper = title.upper()
        is_pitch = 'PITCH' in title_upper or 'LINKEDIN' in title_upper
        is_pricing = 'TARIF' in title_upper or 'PRIX' in title_upper
        is_plan = 'PLAN' in title_upper or '30' in title_upper
        is_template = 'TEMPLATE' in title_upper or 'PROSPECTION' in title_upper or 'SCRIPT' in title_upper or 'APPEL' in title_upper

        block_cls = 'section-block'
        copy_btn = ''
        section_type = 'default'
        if is_pitch:
            section_type = 'pitch'
            block_cls += ' pitch-block'
            copy_btn = '<button class="copy-btn" onclick="copySection(event, this)">Copier</button>'
        elif is_pricing:
            section_type = 'pricing'
            block_cls += ' pricing-block'
        elif is_plan:
            section_type = 'plan'
            block_cls += ' plan-block'
        elif is_template:
            section_type = 'template'
            block_cls += ' template-block'
            copy_btn = '<button class="copy-btn" onclick="copySection(event, this)">Copier</button>'

        html.append(f'<div class="{block_cls} accordion{open_cls}">')
        html.append(f'<div class="section-header acc-toggle" onclick="toggleAcc(this)"><span class="sec-num">{num}</span><span class="sec-title">{title}</span>{copy_btn}<span class="acc-chevron">&#9662;</span></div>')
        html.append('<div class="acc-body">')
        html.extend(_render_body(lines, section_type))
        html.append('</div>')  # .acc-body
        html.append('</div>')  # .section-block

    return '\n'.join(html)


def _save_rapport(contenu, secteur, type_rapport, missions_recentes="", tarif_actuel="", zone_geo="", contrainte_principale=""):
    try:
        if current_user.is_authenticated:
            titre = "Rapport " + (secteur or "positionnement")
            r = Rapport(
                user_id=current_user.id,
                titre=titre[:255],
                secteur=(secteur or "")[:255],
                contenu=contenu,
                type_rapport=type_rapport,
                missions_recentes=missions_recentes or None,
                tarif_actuel=(tarif_actuel or "")[:100] or None,
                zone_geo=(zone_geo or "")[:255] or None,
                contrainte_principale=(contrainte_principale or "")[:255] or None,
            )
            db.session.add(r)
            if type_rapport == "premium" and not current_user.premium:
                current_user.premium = True
            db.session.commit()
    except Exception as e:
        print("Erreur sauvegarde rapport:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generer", methods=["POST"])
def generer():
    competences = request.form.get("competences")
    secteur = request.form.get("secteur")
    experience = request.form.get("experience")
    client_type = request.form.get("client_type")
    objectif = request.form.get("objectif")
    email = request.form.get("email", "")
    missions_recentes = request.form.get("missions_recentes", "")
    tarif_actuel = request.form.get("tarif_actuel", "")
    zone_geo = request.form.get("zone_geo", "")
    contrainte_principale = request.form.get("contrainte_principale", "")

    session['email'] = email
    session['competences'] = competences
    session['secteur'] = secteur
    session['experience'] = experience
    session['client_type'] = client_type
    session['objectif'] = objectif
    session['missions_recentes'] = missions_recentes
    session['tarif_actuel'] = tarif_actuel
    session['zone_geo'] = zone_geo
    session['contrainte_principale'] = contrainte_principale

    contexte_perso_gratuit = ""
    if zone_geo:
        contexte_perso_gratuit += f"\n- Zone geographique: {zone_geo}"
    if contrainte_principale:
        contexte_perso_gratuit += f"\n- Contrainte principale: {contrainte_principale}"

    prompt_gratuit = f"""Tu es un consultant expert en positionnement freelance.
Reponds de maniere sobre, directe et professionnelle.
N'utilise AUCUN emoji, aucun symbole decoratif, aucune etoile, aucun caractere special.
Utilise uniquement du texte avec des titres en ## majuscules.

Profil :
- Competences : {competences}
- Secteur : {secteur}
- Experience : {experience}
- Client cible : {client_type}
- Objectif mensuel : {objectif} EUR{contexte_perso_gratuit}

Ne redige AUCUN titre, introduction ou phrase d'accroche avant la premiere section. Commence directement par "## NICHE RECOMMANDEE".

Redige un apercu avec exactement ces 3 sections:

## NICHE RECOMMANDEE
Un paragraphe precis (5-6 phrases) sur le positionnement ideal avec des chiffres concrets.

## PITCH LINKEDIN
3-4 phrases percutantes. Arrete-toi sur une accroche, donne envie d'en savoir plus. Pas de conclusion.

## FOURCHETTE TARIFAIRE
Une seule ligne avec fourchette TJM approximative.

---

## RAPPORT COMPLET — ACCES RESTREINT

Plateforme recommandee n°1 : ██████████
Mots-cles de visibilite : ██████ · ██████ · ██████
Plan d'action — Semaine 1 : ██████████████████

Debloque l'analyse complete pour acceder a l'integralite du rapport."""

    message_gratuit = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt_gratuit}]
    )

    rapport_gratuit = supprimer_emojis(message_gratuit.content[0].text)
    rapport_html = md_to_html(rapport_gratuit)
    _save_rapport(rapport_gratuit, secteur, "gratuit", missions_recentes, tarif_actuel, zone_geo, contrainte_principale)
    return render_template("resultat.html", rapport=rapport_gratuit, rapport_html=rapport_html, premium=False, stripe_key=STRIPE_PUBLIC_KEY)


@app.route("/code-promo", methods=["POST"])
def code_promo():
    data = request.get_json()
    code = data.get("code", "").strip().upper()
    if code != "LINO1811":
        return jsonify({"success": False, "message": "Code invalide"})
    session["premium_unlocked"] = True
    session.modified = True
    return jsonify({"success": True})

@app.route("/loading")
def loading():
    if not session.get("competences"):
        return redirect(url_for("index"))
    return render_template("loading.html")
@app.route("/premium-result")
def premium_result():
    rapport = session.get("rapport_complet")
    if not rapport:
        competences = session.get("competences", "")
        if not competences:
            return redirect(url_for("index"))
        rapport = generer_rapport_premium_rapide(
            competences,
            session.get("secteur", ""),
            session.get("experience", ""),
            session.get("client_type", ""),
            session.get("objectif", ""),
            session.get("missions_recentes", ""),
            session.get("tarif_actuel", ""),
            session.get("zone_geo", ""),
            session.get("contrainte_principale", "")
        )
        session["rapport_complet"] = rapport
        session.modified = True
        _save_rapport(
            rapport, session.get("secteur", ""), "premium",
            session.get("missions_recentes", ""), session.get("tarif_actuel", ""),
            session.get("zone_geo", ""), session.get("contrainte_principale", "")
        )
    rapport_html = md_to_html(rapport)
    return render_template("resultat.html", rapport=rapport, rapport_html=rapport_html, premium=True, stripe_key=STRIPE_PUBLIC_KEY)


@app.route("/mentions-legales")
def mentions_legales():
    return render_template("mentions-legales.html")

@app.route("/cgv")
def cgv():
    return render_template("cgv.html")

@app.route("/confidentialite")
def confidentialite():
    return render_template("confidentialite.html")


@app.route("/paiement")
def paiement():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "NicheAI — Rapport Premium",
                        "description": "Rapport complet avec donnees marche reelles"
                    },
                    "unit_amount": 1990,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "cancel",
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return str(e)


@app.route("/success")
def success():
    competences = session.get('competences')
    secteur = session.get('secteur')
    experience = session.get('experience')
    client_type = session.get('client_type')
    objectif = session.get('objectif')
    email = session.get('email')
    missions_recentes = session.get('missions_recentes', '')
    tarif_actuel = session.get('tarif_actuel', '')
    zone_geo = session.get('zone_geo', '')
    contrainte_principale = session.get('contrainte_principale', '')

    if not competences:
        return redirect(url_for('index'))

    contexte_perso = ""
    if missions_recentes:
        contexte_perso += f"\n- Missions/clients recents: {missions_recentes}"
    if tarif_actuel:
        contexte_perso += f"\n- Tarif actuellement pratique: {tarif_actuel}"
    if zone_geo:
        contexte_perso += f"\n- Zone geographique: {zone_geo}"
    if contrainte_principale:
        contexte_perso += f"\n- Contrainte principale actuelle: {contrainte_principale}"

    prompt_premium = f"""Tu es un consultant senior en positionnement freelance avec 10 ans d'experience. Tu connais parfaitement le marche freelance francais. Reponds en francais. Sans emoji. Donne de vrais chiffres issus de ta recherche web.

Profil du freelance:
- Competences: {competences}
- Secteur: {secteur}
- Experience: {experience}
- Client cible: {client_type}
- Objectif mensuel: {objectif} EUR{contexte_perso}

IMPORTANT: si des missions recentes, un tarif actuel, une zone geographique ou une contrainte sont fournis ci-dessus, tu DOIS t'appuyer dessus explicitement dans tes recommandations (ex: comparer le tarif actuel au tarif recommande, adapter le plan d'action a la contrainte mentionnee, ancrer le pitch et la niche recommandee sur les missions reelles citees). Ne les ignore pas et ne les reformule pas de maniere generique.

Ne redige AUCUN titre, introduction, phrase d'accroche ou texte quelconque avant le bloc METRICS. Ta reponse doit commencer directement par "METRICS_START", sans rien avant.

Commence OBLIGATOIREMENT par ce bloc de metriques:

METRICS_START
SCORE_POTENTIEL: [nombre entre 55 et 95]/100
SATURATION: [Faible | Moderee | Forte]
POTENTIEL_REVENU: [X EUR/mois realiste]
DEMANDE: [Forte | Moderee | Faible]
CONCURRENCE: [Faible | Moderee | Forte]
METRICS_END

Puis redige ces sections avec ## devant chaque titre:

## ANALYSE DE MARCHE
Donnees reelles issues de ta recherche: tarifs pratiques sur Malt/Upwork/LinkedIn, volume de demande, tendances 2024-2025, secteurs qui recrutent. Minimum 6 donnees chiffrees.

## NICHE RECOMMANDEE
Positionnement ultra-precis. Sous-niches prioritaires. Avantage concurrentiel cle.

## PITCH LINKEDIN
Texte complet 5-7 phrases. Direct, humain, accrocheur. Pret a copier-coller.

## TARIFICATION RECOMMANDEE
TJM avec fourchette. 3 forfaits detailles (nom, prix, contenu, delai). Psychologie tarifaire.

## TOP 3 PLATEFORMES
Strategie complete pour chaque plateforme. Mots-cles, type de missions, tarif a afficher, objectif 90 jours.

## MOTS-CLES SEO
8 mots-cles reels. Classes par volume de recherche.

## PLAN D'ACTION 30 JOURS
Semaine 1: setup. Semaine 2: premieres prises de contact. Semaine 3: follow-up. Semaine 4: bilan. Actions tres concretes.

## TEMPLATE PROSPECTION
Message complet personnalisable (200-250 mots). Pret a envoyer sur LinkedIn.

## SCRIPT APPEL DECOUVERTE
Deroulé complet 30 minutes. Questions exactes, reponses aux objections.

## PROFILS DE REFERENCE
3 freelances qui reussissent dans cette niche. Pourquoi ils marchent, quoi reproduire.
## LIVRABLE - PROFIL MALT PRET A COPIER
Redige le profil Malt complet et pret a l'emploi: un titre accrocheur (60 caracteres max), une bio de 400-500 caracteres a la premiere personne qui vend, et 8 tags/competences. Texte fini, copier-coller direct, pas de conseils.

## LIVRABLE - BIO LINKEDIN
Redige la section "A propos" LinkedIn complete (200-250 mots), a la premiere personne, avec accroche, parcours, proposition de valeur et appel a l'action. Texte fini pret a coller.

## LIVRABLE - 5 MESSAGES DE PROSPECTION
Redige 5 messages de prospection differents, prets a envoyer, personnalises avec [Prenom] et [Entreprise] a remplacer. Chacun 60-80 mots, accroche + valeur + call to action. Numerote-les de 1 a 5.

## LIVRABLE - EMAIL DE RELANCE
Redige un email de relance pret a envoyer pour un prospect qui n'a pas repondu. 80-100 mots, ton amical mais professionnel, avec [Prenom].

## LIVRABLE - PLANNING DE CONTENU 30 JOURS
Cree un planning concret sur 4 semaines: pour chaque semaine, 3 idees de posts precises (sujet + format + objectif) adaptees au secteur du freelance. 

Actionnable immediatement."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": prompt_premium}]
    )

    rapport_complet = ""
    for block in response.content:
        if block.type == "text":
            rapport_complet += block.text

    rapport_complet = supprimer_emojis(rapport_complet)
    session['rapport_complet'] = rapport_complet
    _save_rapport(rapport_complet, secteur, "premium", missions_recentes, tarif_actuel, zone_geo, contrainte_principale)

    if email:
        envoyer_email(email, rapport_complet)

    rapport_html = md_to_html(rapport_complet)
    return render_template("resultat.html", rapport=rapport_complet, rapport_html=rapport_html, premium=True, stripe_key=STRIPE_PUBLIC_KEY)


@app.route("/cancel")
def cancel():
    return redirect(url_for('index'))


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question")
    rapport = data.get("rapport")
    is_premium = data.get("premium", False)
    questions_used = data.get("questions_used", 0)

    if not is_premium and questions_used >= 2:
        return jsonify({"reponse": "Limite atteinte. Debloquez le rapport complet pour continuer."})

    contexte = f"Voici le rapport freelance du client:\n{rapport}\n\nQuestion: {question}\n\nReponds de maniere concrete et professionnelle, sans emoji. Maximum 3 paragraphes." if rapport else f"Question freelance: {question}\n\nReponds de maniere concrete et professionnelle, sans emoji."

    reponse = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": contexte}]
    )
    return jsonify({"reponse": supprimer_emojis(reponse.content[0].text)})



# ===== ROUTES AUTHENTIFICATION =====
@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            return render_template("inscription.html", error="Tous les champs sont requis.")
        if len(password) < 6:
            return render_template("inscription.html", error="Mot de passe trop court (min 6 caracteres).")
        if User.query.filter_by(email=email).first():
            return render_template("inscription.html", error="Un compte existe deja avec cet email.")
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("mes_rapports"))
    return render_template("inscription.html")


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return render_template("connexion.html", error="Email ou mot de passe incorrect.")
        login_user(user)
        return redirect(url_for("mes_rapports"))
    return render_template("connexion.html")


@app.route("/deconnexion")
def deconnexion():
    logout_user()
    return redirect(url_for("index"))


@app.route("/mes-rapports")
@login_required
def mes_rapports():
    rapports = Rapport.query.filter_by(user_id=current_user.id).order_by(Rapport.date_creation.desc()).all()
    return render_template("mes-rapports.html", rapports=rapports, email=current_user.email, premium=current_user.premium)


@app.route("/rapport/<int:rapport_id>")
@login_required
def voir_rapport(rapport_id):
    rapport = db.session.get(Rapport, rapport_id)
    if not rapport or rapport.user_id != current_user.id:
        return redirect(url_for("mes_rapports"))
    rapport_html = md_to_html(rapport.contenu)
    est_premium = (rapport.type_rapport == "premium")
    return render_template("resultat.html", rapport=rapport.contenu, rapport_html=rapport_html, premium=est_premium, stripe_key=STRIPE_PUBLIC_KEY)
# ===== FIN ROUTES AUTH =====


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
