# scripts/migrate_db.py
from core.database import Base, engine

def migrate_database():
    """Met à jour la structure de la base de données."""
    Base.metadata.create_all(bind=engine)
    print("Base de données mise à jour avec succès!")

if __name__ == "__main__":
    migrate_database()