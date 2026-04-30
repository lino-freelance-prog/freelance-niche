from flask import Flask, render_template, request, session, redirect, url_for
import anthropic
import stripe
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.mail import Mail

load_dotenv()

app = Flask(__name__)
app.secret_key = "nicheai_secret_2024"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

def envoyer_email(destinataire, rapport):
    message = Mail(
        from_email="nicheai.contact@gmail.com",
        to_emails=destinataire,
        subject="🎯 Ton rapport NicheAI Premium",
        html_content=f"<h2>Ton rapport NicheAI Premium</h2><pre style='white-space:pre-wrap'>{rapport}</pre>"
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
    except Exception as e:
        print(f"Erreur email: {e}")

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
    email = session.get('email', None)
    if not rapport_complet:
        return redirect(url_for('index'))
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
        return {"reponse": "🔒 Tu as utilisé tes 2 questions gratuites ! Débloque le rapport complet pour un chat illimité."}

    reponse = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": f"Voici le rapport freelance:\n{rapport}\n\nQuestion: {question}"}]
    )
    return {"reponse": reponse.content[0].text}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)