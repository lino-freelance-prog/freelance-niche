from flask import Flask, render_template, request, session, redirect, url_for
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

    return render_template("resultat.html", rapport=rapport_gratuit, premium=False, stripe_key=STRIPE_PUBLIC_KEY)


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
    return render_template("resultat.html", rapport=rapport, premium=True, stripe_key=STRIPE_PUBLIC_KEY)

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
