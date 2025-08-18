from tkinter import messagebox
from tqdm import tqdm
from . import utils
from . import comandos_ssh
import paramiko
import os


# Configurar logger
logger = utils.configurar_logger("update")


def update_cabecera(ip_list, user, password, local_filepath):
    remote_filepath = "/home/ubuntu/update.zip"  # Ruta en el servidor
    port = 22
    algorithm = 'sha256'

    logger.info("# *****************************************************#")
    logger.info("# -> Se van a actualizar las siguientes cabeceras: ")
    logger.info(ip_list)
    logger.info("# -> Con la siguiente version:")
    logger.info(local_filepath)
    resp = messagebox.askyesno("Confirmar actualización",
                               f"¿Actualizar las cabeceras?\n\nIPs:\n{ip_list}\n\nZIP:\n{local_filepath}")
    logger.info("# *****************************************************#")

    if resp:
        for ip in ip_list:
            logger.info(f"# Subiendo en: {ip}")
            update_util = 0
            try:
                # Conexión SSH
                ssh = utils.ssh_authentification(ip, user, password)
                # Comprobar si los archivos existen antes de eliminarlos
                cmd_check = [
                    "[ -f /home/ubuntu/update.zip ] && echo 'update.zip exists' || echo 'update.zip not exists'",
                    "[ -d /home/ubuntu/update ] && echo 'update directory exists' || echo 'update directory not exists'",
                    "[ -f /home/ubuntu/util/he/updateHE.php ] && echo 'updateHE exists' || echo 'updateHE not exists'"
                ]
                for cmd in cmd_check:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode().strip()
                    if 'update.zip exists' in output:
                        logger.info("El archivo update.zip ya existe en el servidor.")
                        comandos_ssh.ssh_command(ssh, ["rm /home/ubuntu/update.zip"], password)
                    if 'update directory exists' in output:
                        logger.info("El directorio update ya existe en el servidor.")
                        comandos_ssh.ssh_command(ssh, ["rm -rf /home/ubuntu/update"], password)
                    if 'updateHE exists' in output:
                        logger.info("El archivo updateHE.php ya existe en el servidor.")
                        update_util = 1

                # Conexión SFTP
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
                    logger.info("Fichero subido., se procede a la actualizacion.!")
                    if update_util == 1:
                        cmd_update = ["nohup php /home/ubuntu/util/he/updateHE.php > /dev/null 2>&1 & sleep 1"]
                        comandos_ssh.ssh_command(ssh, cmd_update, password)
                    elif update_util == 0:
                        local_he = "./ssh/updateHE.php"
                        remote_he = "/home/ubuntu/updateHE.php"

                        local_he_checksum = utils.calculate_checksum(local_he, algorithm)

                        sftp.put(local_he, remote_he)
                        print("Archivo subido exitosamente.")
                        # Comando para calcular checksum en el archivo remoto
                        stdin, stdout, stderr = ssh.exec_command(f"{algorithm}sum {remote_he}")
                        remote_he_output = stdout.read().decode().strip()
                        remote_he_checksum = remote_he_output.split()[0] if remote_he_output else None
                        if not remote_he_checksum:
                            raise ValueError(f"No se pudo calcular el checksum remoto. Error: {stderr.read().decode()}")
                        print(f"Checksum remoto ({algorithm}): {remote_checksum}")
                        if local_he_checksum == remote_he_checksum:
                            print("Fichero he subido")
                            cmd_update = ["chown ubuntu:ubuntu /home/ubuntu/updateHE.php",
                                          "chmod +x /home/ubuntu/updateHE.php",
                                          "nohup php /home/ubuntu/updateHE.php > /dev/null 2>&1 & sleep 1"
                                          ]
                            comandos_ssh.ssh_command(ssh, cmd_update, password)
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


def update_imx(ip_list, user, password, local_filepath):
    remote_filepath = "/home/ubuntu/update.zip"
    port = 22
    algorithm = 'sha256'

    logger.info("# *****************************************************#")
    logger.info("# -> Se van a actualizar las siguientes cabeceras: ")
    logger.info(ip_list)
    # realizar comprobacion de comando
    logger.info("# -> Con la siguiente version:")
    logger.info(local_filepath)
    resp = messagebox.askyesno("Confirmar actualización",
                               f"¿Actualizar las cabeceras?\n\nIPs:\n{ip_list}\n\nZIP:\n{local_filepath}")
    logger.info("# *****************************************************#")

    if resp:
        for ip in ip_list:
            logger.info(f"# Subiendo en: {ip}")
            try:
                # Conexión SSH
                ssh = utils.ssh_authentification(ip, user, password)
                # Comprobar si los archivos existen antes de eliminarlos
                cmd_check = [
                    "[ -f /home/ubuntu/update.zip ] && echo 'update.zip exists' || echo 'update.zip not exists'",
                    "[ -d /var/www/simplicitygw/update ] && echo 'update directory exists' || echo 'update directory not exists'"
                ]
                for cmd in cmd_check:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode().strip()
                    if 'update.zip exists' in output:
                        print("El archivo update.zip ya existe en el servidor.")
                        comandos_ssh.ssh_command(ssh, ["rm /home/ubuntu/update.zip"], password)
                    if 'update directory exists' in output:
                        print("El directorio update ya existe en el servidor.")
                        comandos_ssh.ssh_command(ssh, ["rm -rf /var/www/simplicitygw/update"], password)

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
                    logger.info("Actualizar cabecera")
                    cmd = [
                        f"unzip -P {password} /home/ubuntu/update.zip -d /var/www/simplicitygw/",
                        "chmod +x /var/www/simplicitygw/update/update.sh",
                        "bash /var/www/simplicitygw/update/update.sh > /home/ubuntu/update.log 2>&1 &"
                    ]
                    comandos_ssh.ssh_command(ssh, cmd, password)
                    logger.info("Cabecera actualizada")
                    logger.info("-------------------------------------------------------------------------")
                else:
                    logger.error("❌ Fallo en la integridad: los checksums no coinciden. No se actualiza")
                # Cerrar conexión
                sftp.close()
                transport.close()
                ssh.close()
            except Exception as e:
                logger.error(f"Error durante la transferencia: {e}")
    else:
        logger.info("# Saliendo...")
        logger.info("# So long, and thanks for all the fish.")
