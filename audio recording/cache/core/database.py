from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import datetime

# Base de données URL depuis les variables d'environnement
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transcriptflow.db")

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Création des tables
class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # "transcription", "youtube_extraction", "video_extraction", "tts_generation"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(String, nullable=True)  # Informations supplémentaires (nom fichier, durée, etc.)

    user = relationship("User", back_populates="activities")



# Modèle utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relations
    api_keys = relationship("APIKey", back_populates="user")
    transcriptions = relationship("Transcription", back_populates="user")
# Ajouter cette relation à la classe User existante
    User.activities = relationship("UserActivity", back_populates="user")

# Modèle clé API
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service = Column(String)  # "openai", etc.
    key_value = Column(String)

    user = relationship("User", back_populates="api_keys")


# Modèle transcription
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    duration = Column(Float)
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(String)

    user = relationship("User", back_populates="transcriptions")


# Modèle abonnement
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan = Column(String)  # "free", "standard", "premium"
    active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")


User.subscriptions = relationship("Subscription", back_populates="user")


# Fonction pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()