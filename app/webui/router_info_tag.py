# webui/router_info_tag.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx, os, re, ast


# Router de la UI. Se monta bajo /ui para no mezclar con la API JSON.
router = APIRouter(prefix="/ui", tags=["ui"])
# Carpeta de plantillas Jinja2
templates = Jinja2Templates(directory="./app/templates")
# URL del backend.
BACKEND_URL = os.environ.get("UI_BACKEND_URL", "http://localhost:8000")


def _parse_ips_payload(payload):
    """
    Normaliza la respuesta de /all_ips/{tag} a una lista de dicts con estructura:
      [{"id": str, "ip": str, "estado": "online"|"offline"|None}, ...]
    """
    # Normaliza a texto
    if isinstance(payload, dict) and "ips" in payload:
        src = payload["ips"]
        text = "\n".join(map(str, src)) if isinstance(src, list) else str(src)
    elif isinstance(payload, list):
        text = "\n".join(map(str, payload))
    else:
        text = str(payload)

    # Limpieza de líneas y estado de sección
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out, estado = [], None

    for ln in lines:
        low = ln.lower()
        # Quitar encabezados que no contienen datos
        if low.startswith("tag:"):
            continue
        # Detectar sección (afecta a las filas siguientes)
        if "sims online" in low:
            estado = "online"
            continue
        if "sims offline" in low:
            estado = "offline"
            continue

        # Preferente: línea con dict Python -> parseo seguro
        if ln.startswith("{") and ln.endswith("}"):
            try:
                d = ast.literal_eval(ln)  # evita eval(), solo estructuras literales
                ip = d.get("ip") or d.get("IP")
                sim_id = d.get("id") or d.get("ID")
                if ip or sim_id:
                    out.append({"id": str(sim_id) if sim_id else "-",
                                "ip": str(ip) if ip else "-",
                                "estado": estado})
                    continue
            except Exception:
                # Si falla (formato extraño), caemos al regex
                pass

        # Fallback: extraer IP e ID con regex (acepta comillas y distintos separadores)
        ip_m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", ln)
        id_m = re.search(r"(?:['\"]?id['\"]?\s*[:=]\s*['\"]?)(\d+)", ln, re.I)
        if ip_m or id_m:
            out.append({
                "id": id_m.group(1) if id_m else "-",
                "ip": ip_m.group(1) if ip_m else "-",
                "estado": estado
            })

    # Deduplicado por (ip,id)
    seen, uniq = set(), []
    for x in out:
        k = (x.get("ip"), x.get("id"))
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def _parse_consumos_payload(payload):
    """
    Normaliza la respuesta de /consumos/{tag}.
    """
    # Caso ya normalizado (JSON list[dict])
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload, None

    # Extraer texto de distintas envolturas
    text = None
    if isinstance(payload, dict) and "consumos" in payload:
        text = payload["consumos"]
    elif isinstance(payload, list) and payload and isinstance(payload[0], str):
        text = "\n".join(payload)
    elif isinstance(payload, str):
        text = payload

    if not isinstance(text, str):
        # No es texto reconocible → devolver raw
        return [], payload

    # Quitar encabezado "Tag: ..."
    # y extraer líneas de detalle con regex robusto (coma o punto como decimal)
    pattern = re.compile(
        r"ID:\s*(\d+),\s*Status:\s*([^,]+),\s*Usado:\s*([\d\.,]+)\s*MB,\s*Periodo:\s*([^\s,]+)",
        re.IGNORECASE,
    )

    items = []
    for m in pattern.finditer(text):
        _id = m.group(1).strip()
        status = m.group(2).strip()
        usage_txt = m.group(3).strip().replace(",", ".")
        try:
            usage = float(usage_txt)
        except ValueError:
            usage = usage_txt  # si viene algo raro, lo dejamos como texto
        period = m.group(4).strip()
        items.append({"id": _id, "usage_mb": usage, "period": period, "status": status})

    if items:
        return items, None
    # No coincidió el patrón → mostramos crudo
    return [], text


def _parse_limites_payload(payload):
    """
    Normaliza la respuesta de /limites/{tag} a una lista de dicts:
      [{'id', 'usage_mb_lim', 'limit_mb', 'limit_state'}, ...]

    Acepta:
      - {"limites": "..."} | list[str] | str con líneas:
          "ID: 002369459, Usado: 17.51 MB, Limite: 50.0 MB, Estado: Limite no alcanzado"
    """
    # Homogeneizar a texto
    if isinstance(payload, dict) and "limites" in payload:
        text = str(payload["limites"])
    elif isinstance(payload, list):
        text = "\n".join(map(str, payload))
    else:
        text = str(payload)

    # Regex de 4 grupos: id, usado, límite, estado
    pat = re.compile(
        r"ID:\s*(\d+),\s*Usado:\s*([\d\.,]+)\s*MB,\s*Limite:\s*([\d\.,]+)\s*MB,\s*Estado:\s*([^\n]+)",
        re.I,
    )
    out = []
    for m in pat.finditer(text):
        _id = m.group(1).strip()
        usado = m.group(2).strip().replace(",", ".")
        limite = m.group(3).strip().replace(",", ".")
        estado = m.group(4).strip()
        # Convertir a float si es posible (si no, dejar string)
        try:
            usado = float(usado)
        except ValueError:
            pass
        try:
            limite = float(limite)
        except ValueError:
            pass
        out.append({"id": _id, "usage_mb_lim": usado, "limit_mb": limite, "limit_state": estado})
    return out


# ---------- UI ----------
@router.get("/info_tag", response_class=HTMLResponse)
async def ui_consumos_home(request: Request):
    """
    Página principal de 'Info por tag'.
    Requisito: cargar los tags al abrir, sin romper si /tags falla.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BACKEND_URL}/tags")
            r.raise_for_status()
            payload = r.json()
            tags = payload.get("tags", []) if isinstance(payload, dict) else payload
    except Exception as e:
        # Si falla, muestra página con mensaje de error y sin tags.
        tags = []
        error = f"No se pudieron cargar los tags: {e}"
        return templates.TemplateResponse(
            "router_info_tag.html",
            {"request": request, "tags": tags, "error": error},
            status_code=200,
        )

    return templates.TemplateResponse(
        "router_info_tag.html", {"request": request, "tags": tags, "error": None}
    )


@router.get("/info_tag/_tabla", response_class=HTMLResponse)
async def ui_consumos_list(request: Request, tag: str):
    """
    Parcial HTMX que construye la tabla:
      - Llama a /consumos/{tag}, /all_ips/{tag}, /limites/{tag}
      - Parsea cada respuesta de forma tolerante
      - Fusiona por 'id'
      - Devuelve '_router_info_tag_tabla.html' con 'rows'
    """
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(f"{BACKEND_URL}/tag_data/{tag}")
            r.raise_for_status()
            payload = r.json()
    except Exception as e:
        return templates.TemplateResponse(
            "_router_info_tag_tabla.html",
            {"request": request, "raw": None, "error": f"Error al consultar backend: {e}", "tag": tag},
            status_code=200,
        )
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    return templates.TemplateResponse(
        "_router_info_tag_tabla.html",
        {"request": request, "rows": rows, "error": None, "tag": tag},
    )
