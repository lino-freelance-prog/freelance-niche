from flask import Flask, render_template, request, session, redirect, url_for
import anthropic
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "nicheai_secret_2024"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

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

    prompt_gratuit = f"""Tu es un expert en personal branding pour freelances.
Un freelance te donne ces infos :
- Compétences : {competences}
- Secteur : {secteur}
- Expérience : {experience}
- Client idéal : {client_type}
- Objectif mensuel : {objectif}€

Génère un rapport avec :
1. 🎯 Sa niche recommandée (1 paragraphe percutant et précis)
2. 💬 Un début de pitch LinkedIn (3-4 phrases seulement, arrête-toi au moment le plus intéressant)
3. 💰 Tarifs : donne UNIQUEMENT une fourchette vague en 1 ligne sans détails

Termine avec exactement ce texte :
---
🔒 **Rapport Premium — sections verrouillées**
*Plateforme recommandée n°1 : ██████████*
*Mots-clés pour être trouvé : ██████ • ██████ • ██████*
*Plan d'action semaine 1 : ██████████████████*

👆 Débloque le rapport complet pour accéder à tout."""

    prompt_complet = f"""Tu es un expert en personal branding pour freelances.
Un freelance te donne ces infos :
- Compétences : {competences}
- Secteur : {secteur}
- Expérience : {experience}
- Client idéal : {client_type}
- Objectif mensuel : {objectif}€

Génère un rapport COMPLET et détaillé avec :
1. 🎯 Niche recommandée (très précis)
2. 💬 Pitch LinkedIn complet prêt à copier-coller
3. 💰 Tarifs recommandés (TJM et forfaits)
4. 🚀 Top 3 plateformes pour trouver des clients
5. 🔑 5 mots-clés SEO pour être trouvé
6. 📅 Plan d'action 30 jours

Sois concret, direct et personnalisé. Réponds en français."""

    message_gratuit = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt_gratuit}]
    )

    message_complet = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt_complet}]
    )

    rapport_gratuit = message_gratuit.content[0].text
    rapport_complet = message_complet.content[0].text
    session['rapport_complet'] = rapport_complet

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
                        "description": "Rapport complet : tarifs, plateformes, mots-clés SEO, plan 30 jours + chat illimité"
                    },
                    "unit_amount": 990,
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
    rapport_complet = session.get('rapport_complet', None)
    if not rapport_complet:
        return redirect(url_for('index'))
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
        return {"reponse": "🔒 Tu as utilisé tes 2 questions gratuites ! Débloque le rapport complet pour un chat illimité.", "locked": True}

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"""Tu es un assistant spécialisé uniquement dans le freelancing, le personal branding et la carrière professionnelle.
Si la question n'est pas liée à ces sujets, réponds : "Je suis spécialisé dans le freelancing et la carrière. Je ne peux pas répondre à cette question !"
Voici le rapport de l'utilisateur :
{rapport}
Question : {question}
Réponds de façon concise, pratique et personnalisée en français."""}]
    )
    return {"reponse": message.content[0].text, "locked": False}

if __name__ == "__main__":
    app.run(debug=True)