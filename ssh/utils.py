import paramiko
import hashlib
from cryptography.fernet import Fernet
import logging
import tkinter as tk


########################################################
# Hacer el header para la peticion API
########################################################
def api_headers():
    # Encriptado, hay q usar encript_pass para q funciones y el secret.key correspondiente
    # idem_noadmin = "gAAAAABnGjh_4L_ze765LFObDR6HLClqZfkjPa9zaaNXML8GHbKSYVF_tdeeFOHcJ-lanq923erPx6T1BCSw2eeevGEBFMygQUeECupa5MiXNdrvxMJEQLb47yOVcXg8-00uTCDgRzK27sNFQJ-77rL4W-FsP5q0je8QxAa7KTs3oKwFdIjQM8A="
    idem_admin = "gAAAAABn4Qd5tZvTtmcKaHMEmEFPpIlC9nsIq77LsCk5T_Nib2dOVPqsveOrVeS_WTAbHP0QGivXY6Qt32YQwEGUmT0dcSJMl9csUYWmreCmJASBYd2Q7QvhJV_jh1ZpVK6KH0o2i13nkTlnB7Rp3pHNJhlC4TzxQp8pgL4l487Z5ILwahlXiNQ="
    # Leer la clave previamente guardada
    with open("./secrets/apisecret_admin.key", "rb") as key_file:
        key = key_file.read()
    # Crear el objeto Fernet con la clave
    cipher_suite = Fernet(key)
    api_idem = cipher_suite.decrypt(idem_admin)

    # Header
    headers = {
        'authorization': api_idem  # Añade el accesskey al header
    }

    return headers


########################################################
# Funcion para autentificarse a la cabecera con SSH
########################################################
def ssh_authentification(ip, user, password):
    # Crear un cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Aceptar claves de host automáticamente
    try:
        # Conectarse a una máquina remota
        ssh.connect(ip, username=user, password=password)
        return ssh
    except paramiko.AuthenticationException:
        print("# Error: Fallo en la autentificación")
    except Exception as e:
        print(f"# Error: Fallo al conectarse: {e}")


########################################################
# Funcion para calcular el checksum de un archivo
########################################################
def calculate_checksum(filepath, algorithm):
    """Calcula el checksum de un archivo local."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()


########################################################
# Funcion para redirigir los mensajes
########################################################
def configurar_logger(nombre="app", nivel=logging.DEBUG, handler_personalizado=None):
    logger = logging.getLogger(nombre)
    logger.setLevel(nivel)
    # Formato por defecto
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Evita duplicar handlers si ya está configurado
    if not logger.handlers:
        # Handler por defecto (consola)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Añadir handler personalizado si no existe ya uno del mismo tipo
    if handler_personalizado:
        tipo_handler = type(handler_personalizado)
        ya_existe = any(isinstance(h, tipo_handler) for h in logger.handlers)
        if not ya_existe:
            handler_personalizado.setFormatter(formatter)
            logger.addHandler(handler_personalizado)

    return logger


class TkinterHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.after(0, self._insert_text, msg)

    def _insert_text(self, msg):
        try:
            if self.widget.winfo_exists():
                self.widget.config(state="normal")
                self.widget.insert(tk.END, msg + "\n")
                self.widget.yview(tk.END)
                self.widget.config(state="disabled")
        except tk.TclError:
            # El widget ya no existe
            pass
