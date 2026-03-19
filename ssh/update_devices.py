from tkinter import messagebox
from tqdm import tqdm
from . import utils
from . import comandos_ssh
import paramiko
import os


logger = utils.configurar_logger("update")
SUCCESS_DETAIL = "ZIP subido, checksum validado y update.sh ejecutado"


def _upload_file_with_progress(sftp, local_path, remote_path):
    file_size = os.path.getsize(local_path)
    with tqdm(total=file_size, unit="B", unit_scale=True, desc="Subiendo archivo") as progress_bar:
        def callback(bytes_transferred, bytes_total):
            progress_bar.update(bytes_transferred - progress_bar.n)

        sftp.put(local_path, remote_path, callback=callback)


def _remote_checksum(ssh_client, filepath, algorithm):
    _, stdout, stderr = ssh_client.exec_command(f"{algorithm}sum {filepath}")
    remote_checksum_output = stdout.read().decode().strip()
    remote_checksum = remote_checksum_output.split()[0] if remote_checksum_output else None
    if not remote_checksum:
        raise ValueError(f"No se pudo calcular el checksum remoto. Error: {stderr.read().decode()}")
    return remote_checksum


def _log_checksum_ok(ip, algorithm, local_checksum, remote_checksum):
    logger.info(f"[{ip}] Checksum local ({algorithm}): {local_checksum}")
    logger.info(f"[{ip}] Checksum remoto ({algorithm}): {remote_checksum}")
    logger.info(f"[{ip}] Integridad verificada: checksum OK")


def update_cabecera(ip_list, user, password, local_filepath):
    remote_filepath = "/home/ubuntu/update.zip"
    port = 22
    algorithm = "sha256"

    logger.info("Inicio update CA/LX")
    resp = messagebox.askyesno(
        "Confirmar actualizacion",
        f"Actualizar las cabeceras?\n\nIPs:\n{ip_list}\n\nZIP:\n{local_filepath}",
    )

    if not resp:
        logger.info("Update cancelado por usuario")
        return {"cancelled": True, "results": []}

    results = []
    for ip in ip_list:
        update_util = 0
        ssh = None
        transport = None
        sftp = None

        try:
            logger.info(f"Subiendo en: {ip}")
            ssh = utils.ssh_authentification(ip, user, password)
            if not ssh:
                raise RuntimeError("No se pudo establecer conexion SSH")

            cmd_check = [
                "[ -f /home/ubuntu/update.zip ] && echo 'update.zip exists' || echo 'update.zip not exists'",
                "[ -d /home/ubuntu/update ] && echo 'update directory exists' || echo 'update directory not exists'",
                "[ -f /home/ubuntu/util/he/updateHE.php ] && echo 'updateHE exists' || echo 'updateHE not exists'",
            ]
            for cmd in cmd_check:
                _, stdout, _ = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                if "update.zip exists" in output:
                    comandos_ssh.ssh_command(ssh, ["rm /home/ubuntu/update.zip"], password)
                if "update directory exists" in output:
                    comandos_ssh.ssh_command(ssh, ["rm -rf /home/ubuntu/update"], password)
                if "updateHE exists" in output:
                    update_util = 1

            transport = paramiko.Transport((ip, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            local_checksum = utils.calculate_checksum(local_filepath, algorithm)
            _upload_file_with_progress(sftp, local_filepath, remote_filepath)
            remote_checksum = _remote_checksum(ssh, remote_filepath, algorithm)

            if local_checksum != remote_checksum:
                raise RuntimeError("Fallo de integridad: checksum de update.zip no coincide")
            _log_checksum_ok(ip, algorithm, local_checksum, remote_checksum)

            if update_util == 1:
                cmd_update = ["nohup php /home/ubuntu/util/he/updateHE.php > /dev/null 2>&1 & sleep 1"]
                comandos_ssh.ssh_command(ssh, cmd_update, password)
                detail = SUCCESS_DETAIL
            else:
                local_he = "./ssh/updateHE.php"
                remote_he = "/home/ubuntu/updateHE.php"

                local_he_checksum = utils.calculate_checksum(local_he, algorithm)
                sftp.put(local_he, remote_he)
                remote_he_checksum = _remote_checksum(ssh, remote_he, algorithm)
                if local_he_checksum != remote_he_checksum:
                    raise RuntimeError("Fallo de integridad: checksum de updateHE.php no coincide")
                _log_checksum_ok(ip, algorithm, local_he_checksum, remote_he_checksum)

                cmd_update = [
                    "chown ubuntu:ubuntu /home/ubuntu/updateHE.php",
                    "chmod +x /home/ubuntu/updateHE.php",
                    "nohup php /home/ubuntu/updateHE.php > /dev/null 2>&1 & sleep 1",
                ]
                comandos_ssh.ssh_command(ssh, cmd_update, password)
                detail = SUCCESS_DETAIL

            results.append({"ip": ip, "status": "ok", "detail": detail})
            logger.info(f"[{ip}] Update finalizado")

        except Exception as e:
            logger.error(f"Error durante la transferencia en {ip}: {e}")
            results.append({"ip": ip, "status": "error", "detail": str(e)})
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
            if ssh:
                ssh.close()

    return {"cancelled": False, "results": results}


def update_imx(ip_list, user, password, local_filepath):
    remote_filepath = "/home/ubuntu/update.zip"
    port = 22
    algorithm = "sha256"

    logger.info("Inicio update IMX")
    resp = messagebox.askyesno(
        "Confirmar actualizacion",
        f"Actualizar las cabeceras?\n\nIPs:\n{ip_list}\n\nZIP:\n{local_filepath}",
    )

    if not resp:
        logger.info("Update cancelado por usuario")
        return {"cancelled": True, "results": []}

    results = []
    for ip in ip_list:
        ssh = None
        transport = None
        sftp = None

        try:
            logger.info(f"Subiendo en: {ip}")
            ssh = utils.ssh_authentification(ip, user, password)
            if not ssh:
                raise RuntimeError("No se pudo establecer conexion SSH")

            cmd_check = [
                "[ -f /home/ubuntu/update.zip ] && echo 'update.zip exists' || echo 'update.zip not exists'",
                "[ -d /var/www/simplicitygw/update ] && echo 'update directory exists' || echo 'update directory not exists'",
            ]
            for cmd in cmd_check:
                _, stdout, _ = ssh.exec_command(cmd)
                output = stdout.read().decode().strip()
                if "update.zip exists" in output:
                    comandos_ssh.ssh_command(ssh, ["rm /home/ubuntu/update.zip"], password)
                if "update directory exists" in output:
                    comandos_ssh.ssh_command(ssh, ["rm -rf /var/www/simplicitygw/update"], password)

            transport = paramiko.Transport((ip, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            local_checksum = utils.calculate_checksum(local_filepath, algorithm)
            _upload_file_with_progress(sftp, local_filepath, remote_filepath)
            remote_checksum = _remote_checksum(ssh, remote_filepath, algorithm)

            if local_checksum != remote_checksum:
                raise RuntimeError("Fallo de integridad: checksum de update.zip no coincide")
            _log_checksum_ok(ip, algorithm, local_checksum, remote_checksum)

            cmd = [
                f"unzip -P {password} /home/ubuntu/update.zip -d /var/www/simplicitygw/ > /dev/null 2>&1",
                "chmod +x /var/www/simplicitygw/update/update.sh > /dev/null 2>&1",
                "bash /var/www/simplicitygw/update/update.sh > /home/ubuntu/update.log 2>&1 &",
            ]
            comandos_ssh.ssh_command(ssh, cmd, password)

            results.append({
                "ip": ip,
                "status": "ok",
                "detail": SUCCESS_DETAIL,
            })
            logger.info(f"[{ip}] Update finalizado")

        except Exception as e:
            logger.error(f"Error durante la transferencia en {ip}: {e}")
            results.append({"ip": ip, "status": "error", "detail": str(e)})
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
            if ssh:
                ssh.close()

    return {"cancelled": False, "results": results}
