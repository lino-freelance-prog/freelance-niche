# CLAUDE.md — NicheAI (freelance-niche)

## Le projet

NicheAI (nicheai.fr) : SaaS de rapports de positionnement pour freelances, propulsé par l'API Anthropic. Modèle freemium : rapport gratuit (teaser) + rapport premium à 19,90 € via Stripe. Statut : auto-entrepreneur, SIRET 10564150000019 (mentions légales officielles en ligne).

## Stack

- **Backend** : Flask (Python), PostgreSQL via Flask-SQLAlchemy, Flask-Login (comptes utilisateurs + sauvegarde des rapports)
- **IA** : API Anthropic — Sonnet pour les rapports premium, Haiku pour le gratuit. Web search activé sur les endpoints premium uniquement.
- **Paiement** : Stripe (live), 19,90 €. Codes promo actifs : TIKTOK5, LINO1811 (secret).
- **Emails** : SendGrid, domaine vérifié, expéditeur nicheai.contact@gmail.com
- **Hébergement** : Render plan Starter (7 $/mois). Domaine nicheai.fr chez OVH.
- **Design** : dark violet/purple + touches or, rapports en accordéon interactif, animations de chargement, parser markdown custom (corrigé).

## Environnements

- Laptop : `/c/Users/Proprietaire/Documents/freelance-niche`
- PC fixe : `/c/Users/lycit/freelance-niche`
- Repo GitHub : `lino-freelance-prog/freelance-niche`
- Toujours vérifier `git pull` avant de travailler (deux machines).

## ⚠️ Pièges connus (déjà vécus — ne pas reproduire)

1. **requirements.txt DOIT rester en UTF-8** — une corruption UTF-16 a déjà cassé le déploiement Render. Après toute modification : vérifier l'encodage.
2. **Pas de Poetry** — pip uniquement (conflits Poetry/pip déjà rencontrés sur Render).
3. **Routes Flask dupliquées** — déjà causé des crashs : vérifier qu'une route n'existe pas avant d'en ajouter une.
4. **Échappement JS dans les templates Jinja** — bugs d'escaping déjà rencontrés : attention aux chaînes contenant quotes/apostrophes injectées dans du JS.
5. Déploiement : push sur GitHub → auto-deploy Render. Vérifier les logs Render après chaque déploiement.

## Fonctionnalités premium (prompts)

Le rapport premium inclut : profil Malt optimisé, bio LinkedIn, messages de prospection, email de relance, plan de contenu 30 jours. Quatre champs de formulaire ajoutés pour la personnalisation approfondie.

## Roadmap produit (5 étapes définies)

Personnalisation → données marché → dashboard de suivi → preuve sociale. Priorité actuelle : **valider avec de vrais clients payants** (stade actuel évalué 6/10 — le produit est construit, la traction reste à prouver).

## Marketing

- TikTok Business + Instagram Business créés et actifs (contenu court + carrousels, esthétique noir/violet/or)
- Code promo TIKTOK5 lié aux campagnes TikTok

## Règles de travail

- Fichiers complets prêts à l'emploi, pas de snippets partiels.
- Tester en local avant de pousser.
- Ne jamais toucher aux clés API/secrets dans le code — variables d'environnement Render uniquement.
