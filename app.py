from flask import Flask, render_template, request, session, redirect, url_for
import anthropic
import stripe
import os
import re
from dotenv import load_dotenv
 
load_dotenv()
 
def supprimer_emojis(texte):
    pattern = re.compile(
        u"[\U0001F000-\U0001FFFF"
        u"\U00002300-\U000027BF"
        u"\U00002B00-\U00002BFF"
        u"\U000024C2-\U0001F251"
        u"\uFE00-\uFE0F"
        u"\u200D"
        u"\u20E3"
        u"]+",
        flags=re.UNICODE
    )
    texte = pattern.sub('', texte)
    texte = re.sub(r'\uFE0F', '', texte)
    return texte.strip()
 
app = Flask(__name__)
app.secret_key = "nicheai_secret_2024"
 
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
 
def envoyer_email(destinataire, rapport):
    print(f"Email a envoyer a {destinataire}")
 
def generer_rapport_premium(competences, secteur, experience, client_type, objectif):
    prompt_premium = f"""Tu es un consultant senior en positionnement freelance.
Reponds de maniere sobre, directe et professionnelle.
N'utilise AUCUN emoji, aucun symbole decoratif. Titres en majuscules avec #.
 
Profil :
- Competences : {competences}
- Secteur : {secteur}
- Experience : {experience}
- Client cible : {client_type}
- Objectif mensuel : {objectif}EUR
 
Utilise la recherche web pour des donnees reelles et actuelles.
 
Redige un rapport COMPLET et DETAILLE avec ces sections :
 
# ANALYSE DE MARCHE
Donnees reelles : tarifs constates sur Malt/Upwork/LinkedIn, volume de demande, tendances actuelles du marche francais.
 
# NICHE RECOMMANDEE
Positionnement ultra-precis avec justification chiffree.
 
# PITCH LINKEDIN
Texte complet pret a copier-coller, optimise pour attirer des clients.
 
# TARIFICATION RECOMMANDEE
TJM et forfaits precis bases sur le marche reel avec fourchettes detaillees.
 
# TOP 3 PLATEFORMES
Strategie concrete pour chacune : comment creer son profil, quels mots-cles utiliser, comment se demarquer.
 
# MOTS-CLES DE VISIBILITE
5 mots-cles reels avec volume de recherche estime.
 
# PLAN D ACTION 30 JOURS
Semaine 1, 2, 3, 4 avec actions concretes et mesurables.
 
# TEMPLATE DE PROSPECTION
Message LinkedIn pret a envoyer, personnalise pour la niche.
 
# SCRIPT D APPEL CLIENT
Deroulé complet avec objections et reponses.
 
# PROFILS DE REFERENCE
3 freelances qui reussissent dans cette niche, ce qu ils font et pourquoi ca marche.
 
# OPPORTUNITES CACHEES
2-3 niches adjacentes sous-exploitees avec fort potentiel.
 
Reponds en francais, sois tres concret et actionnable."""
 
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt_premium}]
        )
        rapport = ""
        for block in response.content:
            if block.type == "text":
                rapport += block.text
        return supprimer_emojis(rapport)
    except Exception as e:
        return "Service momentanement surcharge. Veuillez reessayer dans quelques instants."
 
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
N'utilise AUCUN emoji, aucun symbole decoratif. Titres en majuscules avec #.
 
Profil :
- Competences : {competences}
- Secteur : {secteur}
- Experience : {experience}
- Client cible : {client_type}
- Objectif mensuel : {objectif}EUR
 
Redige un rapport avec exactement ces trois sections :
 
# NICHE RECOMMANDEE
Un paragraphe precis et direct sur le positionnement ideal.
 
# PITCH LINKEDIN
3-4 phrases percutantes, arrête avant la conclusion.
 
# FOURCHETTE TARIFAIRE
Une seule ligne.
 
---
 
# RAPPORT COMPLET — ACCES RESTREINT
 
Plateforme recommandee n1 : ██████████
Mots-cles de visibilite : ██████ · ██████ · ██████
Plan semaine 1 : ██████████████████
 
Debloque l'analyse complete pour tout voir."""
 
    try:
        message_gratuit = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt_gratuit}]
        )
        rapport_gratuit = supprimer_emojis(message_gratuit.content[0].text)
    except Exception as e:
        rapport_gratuit = "Service momentanement surcharge. Veuillez reessayer dans quelques instants."
 
    return render_template("resultat.html", rapport=rapport_gratuit, premium=False, stripe_key=STRIPE_PUBLIC_KEY)
 
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
 
    rapport_complet = generer_rapport_premium(competences, secteur, experience, client_type, objectif)
    session['rapport_complet'] = rapport_complet
 
    if email:
        envoyer_email(email, rapport_complet)
 
    return render_template("resultat.html", rapport=rapport_complet, premium=True, stripe_key=STRIPE_PUBLIC_KEY)
 
@app.route("/preview-premium")
def preview_premium():
    competences = session.get('competences')
    secteur = session.get('secteur')
    experience = session.get('experience')
    client_type = session.get('client_type')
    objectif = session.get('objectif')
 
    if not competences:
        return redirect(url_for('index'))
 
    rapport_complet = generer_rapport_premium(competences, secteur, experience, client_type, objectif)
 
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
 
    try:
        reponse = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": f"Rapport:\n{rapport}\n\nQuestion: {question}\n\nReponds sans emoji, de maniere sobre et professionnelle."}]
        )
        return {"reponse": supprimer_emojis(reponse.content[0].text)}
    except Exception as e:
        return {"reponse": "Service momentanement surcharge. Veuillez reessayer."}
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
