import requests


#####################################################################################################################
# FUNCIONES PARA MOSTRAR INFO A CARA PERRO
#####################################################################################################################
# Función para obtener info de una sim en especifico
def get_sim_info(headers, sim_id):
    # print("Obtener la info de una sim en especifico")
    url = f'https://api.onomondo.com/sims/{sim_id}'

    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()  # Obtener la respuesta en formato JSON
            return data
        else:
            return f"Error: {response.status_code}, {response.text}"  # Mensaje de error si falla la solicitud
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"  # Manejo de excepciones


#####################################################################################################################
# Obtener todas las SIMs con todos los datos a cara perro
#####################################################################################################################
def get_all_sims(headers):
    print("Obtener todas las sims")
    url = 'https://api.onomondo.com/sims'

    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)
        print(f"Estado de la respuesta: {response.status_code}")

        # Comprobar si la respuesta fue exitosa (código 200)
        if response.status_code == 200:
            data = response.json()  # Obtener la respuesta en formato JSON
            print("Respuesta exitosa!")
            return data
        else:
            print(f"Error en la solicitud: {response.status_code}")
            return f"Error: {response.status_code}, {response.text}"  # Mensaje de error si falla la solicitud
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"  # Manejo de excepciones


#####################################################################################################################
# FUNCIONES CON USO DE TAG
# Obtener la info de las sims de un tag
#####################################################################################################################
def get_sims_by_tag(headers, inst_tag):
    print("Obtener SIMs con un tag")
    url = 'https://api.onomondo.com/sims'
    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)
        print(f"Estado de la respuesta: {response.status_code}")

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            print("Respuesta exitosa!")
            data = response.json()  # Obtener la respuesta en formato JSON

            sims = data.get("sims", [])  # Obtener la lista de SIMs, o una lista vacía si no existe
            sims_with_tag = []  # Lista para almacenar SIMs que tengan el tag buscado

            # Recorrer cada SIM
            for sim in sims:
                tags = sim.get("tags", [])  # Obtener los tags de cada SIM

                # Comprobar si alguno de los tags tiene el nombre deseado
                for tag in tags:
                    if tag.get("name") == inst_tag:
                        sims_with_tag.append(sim)  # Añadir la SIM a la lista si tiene el tag

            # Verificar si encontramos SIMs con el tag
            if sims_with_tag:
                return sims_with_tag  # Devolver las SIMs con el tag
            else:
                return f"No se encontraron SIMs con el tag '{inst_tag}'"
        else:
            print(f"Error en la solicitud: {response.status_code}")
            return f"Error: {response.status_code}, {response.text}"  # Manejo de error en la solicitud
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"  # Manejo de excepciones


#####################################################################################################################
# Obtener las IPs de las sims de un tag para una instalacion
#####################################################################################################################
def get_ips_by_tag(headers, inst_tag):
    print(f"API: Obteniendo las IPs de la instación con tag: {inst_tag}")
    url = 'https://api.onomondo.com/sims'

    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)
        print(f"API: Estado de la respuesta: {response.status_code}")

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            print("API: Respuesta exitosa!")
            data = response.json()  # Obtener la respuesta en formato JSON

            sims = data.get("sims", [])  # Obtener la lista de SIMs, o una lista vacía si no existe
            ip_with_tag = []  # Lista para almacenar SIMs que tengan el tag buscado

            # Bucle que recorre todas las sims y obtiene los tags de todas las instalaciones
            for sim in sims:
                tags = sim.get("tags", [])  # Obtener los tags de cada SIM
                # Bucle que recorre todas los tags para buscar el tag en especifico
                for tag in tags:
                    if tag.get("name") == inst_tag:
                        ip = sim.get("ipv4")
                        if ip:
                            ip_with_tag.append(ip)  # Añadir la SIM a la lista si tiene el tag
                        break

            if ip_with_tag:
                for ip in ip_with_tag:
                    # Imprimir y devolver todas las IPs encontradas
                    # print(f"IPs encontradas con el tag: {inst_tag} -> {ip_with_tag}")
                    return f"API: tag: {inst_tag} -> {ip_with_tag}"
            else:
                return f"API: No se encontraron SIMs con el tag '{inst_tag}'"
        else:
            print(f"API: Error en la solicitud: {response.status_code}")
            return f"API: Error: {response.status_code}, {response.text}"  # Manejo de error en la solicitud
    except requests.exceptions.RequestException as e:
        return f"API: Error en la solicitud: {e}"  # Manejo de excepciones


########################################################################################################################
# Obtener las Ids de las SIM por tag
########################################################################################################################
def get_ids_by_tag(headers, inst_tag):
    # print("Obtener el uso de datos de la instalacion del tag (API)")
    url = 'https://api.onomondo.com/sims'

    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)
        print(f"Respuesta API: {response.status_code}")

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # print("Respuesta exitosa!")
            data = response.json()  # Obtener la respuesta en formato JSON

            sims = data.get("sims", [])  # Obtener la lista de SIMs, o una lista vacía si no existe
            data_with_tag = []  # Lista para almacenar SIMs que tengan el tag buscado

            # Bucle que recorre todas las sims y obtiene los tags de todas las instalaciones
            for sim in sims:
                tags = sim.get("tags", [])  # Obtener los tags de cada SIM
                # Bucle que recorre todas los tags para buscar el tag en especifico
                for tag in tags:
                    if tag.get("name") == inst_tag:
                        id = sim.get("id")
                        data_with_tag.append(id)

            if data_with_tag:
                return data_with_tag
            else:
                return f"No se encontraron SIMs con el tag '{inst_tag}'"
        else:
            print(f"Error en la solicitud: {response.status_code}")
            return f"Error: {response.status_code}, {response.text}"  # Manejo de error en la solicitud
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"  # Manejo de excepciones


########################################################################################################################
# Obtener las limitaciones de consumo  y el consumo actual por tag
########################################################################################################################
def usage_by_tag(headers, inst_tag):
    # print("Obtener el uso de datos de la instación del tag")
    ids_tag = get_ids_by_tag(headers, inst_tag)
    # print(ids_tag)
    data_limit_tag = {}  # diccionario para almacenar SIMs que tengan el tag buscado

    for id in ids_tag:
        try:
            # Obtener la información de la SIM (un diccionario)
            url_id = get_sim_info(headers, id)
            # print(f"Haciendo solicitud GET a: {url_id}")

            # Acceder directamente al campo 'data_limit'
            data_limit = url_id.get("data_limit", {})  # Obtener data_limit o dic vacio
            online = url_id.get("online")
            if data_limit:
                used = data_limit.get("used")
                total = data_limit.get("total")
                type = data_limit.get("type")

                # Convertir de bytes a megabytes y redondear a 2 decimales
                if used is not None:
                    used_mb = round(used / 1_000_000, 2)  # Convertir de bytes a MB
                else:
                    used_mb = 0
                if total is not None:
                    total_mb = round(total / 1_000_000, 2)  # Convertir de bytes a MB
                else:
                    total_mb = 0

                # Agregar los datos al diccionario usando el ID como clave
                data_limit_tag[id] = {
                    "Online" : online,
                    "usado actual (MB)": used_mb,
                    "limite total (MB)": total_mb,
                    "tipo": type
                }

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")  # Manejo de excepciones

    # Verificar si se han encontrado datos y devolverlos al final del bucle
    if data_limit_tag:
        # Ordenar los resultados, primero Online=True, luego Online=False
        sorted_data = sorted(data_limit_tag.items(), key=lambda x: not x[1]["Online"])
        # Formatear la salida para que sea legible
        result = f"Tag: {inst_tag} ->\n"
        for id, data in sorted_data:
            result += f"ID: {id}\n Datos: {data}\n"
        return result
    else:
        return f"No se encontraron SIMs con el tag '{inst_tag}'"


########################################################################################################################
# Obtener las IPs de las SIM y listarlas si estan online o no
########################################################################################################################
def get_ips_status(headers, inst_tag):
    ids_tag = get_ids_by_tag(headers, inst_tag)
    ip_online = {}  # diccionario para almacenar SIMs que este online
    ip_offline = {}  # diccionario para almacenar SIMs que este offline

    for id in ids_tag:
        try:
            # Obtener la información de la SIM
            url_id = get_sim_info(headers, id)
            online = url_id.get("online")
            ipv4 = url_id.get("ipv4")
            if online is True:
                # Agregar los datos al diccionario usando el ID como clave
                ip_online[id] = {
                    "id" : id,
                    "ip": ipv4
                }
            else:
                ip_offline[id] = {
                    "id" : id,
                    "ip": ipv4
                }

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")  # Manejo de excepciones

    result = f"Tag: {inst_tag} ->\n"
    # Verificar si se han encontrado datos y devolverlos al final del bucle
    if ip_online:
        # Formatear la salida para que sea legible
        result += "SIMs Online:\n"
        for id, data in ip_online.items():
            result += f"{data}\n"
    if ip_offline:
        # Formatear la salida para que sea legible
        result += "SIMs offline:\n"
        for id, data in ip_offline.items():
            result += f"{data}\n"

    return result


########################################################################################################################
# Obtener todos los tags de las instalaciones
########################################################################################################################
def get_tags(headers):
    print("Obtener los tags")
    limit = 100  # Ver todas los tags con un limite de 100
    url = f'https://api.onomondo.com/tags/search/tags?limit={limit}'

    try:
        # Hacer la solicitud GET
        response = requests.get(url, headers=headers)
        print(f"Estado de la respuesta: {response.status_code}")

        # Comprobar si la respuesta fue exitosa (código 200)ono
        if response.status_code == 200:
            data = response.json()  # Obtener la respuesta en formato JSON
            print("Respuesta exitosa!")
            tags = data.get("result", [])  # Obtener la lista de tags, o una lista vacía si no existe
            inst_tag = []  # Lista para almacenar tags de las instalaciones

            for tag in tags:
                name_tag = tag.get("name")
                inst_tag.append(name_tag)  # Añadir el nombre del tag a la lista

            print(inst_tag)
            return inst_tag
        else:
            print(f"Error en la solicitud: {response.status_code}")
            return f"Error: {response.status_code}, {response.text}"  # Mensaje de error si falla la solicitud
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"  # Manejo de excepciones
