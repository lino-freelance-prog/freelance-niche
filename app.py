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

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

def envoyer_email(destinataire, rapport):
    print(f"Email a envoyer a {destinataire}")

def generer_rapport_premium_rapide(competences, secteur, experience, client_type, objectif):
    import anthropic as ac
    cl = ac.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""Tu es un consultant senior en positionnement freelance. Reponds en francais. Sans emoji.

Profil:
- Competences: {competences}
- Secteur: {secteur}
- Experience: {experience}
- Client cible: {client_type}
- Objectif mensuel: {objectif}EUR

Commence OBLIGATOIREMENT par ce bloc de metriques (remplace les valeurs par tes analyses reelles):

METRICS_START
SCORE_POTENTIEL: [nombre entre 60 et 95]/100
SATURATION: [Faible | Moderee | Forte]
POTENTIEL_REVENU: [X EUR/mois realiste]
DEMANDE: [Forte | Moderee | Faible]
CONCURRENCE: [Faible | Moderee | Forte]
METRICS_END

Puis redige ces sections avec ## devant chaque titre:

## ANALYSE DE MARCHE
Donnees chiffrees reelles sur le marche freelance dans ce secteur.

## NICHE RECOMMANDEE
Positionnement ultra-precis avec justification chiffree.

## PITCH LINKEDIN
Texte complet pret a copier. Direct, humain, percutant.

## TARIFICATION RECOMMANDEE
TJM et forfaits avec fourchettes precises.

## TOP 3 PLATEFORMES
Strategie concrete pour chaque plateforme.

## MOTS-CLES SEO
Liste des mots-cles prioritaires.

## PLAN 30 JOURS
Actions semaine par semaine, tres concret.

## TEMPLATE PROSPECTION
Message complet pret a envoyer.

## SCRIPT APPEL DECOUVERTE
Script complet pour premier appel client.

Sois tres precis, donne des vrais chiffres marche, evite les generalites."""
    try:
        r = cl.messages.create(model="claude-haiku-4-5-20251001", max_tokens=3500,
            messages=[{"role":"user","content":prompt}])
        return r.content[0].text
    except Exception as e:
        return f"Erreur generation: {str(e)}"


def md_to_html(text):
    import re
    lines = text.split("\n")
    html = []
    in_list = False
    for line in lines:
        line = line.rstrip()
        # Headers
        if re.match(r"^### ", line):
            if in_list: html.append("</ul>"); in_list = False
            html.append("<h3>" + re.sub(r"^### ","",line) + "</h3>")
        elif re.match(r"^## ", line):
            if in_list: html.append("</ul>"); in_list = False
            html.append("<h2>" + re.sub(r"^## ","",line) + "</h2>")
        elif re.match(r"^# ", line):
            if in_list: html.append("</ul>"); in_list = False
            html.append("<h2>" + re.sub(r"^# ","",line) + "</h2>")
        # Lists
        elif re.match(r"^[-*] ", line) or re.match(r"^- ", line):
            if not in_list: html.append("<ul>"); in_list = True
            item = re.sub(r"^[-*] ","",line)
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            html.append("<li>" + item + "</li>")
        elif re.match(r"^\d+\. ", line):
            if not in_list: html.append("<ul>"); in_list = True
            item = re.sub(r"^\d+\. ","",line)
            html.append("<li>" + item + "</li>")
        elif line.strip() == "" or line.strip() == "---":
            if in_list: html.append("</ul>"); in_list = False
            if line.strip() == "---":
                html.append("<hr>")
        else:
            if in_list: html.append("</ul>"); in_list = False
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            if line.strip():
                html.append("<p>" + line + "</p>")
    if in_list: html.append("</ul>")
    return "\n".join(html)

def md_to_html(text):
    import re
    lines = text.split("\n")
    html = []
    in_list = False
    section_count = 0
    in_pitch = False

    for i, line in enumerate(lines):
        line = line.rstrip()

        if re.match(r"^#{1,3} ", line):
            if in_list: html.append("</ul>"); in_list = False
            title = re.sub(r"^#{1,3} ", "", line).strip()
            section_count += 1
            num = str(section_count).zfill(2)
            in_pitch = "PITCH" in title.upper() or "LINKEDIN" in title.upper()
            if in_pitch:
                html.append(f'''<div class="section-block pitch-block">
<div class="section-header"><span class="sec-num">{num}</span><span class="sec-title">{title}</span><button class="copy-btn" onclick="copyPitch(this)">Copier</button></div>''')
            else:
                html.append(f'''<div class="section-block">
<div class="section-header"><span class="sec-num">{num}</span><span class="sec-title">{title}</span></div>''')

        elif re.match(r"^[-*] |^- ", line):
            if not in_list:
                html.append("<ul>")
                in_list = True
            item = re.sub(r"^[-*] ", "", line)
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"(\d+[\s]?(?:EUR|€|%|k€|K€|\$/h|EUR/h|EUR/mois)[^\s,]*)", r'<span class="stat">\1</span>', item)
            html.append(f"<li>{item}</li>")

        elif line.strip() == "" or line.strip() == "---":
            if in_list: html.append("</ul>"); in_list = False
            if html and not html[-1].endswith("</div>") and not html[-1] == "<ul>":
                if in_pitch:
                    html.append("</div>")
                    in_pitch = False
                elif html[-1] not in ["</ul>", ""]:
                    pass

        else:
            if in_list: html.append("</ul>"); in_list = False
            if line.strip():
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
                line = re.sub(r"(\d+[\s]?(?:EUR|€|%|k€|K€|EUR/h|EUR/mois)[^\s,\.]*)", r'<span class="stat">\1</span>', line)
                if in_pitch:
                    html.append(f'<p class="pitch-text">{line}</p>')
                else:
                    html.append(f"<p>{line}</p>")

    if in_list: html.append("</ul>")
    result = "\n".join(html)
    # Fermer les section-blocks
    result = re.sub(r'(<div class="section-block[^>]*>[\s\S]*?)(?=<div class="section-block|$)', r'\1</div>\n', result)
    return result

def md_to_html(text):
    import re

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

    # Rendu du dashboard si métriques présentes
    if metrics:
        score = metrics.get('SCORE_POTENTIEL', '82/100').replace('/100','')
        sat = metrics.get('SATURATION', 'Moderee')
        rev = metrics.get('POTENTIEL_REVENU', 'N/A')
        dem = metrics.get('DEMANDE', 'Forte')
        conc = metrics.get('CONCURRENCE', 'Moderee')

        sat_color = '#4ADE80' if sat == 'Faible' else '#F59E0B' if sat == 'Moderee' else '#F87171'
        dem_color = '#4ADE80' if dem == 'Forte' else '#F59E0B' if dem == 'Moderee' else '#F87171'
        conc_color = '#F87171' if conc == 'Forte' else '#F59E0B' if conc == 'Moderee' else '#4ADE80'

        def bar_width(val):
            return {'Forte': 85, 'Moderee': 55, 'Faible': 30}.get(val, 60)

        html.append(f'''<div class="report-dashboard">
  <div class="dash-header"><span class="dash-dots"><span style="background:#FF5F57"></span><span style="background:#FFBD2E"></span><span style="background:#28C840"></span></span><span class="dash-title">NicheAI — Rapport Strategique</span></div>
  <div class="dash-scores">
    <div class="dash-score-card">
      <div class="dash-score-label">Score de potentiel</div>
      <div class="dash-score-value" style="color:#8B5CF6">{score}<span style="font-size:18px;color:#64748B">/100</span></div>
      <div class="dash-score-sub">Potentiel eleve</div>
    </div>
    <div class="dash-score-card">
      <div class="dash-score-label">Saturation marche</div>
      <div class="dash-score-value" style="color:{sat_color}">{sat}</div>
      <div class="dash-score-sub">Opportunite detectee</div>
    </div>
  </div>
  <div class="dash-bars">
    <div class="dash-bar-row"><span>Potentiel de revenus</span><div class="dash-bar"><div class="dash-bar-fill" style="width:80%;background:#8B5CF6"></div></div><span style="color:#8B5CF6;font-weight:700">{rev}</span></div>
    <div class="dash-bar-row"><span>Demande marche</span><div class="dash-bar"><div class="dash-bar-fill" style="width:{bar_width(dem)}%;background:{dem_color}"></div></div><span style="color:{dem_color};font-weight:700">{dem}</span></div>
    <div class="dash-bar-row"><span>Niveau concurrence</span><div class="dash-bar"><div class="dash-bar-fill" style="width:{bar_width(conc)}%;background:{conc_color}"></div></div><span style="color:{conc_color};font-weight:700">{conc}</span></div>
  </div>
</div>''')

    # Parser les sections
    lines = text.split('\n')
    in_list = False
    sec_count = 0

    for line in lines:
        line = line.rstrip()
        if re.match(r'^#{1,3} ', line):
            if in_list: html.append('</ul></div>'); in_list = False
            else:
                if sec_count > 0: html.append('</div>')
            title = re.sub(r'^#{1,3} ', '', line)
            sec_count += 1
            num = str(sec_count).zfill(2)
            is_pitch = 'PITCH' in title.upper() or 'LINKEDIN' in title.upper()
            extra = 'pitch-block' if is_pitch else ''
            copy_btn = '<button class="copy-btn" onclick="copyPitch(this)">Copier</button>' if is_pitch else ''
            html.append(f'<div class="section-block {extra}"><div class="section-header"><span class="sec-num">{num}</span><span class="sec-title">{title}</span>{copy_btn}</div>')
        elif re.match(r'^[-*] |^- ', line):
            if not in_list: html.append('<ul>'); in_list = True
            item = re.sub(r'^[-*] ', '', line)
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
            item = re.sub(r'(\d+[\s]?(?:EUR|€|%|k€|EUR/h|EUR/mois)[^\s,\.]*)', r'<span class="stat">\1</span>', item)
            html.append(f'<li>{item}</li>')
        elif line.strip() == '' or line.strip() == '---':
            if in_list: html.append('</ul>'); in_list = False
        else:
            if in_list: html.append('</ul>'); in_list = False
            if line.strip():
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                line = re.sub(r'(\d+[\s]?(?:EUR|€|%|k€|EUR/h|EUR/mois)[^\s,\.]*)', r'<span class="stat">\1</span>', line)
                is_pitch_section = sec_count > 0 and ('PITCH' in str(html[-3:]).upper() or 'LINKEDIN' in str(html[-3:]).upper())
                css = 'pitch-text' if is_pitch_section else ''
                html.append(f'<p class="{css}">{line}</p>')

    if in_list: html.append('</ul>')
    if sec_count > 0: html.append('</div>')
    return '\n'.join(html)

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

    session['email'] = email
    session['competences'] = competences
    session['secteur'] = secteur
    session['experience'] = experience
    session['client_type'] = client_type
    session['objectif'] = objectif

    prompt_gratuit = f"""Tu es un consultant expert en positionnement freelance.
Reponds de maniere sobre, directe et professionnelle.
N'utilise AUCUN emoji, aucun symbole decoratif, aucune etoile, aucun caractere special.
Utilise uniquement du texte brut avec des titres en majuscules.

Profil :
- Competences : {competences}
- Secteur : {secteur}
- Experience : {experience}
- Client cible : {client_type}
- Objectif mensuel : {objectif}EUR

Redige un rapport avec exactement ces sections, titres en majuscules avec # :

# NICHE RECOMMANDEE
Un paragraphe precis et percutant sur le positionnement ideal.

# PITCH LINKEDIN
3-4 phrases, arrête-toi avant la conclusion pour donner envie d'en savoir plus.

# FOURCHETTE TARIFAIRE
Une ligne uniquement, fourchette vague.

---

# RAPPORT COMPLET — ACCES RESTREINT

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
            session.get("objectif", "")
        )
        session["rapport_complet"] = rapport
        session.modified = True
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

    if not competences:
        return redirect(url_for('index'))

    prompt_premium = f"""Tu es un consultant senior en positionnement freelance.
Reponds de maniere sobre, directe et professionnelle.
N'utilise AUCUN emoji, aucun symbole decoratif, aucune etoile, aucun caractere special.
Utilise uniquement du texte brut avec des titres en majuscules.

Profil :
- Competences : {competences}
- Secteur : {secteur}
- Experience : {experience}
- Client cible : {client_type}
- Objectif mensuel : {objectif}EUR

Utilise la recherche web pour obtenir des donnees reelles et actuelles sur les tarifs, la demande et les profils qui reussissent.

Redige un rapport complet avec ces sections, titres en majuscules avec # :

# ANALYSE DE MARCHE
Donnees reelles : tarifs constates, volume de demande, tendances actuelles.

# NICHE RECOMMANDEE
Positionnement ultra-precis avec justification marche.

# PITCH LINKEDIN
Texte complet pret a copier-coller.

# TARIFICATION RECOMMANDEE
TJM et forfaits bases sur le marche reel.

# TOP 3 PLATEFORMES
Avec strategie concrete pour chacune.

# MOTS-CLES DE VISIBILITE
5 mots-cles reels recherches par tes futurs clients.

# PLAN D'ACTION 30 JOURS
Semaine par semaine, actions concretes.

# TEMPLATE DE PROSPECTION
Message pret a envoyer.

# SCRIPT D'APPEL CLIENT
Deroulé complet.

# PROFILS DE REFERENCE
3 freelances qui reussissent dans cette niche et pourquoi.

Reponds en francais."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt_premium}]
    )

    rapport_complet = ""
    for block in response.content:
        if block.type == "text":
            rapport_complet += block.text

    rapport_complet = supprimer_emojis(rapport_complet)
    session['rapport_complet'] = rapport_complet

    if email:
        envoyer_email(email, rapport_complet)

    return render_template("resultat.html", rapport=rapport_complet, premium=True, stripe_key=STRIPE_PUBLIC_KEY)

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
        return {"reponse": "Limite atteinte. Debloquez le rapport complet pour continuer."}

    reponse = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": f"Voici le rapport freelance:\n{rapport}\n\nQuestion: {question}\n\nReponds de maniere sobre et professionnelle, sans emoji."}]
    )
    return {"reponse": supprimer_emojis(reponse.content[0].text)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
