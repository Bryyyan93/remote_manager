from . import utils

# Configurar logger
logger = utils.configurar_logger("cmds")


########################################################
# Funcion para enviar comandos en la consola de SSH
########################################################
def ssh_command(client, cmds, password):
    failed_cmds = []

    if client is None:
        logger.error("# No se pudo ejecutar el comando porque no se estableció la conexión SSH")
        return

    try:
        for cmd in cmds:
            logger.info(f"# Ejecutando comando: {cmd}")
            # Ejecutar el comando con sudo, pasando la contraseña
            rcmd = f"echo {password} | sudo -S {cmd}"
            # Ejecutar el comando remoto
            stdin, stdout, stderr = client.exec_command(rcmd)

            # leer la salida del comando
            output = stdout.read().decode()
            error = stderr.read().decode()

            # impirmir la salida del comando
            if error:
                # Ignorar mensajes de sudo no críticos
                if "sudo" in error or "password for" in error:
                    if "sudo:" in error:
                        print("# -> error: ")
                        error = str(error).split("sudo:")[1].strip()
                        logger.error(error)
                        # Solo agregar a failed_cmds si el comando realmente falló
                        if "command not found" in error or "No such file or directory" in error:
                            logger.error(error)
                            failed_cmds.append(cmd)  # Solo agregar comandos fallidos
                    else:
                        logger.info("Comando aceptado.!")
                        logger.info("# *****************************************************#")

            if output:
                print("# -> Respuesta del comando:")
                logger.info(output)

    except Exception as e:
        logger.error(f"# Error: Fallo al ejecutar el comando - {e}")

    return failed_cmds  # Devolver los comandos que fallaron


########################################################
# Enviar comandos a todas las ips de un tag (Onomono)
########################################################
def command_all_ips(cmds, user, password, ips):
    failed_cmds_report = []
    # logger.info("# *****************************************************#")
    # logger.info("# -> IPs a enviar el comando: ")
    # logger.info(ips)
    # realizar comprobacion de comando
    # logger.info("# -> Comandos a enviar:")
    # logger.info(cmds)

    for ip in ips:
        logger.info("# *****************************************************#")
        logger.info(f"# Autentificando en: {ip}")
        # Conectarse mediante SSH
        client = utils.ssh_authentification(ip, user, password)

        # Ejecutar el comando si la conexión fue exitosa
        if client:
            failed_cmds = ssh_command(client, cmds, password)
            if failed_cmds:
                for cmd in failed_cmds:  # Solo agregar los comandos que fallaron
                    if cmd not in failed_cmds_report:
                        failed_cmds_report[cmd] = []  # Crear una lista para las IPs que fallaron
                    failed_cmds_report[cmd].append(ip)  # Agregar la IP a la lista de fallos del comando
            client.close()
        else:
            logger.error(f"No se puedo establecer conexion ssh en {ip}")
        print(f"# Finalizado en: {ip}")
    return failed_cmds_report  # Devolver el diccionario con el reporte de fallos


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
