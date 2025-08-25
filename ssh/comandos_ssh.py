from . import utils
from typing import List, Dict, Any

# Configurar logger
logger = utils.configurar_logger("cmds")


########################################################
# Funcion para enviar comandos en la consola de SSH
########################################################
def ssh_command(client, cmds, password) -> List[Dict[str, str]]:
    resp_cmds: List[Dict[str, str]] = []
    try:
        for cmd in cmds:
            logger.info(f"# Ejecutando comando: {cmd}")
            # Ejecutar el comando con sudo, pasando la contraseña
            rcmd = f"echo {password} | sudo -S {cmd}"
            # Ejecutar el comando remoto
            stdin, stdout, stderr = client.exec_command(rcmd)

            # leer la salida del comando
            salida = stdout.read().decode()
            error = stderr.read().decode()

            # impirmir la salida del comando
            if error:
                # Ignorar mensajes de sudo no críticos
                if "sudo" in error or "password for" in error:
                    if "sudo:" in error:
                        error = str(error).split("sudo:")[1].strip()
                        if "command not found" in error or "No such file or directory" in error:
                            logger.error(error)
                    else:
                        logger.info("Comando aceptado.!")
                        logger.info("# *****************************************************#")
                        logger.info(f"# -> Respuesta del comando:\n{salida}")
                resp_cmds.append({
                    "cmd": cmd,
                    "stdout": salida,
                    "stderr": error
                })
        return resp_cmds
    except Exception as e:
        logger.error(f"# Error: Fallo al ejecutar el comando - {e}")


########################################################
# Enviar comandos a todas las ips de un tag (Onomono)
########################################################
def command_all_ips(cmds, user, password, ips) -> Dict[str, Any]:
    # resultados = []
    resultados: List[Dict[str, Any]] = []
    logs = []

    for ip in ips:
        logger.info("# *****************************************************#")
        logs.append(f"# Autentificando en: {ip}")
        # Conectarse mediante SSH
        client = utils.ssh_authentification(ip, user, password)
        # Ejecutar el comando si la conexión fue exitosa
        if not client:
            msg = f"No se puedo establecer conexion ssh en {ip}"
            logger.error(msg)
            resultados.append({
                "ip": ip,
                "error": msg,
                "commands": []})
            logs.append(f"Error: {msg}")
            continue
        try:
            per_ip = ssh_command(client, cmds, password)
            resultados.append({
                "ip": ip,
                "commands": per_ip
            })
        except Exception as e:
            msg = f"Fallo ejecutando comandos en {ip}: {e}"
            logger.error(msg)
            resultados.append({
                "ip": ip,
                "error": str(e),
                "commands": []
            })
        finally:
            client.close()
            fin = f"# Finalizado en: {ip}"
            logger.info(fin)
            logs.append(fin)

    return {"status": "ok", "results": resultados, "logs": logs}


def sql_command(password, querys, opc):
    # Para SQL
    # ejem de comando a enviar
    # sqlite3 /tmp/ramdisk/WSdatabase/cabeceraws.db "DELETE FROM tbl_suscription WHERE type = 'energyNode';"
    tmp_ddbb_dir = "/tmp/ramdisk/WSdatabase/cabeceraws.db"
    cmds = []

    for query in querys:
        cmd = f"sqlite3 {tmp_ddbb_dir} \"{query}\""
        logger.info(f"# Ejecutando comando: {cmd}")

        cmds.append(cmd)

    command_all_ips(cmds, password, opc)
