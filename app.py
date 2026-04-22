from flask import Flask, render_template, request
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

    prompt = f"""Tu es un expert en personal branding pour freelances.
Un freelance te donne ces infos :
- Compétences : {competences}
- Secteur : {secteur}
- Expérience : {experience}
- Type de client idéal : {client_type}
- Objectif mensuel : {objectif}€

Génère un rapport structuré avec :
1. Sa niche recommandée (sois très précis)
2. Son pitch LinkedIn prêt à copier-coller
3. Ses tarifs recommandés (TJM et forfaits)
4. Les 3 meilleures plateformes pour lui
5. Les 5 mots-clés pour être trouvé par les bons clients

Sois concret, direct, et personnalisé. Réponds en français."""

    message = client.messages.create(model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    rapport = message.content[0].text
    return render_template("resultat.html", rapport=rapport)
@app.route("/chat", methods=["POST"])
def chat():
    import json
    data = request.get_json()
    question = data.get("question")
    rapport = data.get("rapport")

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"""Tu es un assistant spécialisé uniquement dans le freelancing, le personal branding, la carrière et le développement professionnel.

Si la question n'est pas liée à ces sujets, réponds poliment : "Je suis spécialisé dans le freelancing et la carrière professionnelle. Je ne peux pas répondre à cette question, mais je suis là pour t'aider sur ton positionnement, tes clients ou ta carrière !"

Voici le rapport de l'utilisateur :
{rapport}

Question : {question}

Réponds de façon concise, pratique et personnalisée en français."""}]
    )
    return {"reponse": message.content[0].text}
if __name__ == "__main__":
    app.run(debug=True)