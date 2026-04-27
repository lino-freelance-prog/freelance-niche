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
1. 🎯 Score de niche X/10 avec explication en 1 phrase
2. 🎯 Niche recommandée (2 paragraphes précis et percutants)
3. 💬 Pitch LinkedIn COMPLET prêt à copier-coller
4. 💰 Fourchette de tarifs avec 2-3 options concrètes

Termine avec exactement ce texte :
---
🔒 **Rapport Premium — sections verrouillées**
*Plateforme n°1 recommandée : ██████████ — voici exactement comment créer ton profil pour apparaître en premier...*
*Mots-clés SEO : ██████ • ██████ • ██████ — utilisés par tes futurs clients pour te trouver*
*Plan d'action semaine 1 : Contacte ces ██████ types de prospects sur ██████ avec ce message...*
*Template de prospection personnalisé : "Bonjour ██████, j'ai remarqué que..."*

👆 Débloque tout pour 4,90€ — accès à vie."""

    prompt_complet = f"""Tu es un expert en personal branding pour freelances.
Un freelance te donne ces infos :
- Compétences : {competences}
- Secteur : {secteur}
- Expérience : {experience}
- Client idéal : {client_type}
- Objectif mensuel : {objectif}€

Génère un rapport COMPLET et détaillé avec :
1. 🎯 Score de niche X/10 avec explication détaillée
2. 🎯 Niche recommandée (très précis)
3. 💬 Pitch LinkedIn complet prêt à copier-coller
4. 💰 Tarifs recommandés (TJM et forfaits détaillés)
5. 🚀 Top 3 plateformes pour trouver des clients + stratégie
6. 🔑 5 mots-clés SEO pour être trouvé
7. 📅 Plan d'action 30 jours détaillé
8. 📧 Template de prospection personnalisé prêt à envoyer
9. 📞 Script d'appel client

Sois concret, direct et personnalisé. Réponds en français."""

    message_gratuit = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt_gratuit}]
    )

    message_complet = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
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
                        "description": "Rapport complet : tarifs, plateformes, mots-clés SEO, plan 30 jours, template prospection + chat illimité"
                    },
                    "unit_amount": 490,
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))