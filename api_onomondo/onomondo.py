import time
from urllib.parse import urlencode

import requests
from ssh import utils

BASE_URL = "https://api.onomondo.com"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.6
SIMS_PAGE_LIMIT = 5000
logger = utils.configurar_logger("onomondo")


def _get(url, headers):
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.debug(f"GET {url} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429 and attempt < MAX_RETRIES:
                logger.warning(f"GET {url} -> 429 Too Many Requests; retrying")
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            if resp.status_code >= 400:
                logger.warning(f"GET {url} -> HTTP {resp.status_code}")
            else:
                logger.debug(f"GET {url} -> HTTP {resp.status_code}")
            return resp
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"GET {url} failed on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
    logger.error(f"GET {url} exhausted retries: {last_error}")
    raise requests.exceptions.RequestException(str(last_error))


def get_sim_info(headers, sim_id):
    url = f"{BASE_URL}/sims/{sim_id}"
    try:
        response = _get(url, headers)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                logger.error(f"GET /sims/{sim_id} devolvió JSON inválido")
                return None
        logger.warning(f"GET /sims/{sim_id} devolvió HTTP {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error consultando SIM {sim_id}: {e}")
        return None


def _append_query_params(url, params):
    query = urlencode({k: v for k, v in params.items() if v is not None})
    if not query:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{query}"


def _fetch_all_sims_pages(headers, extra_params=None):
    sims = []
    next_page = None
    page_number = 0
    params = {"limit": SIMS_PAGE_LIMIT}
    if extra_params:
        params.update(extra_params)

    while True:
        page_number += 1
        page_params = dict(params)
        if next_page:
            page_params["next_page"] = next_page
        url = _append_query_params(f"{BASE_URL}/sims", page_params)
        response = _get(url, headers)
        logger.info(f"Recuperando página {page_number} de /sims")

        if response.status_code != 200:
            raise ValueError(f"Error: {response.status_code}, {response.text}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError("La respuesta de /sims no contiene un JSON válido") from exc

        if not isinstance(data, dict):
            raise ValueError("La respuesta de /sims no tiene el formato esperado")

        page_sims = data.get("sims")
        if not isinstance(page_sims, list):
            raise ValueError("La respuesta de /sims no incluye una lista válida de SIMs")

        sims.extend(page_sims)
        next_page = data.get("next_page")
        logger.info(
            f"Página {page_number} de /sims: {len(page_sims)} SIMs, acumuladas {len(sims)}, "
            f"siguiente cursor={'sí' if next_page else 'no'}"
        )
        if not next_page:
            return {"sims": sims, "next_page": None}


def get_all_sims(headers):
    print("Obtener todas las sims")
    try:
        data = _fetch_all_sims_pages(headers)
        print("Respuesta exitosa!")
        return data
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error en la solicitud: {e}") from e
    except ValueError:
        raise


def _filter_sims_by_tag(sims, inst_tag):
    sims_with_tag = []
    for sim in sims:
        tags = sim.get("tags", [])
        for tag in tags:
            if tag.get("name") == inst_tag:
                sims_with_tag.append(sim)
                break
    return sims_with_tag


def get_sims_by_tag(headers, inst_tag):
    print("Obtener SIMs con un tag")
    try:
        data = get_all_sims(headers)
        sims = data.get("sims", [])
        sims_with_tag = _filter_sims_by_tag(sims, inst_tag)

        if sims_with_tag:
            return sims_with_tag
        return f"No se encontraron SIMs con el tag '{inst_tag}'"
    except ValueError as e:
        return f"Error en la solicitud: {e}"


def get_ips_by_tag(headers, inst_tag):
    print(f"API: Obteniendo las IPs de la instalacion con tag: {inst_tag}")
    try:
        data = get_all_sims(headers)
        sims = _filter_sims_by_tag(data.get("sims", []), inst_tag)
        ip_with_tag = []

        for sim in sims:
            ip = sim.get("ipv4")
            if ip:
                ip_with_tag.append(ip)

        if ip_with_tag:
            return f"API: tag: {inst_tag} -> {ip_with_tag}"
        return f"API: No se encontraron SIMs con el tag '{inst_tag}'"
    except ValueError as e:
        return f"API: Error en la solicitud: {e}"


def get_ids_by_tag(headers, inst_tag):
    try:
        sims = get_all_sims(headers).get("sims", [])
        data_with_tag = []

        for sim in _filter_sims_by_tag(sims, inst_tag):
            sim_id = sim.get("id")
            if sim_id:
                data_with_tag.append(sim_id)

        return data_with_tag
    except ValueError as e:
        print(f"Error en la solicitud: {e}")
        return []


def usage_by_tag(headers, inst_tag):
    ids_tag = get_ids_by_tag(headers, inst_tag)
    data_limit_tag = {}

    for sim_id in ids_tag:
        sim_data = get_sim_info(headers, sim_id)
        if not isinstance(sim_data, dict):
            continue

        data_limit = sim_data.get("data_limit", {})
        online = sim_data.get("online")
        if not data_limit:
            continue

        used = data_limit.get("used")
        total = data_limit.get("total")
        sim_type = data_limit.get("type")

        used_mb = round(used / 1_000_000, 2) if used is not None else 0
        total_mb = round(total / 1_000_000, 2) if total is not None else 0

        data_limit_tag[sim_id] = {
            "Online": online,
            "usado actual (MB)": used_mb,
            "limite total (MB)": total_mb,
            "tipo": sim_type,
        }

    if data_limit_tag:
        sorted_data = sorted(data_limit_tag.items(), key=lambda x: not bool(x[1].get("Online")))
        result = f"Tag: {inst_tag} ->\n"
        for sim_id, data in sorted_data:
            result += f"ID: {sim_id}\n Datos: {data}\n"
        return result
    return f"No se encontraron SIMs con el tag '{inst_tag}'"


def get_ips_status(headers, inst_tag):
    ids_tag = get_ids_by_tag(headers, inst_tag)
    ip_online = {}
    ip_offline = {}

    for sim_id in ids_tag:
        sim_data = get_sim_info(headers, sim_id)
        if not isinstance(sim_data, dict):
            continue

        online = sim_data.get("online")
        ipv4 = sim_data.get("ipv4")
        if online is True:
            ip_online[sim_id] = {"id": sim_id, "ip": ipv4}
        else:
            ip_offline[sim_id] = {"id": sim_id, "ip": ipv4}

    result = f"Tag: {inst_tag} ->\n"
    if ip_online:
        result += "SIMs Online:\n"
        for _, data in ip_online.items():
            result += f"{data}\n"
    if ip_offline:
        result += "SIMs offline:\n"
        for _, data in ip_offline.items():
            result += f"{data}\n"

    return result


def get_tags(headers):
    print("Obtener los tags")
    limit = 100
    url = f"{BASE_URL}/tags/search/tags?limit={limit}"

    try:
        response = _get(url, headers)
        print(f"Estado de la respuesta: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("Respuesta exitosa!")
            tags = data.get("result", [])
            inst_tag = []
            excluded_tags = {"sat", "uvax", "reserva", "produccion uvax", "ing"}

            for tag in tags:
                name_tag = tag.get("name")
                if name_tag and str(name_tag).strip().lower() not in excluded_tags:
                    inst_tag.append(name_tag)

            print(inst_tag)
            return inst_tag

        print(f"Error en la solicitud: {response.status_code}")
        return f"Error: {response.status_code}, {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud: {e}"
