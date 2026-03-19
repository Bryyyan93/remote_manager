from pathlib import Path
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os, logging
import paramiko, hashlib
import os, logging
import paramiko, hashlib
import tkinter as tk


########################################################
# Hacer el header para la peticion API
########################################################
def api_headers():
    # Carpeta base del proyecto = subir 1 nivel desde ssh/
    project_root = Path(__file__).resolve().parents[1]   # sube de ssh/ a raíz del repo

    # Buscar carpeta secrets en cualquier sitio dentro de ese root
    secrets_dir = project_root / "secrets"
    env_path = secrets_dir / ".env"
    key_path = secrets_dir / "apisecret_admin.key"

    # Si no existen, dar error claro
    if not secrets_dir.exists():
        raise FileNotFoundError(f"No se encontró {secrets_dir}")
    if not env_path.exists():
        raise FileNotFoundError(f"No se encontró {env_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"No se encontró {key_path}")

    # Cargar variables de entorno
    load_dotenv(dotenv_path=env_path)

    idem_admin = os.getenv("IDEM_ADMIN")
    if not idem_admin:
        raise RuntimeError(f"No se encontró IDEM_ADMIN en {env_path}")

    idem_admin = idem_admin.strip()
    # Cargar clave Fernet
    key = key_path.read_bytes()
    cipher = Fernet(key)
    api_idem = cipher.decrypt(idem_admin.encode()).decode()

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
