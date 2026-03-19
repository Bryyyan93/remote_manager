from cryptography.fernet import Fernet

# Generar una clave y guardarla para su uso posterior
key = Fernet.generate_key()

# Guardar la clave en un archivo seguro (esto es importante para poder desencriptar después)
with open("apisecret_admin.key", "wb") as key_file:
    key_file.write(key)

# Crear el objeto Fernet con la clave generada
cipher_suite = Fernet(key)

# La API key que deseas encriptar
api_key = b"API_KEY_ONOMONDO"
# Encriptar la API key
cipher_text = cipher_suite.encrypt(api_key)
print(cipher_text.decode())  # 👈 ESTO es lo que va al .env
