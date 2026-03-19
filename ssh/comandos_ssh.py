from . import utils
from typing import List, Dict, Any
import paramiko

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


########################################################
# Cambio en ntp y tiempo de espera
########################################################
def change_ntp_imx():
    imx = "-u postgres psql -d simplicity -t -A -c"  # -t -A quita bordes y formato
    user = ""
    password = ""
    min = 15  # minutos
    seg = min * 60
    ntps = "0.es.pool.ntp.org;1.es.pool.ntp.org;ntp.uvax.es"

    ips = ["10.10.2.1"]

    # pasos para cambiar ntp en imx8
    def run_querys(query):
        rcmd = f"echo {password} | sudo -S {imx} \"{query}\""
        stdin, stdout, stderr = ssh.exec_command(rcmd)
        print(rcmd)

        # leer la salida del comando
        salida = stdout.read().decode()

        return salida.splitlines()
    for ip in ips:
        try:
            print(f"Conenctando a {ip}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip , username=user , password=password)

            # OBTENER NTP Y MODIFICAR
            # paso 1 obtener id de app_deviceclass
            print("paso 1")
            q1 = "select id from app_deviceclass where name='CPU';"
            s1 = run_querys(q1)[0]
            # print(f"Paso 1 -> {s1}")

            # paso 2 obtener id de app_device
            print("paso 2")
            q2 = f"select id from app_device where \\\"talqClass_id\\\"={s1};"
            s2 = run_querys(q2)[0]
            # print(f"Paso 2:-> {s2}")

            # paso 3 obtener id de function
            print("paso 3")
            q3 = f"select id from app_function where \\\"device_id\\\"={s2} and \\\"type\\\"='BasicFunction';"
            s3 = run_querys(q3)[0]
            # print(f"Paso 3:-> {s3}")

            # paso 4 obtener ntpServers_id
            print("paso 4")
            q4 = f"select \\\"ntpServers_id\\\" from app_basicfunction where function_id={s3};"
            s4 = run_querys(q4)[0]
            # print(f"Paso 4:-> {s4}")

            # paso 5 obtener id de app_attribute
            print("paso 5")
            q5 = f"select id from app_attribute where id={s4};"
            run_querys(q5)[0]
            # print(f"Paso 5:-> {s5}")

            # paso 6 obtener id de app_attributestringarray
            print("paso 6")
            q6 = f"select id from app_attributestringarray where attribute_id={s4};"
            s6 = run_querys(q6)[0]
            # print(f"Paso 6:-> {s6}")

            # paso 7 actualizar valores NTP
            print("paso 7")
            q7 = f"update app_attributestringarray set \\\"value\\\"='{ntps}' where id={s6};"
            run_querys(q7)[0]
            # print(f"Paso 7:-> {s7}")

            cntp = f"select * from app_attributestringarray where id={s6};"
            sntp = run_querys(cntp)
            print(f"check:-> {sntp}")

            # OBTENER NTP SINCRO TIME Y MODIFICAR
            # paso 8 sacar id de ntpSynchPeriod
            print("paso 8")
            q8 = f"select \\\"ntpSynchPeriod_id\\\" from app_basicfunction where function_id={s3};"
            s8 = run_querys(q8)[0]
            # print(f"Paso 8:-> {s8}")

            # paso 9 sacar id de ntpSynchPeriod
            print("paso 9")
            q9 = f"select id from app_attribute where id={s8};"
            s9 = run_querys(q9)[0]
            # print(f"Paso 8:-> {s9}")

            cai = f"select * from app_attributeinteger where attribute_id={s9};"
            sai = run_querys(cai)
            print(f"check:-> {sai}")

            # paso 11 sacar id de ntpSynchPeriod
            print("paso 11")
            q11 = f"update app_attributeinteger set \\\"value\\\"={min} where attribute_id={s9};"
            run_querys(q11)[0]
            # print(f"Paso 10:-> {s11}")

            cai = f"select * from app_attributeinteger where attribute_id={s9};"
            sai = run_querys(cai)
            print(f"check:-> {sai}")

            # CAMBIO de horas a minutos
            # paso 12 actualizar los segundos
            q12 = f"UPDATE background_task set \\\"repeat\\\"={seg} where \\\"queue\\\"='ntpSynch';"
            run_querys(q12)
            # print(f"Paso 12:-> {s12}")

            cs = "SELECT repeat FROM background_task where \\\"queue\\\"='ntpSynch';"
            ss = run_querys(cs)
            print(f"check:-> {ss}")
            print("---------------------------------------------")

        except Exception as e:
            print(f"Error de conexion: {e}")
        finally:
            ssh.close()
