import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from api_onomondo import onomondo
from ssh import utils

# Configurar logger
logger = utils.configurar_logger("api")
MAX_WORKERS = 6
BATCH_SIZE = 25
BATCH_PAUSE_SECONDS = 0.35
RETRY_WORKERS = 1
RETRY_PASSES = 2


def _limit_state(usado, limite):
    if usado > limite:
        return "Limite superado"
    if usado == limite:
        return "Limite alcanzado"
    if usado < limite - 5 and usado > limite - 10:
        return "Limite cercano"
    return "Limite no alcanzado"


def _build_row(sim_id, sim_data):
    data_limit = sim_data.get("data_limit", {}) or {}
    used = data_limit.get("used")
    total = data_limit.get("total")
    period = data_limit.get("type")
    used_mb = round(used / 1_000_000, 2) if used is not None else None
    total_mb = round(total / 1_000_000, 2) if total is not None else None
    online = sim_data.get("online")
    conn_state = "online" if online is True else "offline"
    limit_state = _limit_state(used_mb, total_mb) if used_mb is not None and total_mb is not None else None

    return {
        "id": str(sim_id),
        "ip": sim_data.get("ipv4"),
        "conn_state": conn_state,
        "usage_mb": used_mb,
        "limit_mb": total_mb,
        "period": period,
        "limit_state": limit_state,
    }


def _fetch_rows_batch(headers, sim_ids, max_workers):
    row_by_id = {}
    errors = []
    worker_count = min(max_workers, max(len(sim_ids), 1))

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {pool.submit(onomondo.get_sim_info, headers, sim_id): str(sim_id) for sim_id in sim_ids}
        for future in as_completed(futures):
            sim_id = futures[future]
            try:
                sim_data = future.result()
            except Exception as exc:
                errors.append({"sim_id": sim_id, "error": str(exc)})
                continue

            if not isinstance(sim_data, dict):
                errors.append({"sim_id": sim_id, "error": "No se pudo obtener información de la SIM"})
                continue

            row_by_id[sim_id] = _build_row(sim_id, sim_data)

    return row_by_id, errors


def _fetch_rows_by_id(headers, sim_ids):
    normalized_ids = [str(sim_id) for sim_id in sim_ids]
    if not normalized_ids:
        return {}, []

    row_by_id = {}
    pending_ids = normalized_ids
    final_errors = []

    for attempt in range(1, RETRY_PASSES + 2):
        if not pending_ids:
            break

        is_retry = attempt > 1
        attempt_rows = {}
        attempt_errors = []
        workers = RETRY_WORKERS if is_retry else MAX_WORKERS
        logger.info(
            f"Snapshot fetch attempt {attempt}: {len(pending_ids)} SIMs pendientes, "
            f"workers={min(workers, max(len(pending_ids), 1))}, batch_size={BATCH_SIZE}"
        )

        for index in range(0, len(pending_ids), BATCH_SIZE):
            batch_ids = pending_ids[index:index + BATCH_SIZE]
            batch_rows, batch_errors = _fetch_rows_batch(headers, batch_ids, workers)
            attempt_rows.update(batch_rows)
            attempt_errors.extend(batch_errors)

            if index + BATCH_SIZE < len(pending_ids):
                time.sleep(BATCH_PAUSE_SECONDS)

        row_by_id.update(attempt_rows)
        pending_ids = [err["sim_id"] for err in attempt_errors if err["sim_id"] not in row_by_id]

        if pending_ids:
            logger.warning(
                f"Intento {attempt} incompleto: {len(pending_ids)} SIMs siguen pendientes"
            )
            final_errors = attempt_errors
        else:
            final_errors = []

    if pending_ids:
        final_errors = [
            err for err in final_errors
            if err["sim_id"] in set(pending_ids)
        ]
        logger.warning(
            f"Fallo al recuperar {len(final_errors)} de {len(normalized_ids)} SIMs del snapshot"
        )
    else:
        final_errors = []

    return row_by_id, final_errors


def get_tag_snapshot(inst_tag):
    """
    Dataset unificado por tag para evitar repetir llamadas pesadas.
    """
    headers = utils.api_headers()
    ids_tag = onomondo.get_ids_by_tag(headers, inst_tag)
    if not isinstance(ids_tag, list) or not ids_tag:
        return {"tag": inst_tag, "rows": [], "errors": []}

    row_by_id, sim_errors = _fetch_rows_by_id(headers, ids_tag)
    rows = [row_by_id[str(sim_id)] for sim_id in ids_tag if str(sim_id) in row_by_id]
    rows.sort(key=lambda x: x.get("id", ""))
    errors = [{"tag": inst_tag, "sim_id": err["sim_id"], "error": err["error"]} for err in sim_errors]
    if errors:
        logger.warning(f"Snapshot del tag '{inst_tag}' incompleto: {len(errors)} SIMs con error")
    return {"tag": inst_tag, "rows": rows, "errors": errors}


def get_all_tags_snapshot():
    """
    Dataset unificado para todos los tags.
    Devuelve resultados parciales y acumula errores por tag.
    """
    headers = utils.api_headers()
    tags = onomondo.get_tags(headers)
    if not isinstance(tags, list):
        raise ValueError("No se pudo obtener la lista de tags")

    sims_payload = onomondo.get_all_sims(headers)
    if not isinstance(sims_payload, dict):
        raise ValueError("No se pudo obtener el inventario de SIMs")

    sims = sims_payload.get("sims", [])
    if not isinstance(sims, list):
        raise ValueError("No se pudo obtener una lista válida de SIMs")
    tag_set = {str(t) for t in tags}

    # Mapa tag -> ids usando una sola lectura del inventario /sims.
    ids_by_tag = {tag: [] for tag in tags}
    for sim in sims:
        sim_id = sim.get("id")
        if not sim_id:
            continue
        for sim_tag in sim.get("tags", []):
            sim_tag_name = sim_tag.get("name")
            if sim_tag_name in tag_set:
                ids_by_tag[sim_tag_name].append(sim_id)

    # Evita pedir la misma SIM muchas veces cuando está en varios tags.
    unique_ids = sorted({sim_id for ids in ids_by_tag.values() for sim_id in ids})
    row_by_id, sim_errors = _fetch_rows_by_id(headers, unique_ids)

    items = []
    errors = [{"sim_id": err["sim_id"], "error": err["error"]} for err in sim_errors]
    failed_sim_ids = {err["sim_id"] for err in sim_errors}
    for tag in tags:
        try:
            tag_ids = ids_by_tag.get(tag, [])
            rows = [row_by_id[str(sim_id)] for sim_id in tag_ids if str(sim_id) in row_by_id]
            rows.sort(key=lambda x: x.get("id", ""))
            items.append({"tag": tag, "rows": rows})
            missing_ids = [
                str(sim_id)
                for sim_id in tag_ids
                if str(sim_id) not in row_by_id and str(sim_id) not in failed_sim_ids
            ]
            for sim_id in missing_ids:
                errors.append({"tag": tag, "sim_id": sim_id, "error": "La SIM no pudo incluirse en el snapshot"})
        except Exception as e:
            errors.append({"tag": tag, "error": str(e)})

    if sim_errors:
        logger.warning(
            f"Snapshot global incompleto: {len(sim_errors)} SIMs no devolvieron detalle desde Onomondo"
        )

    return {"items": items, "errors": errors}


########################################################
# Extraer las IP desde la API de Onomondo
########################################################
def ip_list_api_mono(inst_tag):
    snapshot = get_tag_snapshot(inst_tag)
    rows = snapshot.get("rows", [])
    return [r["ip"] for r in rows if r.get("conn_state") == "online" and r.get("ip")]


########################################################
# Obtener la info de datos de todas las ips de un tag (Onomondo)
########################################################
def get_usage(inst_tag):
    snapshot = get_tag_snapshot(inst_tag)
    rows = snapshot.get("rows", [])
    salida = [f"Tag: {inst_tag}"]

    for r in rows:
        status = "Conectada" if r.get("conn_state") == "online" else "Desconectada"
        usado = r.get("usage_mb") if r.get("usage_mb") is not None else "?"
        tipo = r.get("period") if r.get("period") else "?"
        salida.append(f"ID: {r.get('id')}, Status: {status}, Usado: {usado} MB, Periodo: {tipo}\n")

    resultado = "\n".join(salida)
    logger.info(resultado)
    return resultado


########################################################
# Obtener limites de datos de un tag (Onomondo)
########################################################
def get_limit(inst_tag):
    snapshot = get_tag_snapshot(inst_tag)
    rows = snapshot.get("rows", [])
    salida = [f"Tag: {inst_tag}"]

    for r in rows:
        usado = r.get("usage_mb") if r.get("usage_mb") is not None else "?"
        limite = r.get("limit_mb") if r.get("limit_mb") is not None else "?"
        estado = r.get("limit_state") if r.get("limit_state") else "Desconocido"
        salida.append(f"ID: {r.get('id')}, Usado: {usado} MB, Limite: {limite} MB, Estado: {estado}\n")

    resultado = "\n".join(salida)
    logger.info(resultado)
    return resultado
