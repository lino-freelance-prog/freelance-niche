from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    premium = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    rapports = db.relationship("Rapport", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Rapport(db.Model):
    __tablename__ = "rapports"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    titre = db.Column(db.String(255), default="Rapport de positionnement")
    secteur = db.Column(db.String(255))
    contenu = db.Column(db.Text, nullable=False)
    type_rapport = db.Column(db.String(20), default="gratuit")
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Champs de personnalisation avancee (etape 2 roadmap)
    missions_recentes = db.Column(db.Text)
    tarif_actuel = db.Column(db.String(100))
    zone_geo = db.Column(db.String(255))
    contrainte_principale = db.Column(db.String(255))
