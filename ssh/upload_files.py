from tkinter import messagebox
from tqdm import tqdm
from . import utils
import paramiko
import os

logger = utils.configurar_logger("upload")


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


def upload_files(ip_list, user, password, local_filepath, remote_filepath):
    port = 22
    algorithm = "sha256"

    logger.info("Inicio upload")
    resp = messagebox.askyesno(
        "Confirmar",
        f"Subir los ficheros?\n\nIPs:\n{ip_list}\n\nLocal:\n{local_filepath}\n\nRemoto:\n{remote_filepath}",
    )

    if not resp:
        logger.info("Upload cancelado por usuario")
        return {"cancelled": True, "results": []}

    results = []
    for ip in ip_list:
        transport = None
        sftp = None
        ssh = None
        try:
            logger.info(f"Subiendo en: {ip}")

            transport = paramiko.Transport((ip, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            local_checksum = utils.calculate_checksum(local_filepath, algorithm)
            _upload_file_with_progress(sftp, local_filepath, remote_filepath)

            ssh = utils.ssh_authentification(ip, user, password)
            if not ssh:
                raise RuntimeError("No se pudo establecer conexion SSH para validar checksum remoto")

            remote_checksum = _remote_checksum(ssh, remote_filepath, algorithm)

            if local_checksum != remote_checksum:
                raise RuntimeError("Fallo de integridad: checksum no coincide")

            results.append({
                "ip": ip,
                "status": "ok",
                "detail": f"Fichero subido y validado en {remote_filepath}",
            })

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
