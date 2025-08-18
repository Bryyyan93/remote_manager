from tkinter import messagebox
from tqdm import tqdm
from . import utils
# from . import comandos_ssh
import paramiko
import os

# Configurar logger
logger = utils.configurar_logger("upload")


def upload_files(ip_list, user, password, local_filepath, remote_filepath):
    port = 22
    algorithm = 'sha256'

    logger.info("# *********************************************************#")
    logger.info("# -> En las siguientes cabeceras: ")
    logger.info(ip_list)
    logger.info("# -> Se subirá el fichero:")
    logger.info(local_filepath)
    resp = messagebox.askyesno("Confirmar:",
                               f"¿Subir los ficheros?\n\nIPs:\n{ip_list}\n\nZIP:\n{local_filepath}")
    logger.info("# *********************************************************#")

    if resp:
        for ip in ip_list:
            logger.info(f"# Subiendo en: {ip}")
            print(f"{user} y {password}")
            try:
                # Conexión SSH
                transport = paramiko.Transport((ip, port))
                transport.connect(username=user, password=password)
                # Inicializar SFTP
                sftp = paramiko.SFTPClient.from_transport(transport)
                # Obtener tamaño del archivo local
                file_size = os.path.getsize(local_filepath)
                # Calcular checksum del archivo local
                local_checksum = utils.calculate_checksum(local_filepath, algorithm)
                print(f"Checksum local ({algorithm}): {local_checksum}")
                # Definir una barra de progreso
                with tqdm(total=file_size, unit="B", unit_scale=True, desc="Subiendo archivo") as progress_bar:
                    def callback(bytes_transferred, bytes_total):
                        progress_bar.update(bytes_transferred - progress_bar.n)
                    # Subir archivo con barra de progreso
                    sftp.put(local_filepath, remote_filepath, callback=callback)
                logger.info("Archivo subido exitosamente.")
                # Ejecutar comando remoto para calcular el checksum
                ssh = utils.ssh_authentification(ip, user, password)
                # Comando para calcular checksum en el archivo remoto
                stdin, stdout, stderr = ssh.exec_command(f"{algorithm}sum {remote_filepath}")
                remote_checksum_output = stdout.read().decode().strip()
                remote_checksum = remote_checksum_output.split()[0] if remote_checksum_output else None
                if not remote_checksum:
                    raise ValueError(f"No se pudo calcular el checksum remoto. Error: {stderr.read().decode()}")
                print(f"Checksum remoto ({algorithm}): {remote_checksum}")
                # Comparar checksums
                if local_checksum == remote_checksum:
                    logger.info("✔ Integridad verificada: los checksums coinciden.")
                    logger.info("Fichero subido.!")
                else:
                    logger.error("❌ Fallo en la integridad: los checksums no coinciden.")
                logger.info("So long, and thanks for all the fish.")
                # Cerrar conexión
                sftp.close()
                transport.close()
                ssh.close()
            except Exception as e:
                logger.error(f"Error durante la transferencia: {e}")
    else:
        logger.info("# Saliendo...")
        logger.info("# So long, and thanks for all the fish.")
