from api_onomondo import onomondo
from ssh import utils
import ast

# Configurar logger
logger = utils.configurar_logger("api")


########################################################
# Extraer las IP desde la API de Onomono
########################################################
def ip_list_api_mono(inst_tag):
    print("-> Llamada API")
    headers = utils.api_headers()
    # Obtener lista de nodos desde la peticion API
    list_ips = []
    resp = onomondo.get_ips_status(headers, inst_tag)

    logger.info(resp)

    is_online_section = False

    for line in resp.splitlines():
        if "SIMs Online:" in line:
            is_online_section = True
            continue
        if "SIMs offline:" in line:
            is_online_section = False
            continue

        # Si estamos en la sección online, extraer las IPs
        if is_online_section:
            try:
                # Usar eval() o ast.literal_eval para convertir la cadena de diccionario a un objeto Python
                data = eval(line.strip())
                ip = data.get("ip")
                if ip:
                    list_ips.append(ip)
            except Exception as e:
                logger.error(f"Error al obtener los valores {e}")
                # Si no se puede hacer eval, simplemente pasamos a la siguiente línea
                pass
    return list_ips


########################################################
# Obtener la info de datos de todas las ips de un tag (Onomono)
########################################################
def get_usage(inst_tag):
    headers = utils.api_headers()

    data_use = onomondo.usage_by_tag(headers, inst_tag)

    # Si es un string con contenido, lo parseamos
    salida = [f"Tag: {inst_tag}"]
    current_id = None

    for line in data_use.splitlines():
        line = line.strip()
        if line.startswith("ID:"):
            current_id = line.split("ID:")[1].strip()
        elif line.startswith("Datos:") and current_id:
            try:
                # Extraer el diccionario de la línea
                dict_str = line.split("Datos:")[1].strip()
                # Convertir la cadena de diccionario a un objeto Python
                datos = ast.literal_eval(dict_str)
                online = datos.get("Online", "¿?")
                if online is True:
                    online = "Conectada"
                elif online is False:
                    online = "Desconectada"
                usado = datos.get("usado actual (MB)", "¿?")
                tipo = datos.get("tipo", "¿?")
                salida.append(f"ID: {current_id}, Status: {online}, Usado: {usado} MB, Periodo: {tipo}\n")
            except Exception as e:
                salida.append(f"Error al procesar los datos: {e}\n")
            current_id = None  # Reinicia current_id para la siguiente iteración
    resultado = "\n".join(salida)
    logger.info(resultado)
    return resultado


########################################################
# Obtener limites de datos de un tag (Onomono)
########################################################
def get_limit(inst_tag):
    headers = utils.api_headers()

    data_limit = onomondo.usage_by_tag(headers, inst_tag)

    # Si es un string con contenido, lo parseamos
    salida = [f"Tag: {inst_tag}"]
    current_id = None

    for line in data_limit.splitlines():
        line = line.strip()
        if line.startswith("ID:"):
            current_id = line.split("ID:")[1].strip()
        elif line.startswith("Datos:") and current_id:
            try:
                # Extraer el diccionario de la línea
                dict_str = line.split("Datos:")[1].strip()
                # Convertir la cadena de diccionario a un objeto Python
                datos = ast.literal_eval(dict_str)
                usado = datos.get("usado actual (MB)", "¿?")
                limite = datos.get("limite total (MB)", "¿?")
                if usado > limite:
                    Estado = "Limite superado"
                elif usado == limite :
                    Estado = "Limite alcanzado"
                elif usado < limite - 5 and usado > limite - 10:
                    Estado = "Limite cercano"
                else:
                    Estado = "Limite no alcanzado"
                salida.append(f"ID: {current_id}, Usado: {usado} MB, Limite: {limite} MB, Estado: {Estado}\n")
            except Exception as e:
                salida.append(f"Error al procesar los datos: {e}\n")
            current_id = None  # Reinicia current_id para la siguiente iteración
    resultado = "\n".join(salida)
    logger.info(resultado)
    return resultado
