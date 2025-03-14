import random
import string
import bcrypt

# 🔹 Fonction pour générer un mot de passe aléatoire sécurisé
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# 🔹 Génère un mot de passe aléatoire
random_password = generate_random_password()

# 🔹 Hachage du mot de passe avec bcrypt
hashed_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 🔹 Affiche le mot de passe en clair et son hash
print(f"🔑 Mot de passe généré : {random_password}")
print(f"🔒 Mot de passe hashé   : {hashed_password}")
