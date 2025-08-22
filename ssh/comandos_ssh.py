from . import utils

# Configurar logger
logger = utils.configurar_logger("cmds")
logs = []
resultados = [] 

########################################################
# Funcion para enviar comandos en la consola de SSH
########################################################
def ssh_command(client, cmds, password):
    resp_cmds = [] 
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
                        print("# -> error: ")
                        error = str(error).split("sudo:")[1].strip()
                        logger.error(error)
                        # Solo agregar a failed_cmds si el comando realmente falló
                        if "command not found" in error or "No such file or directory" in error:
                            logger.error(error)
                            #failed_cmds.append(cmd)  # Solo agregar comandos fallidos
                            logs.append(f"# -> Error del comando:\n{error}")
                    else:
                        logger.info("Comando aceptado.!")
                        logger.info("# *****************************************************#")
                        logs.append(f"# -> Respuesta del comando:\n{salida}")

                    return resp_cmds.append({
                        "cmd": cmd,
                        "stdout": salida,
                        "stderr": error
                    })
    except Exception as e:
        logger.error(f"# Error: Fallo al ejecutar el comando - {e}")

    #return failed_cmds  # Devolver los comandos que fallaron


########################################################
# Enviar comandos a todas las ips de un tag (Onomono)
########################################################
def command_all_ips(cmds, user, password, ips):
    respuesta = []
    # logger.info("# *****************************************************#")
    # logger.info("# -> IPs a enviar el comando: ")
    # logger.info(ips)
    # realizar comprobacion de comando
    # logger.info("# -> Comandos a enviar:")
    # logger.info(cmds)

    for ip in ips:
        logger.info("# *****************************************************#")
        logs.append(f"# Autentificando en: {ip}")
        # Conectarse mediante SSH
        client = utils.ssh_authentification(ip, user, password)

        # Ejecutar el comando si la conexión fue exitosa
        if client:
            exec_cmds = ssh_command(client, cmds, password)
            resultados.append({
                "IP" : ip
            })
            client.close()
        else:
            logger.error(f"No se puedo establecer conexion ssh en {ip}")
        print(f"# Finalizado en: {ip}")

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
