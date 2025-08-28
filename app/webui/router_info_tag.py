# webui/router_info_tag.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx, os, re, ast


router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="./app/templates")
# URL del backend.
BACKEND_URL = os.environ.get("UI_BACKEND_URL", "http://localhost:8000")


def _parse_ips_payload(payload):
    """
    Entrada posible (cualquiera de estas):
      - {"ips":[...]} | list[str] | str (con \n)
      - Bloque tipo:
          Tag: ElPedroso ->
          SIMs Online:
          {'id': '002369459', 'ip': '100.88.244.238'}
          ...
          SIMs offline:
          {'id': '002369460', 'ip': '100.88.244.239'}
    Devuelve: [{"id": str, "ip": str, "estado": "online"|"offline"|None}, ...]
    """
    # Normaliza a texto
    if isinstance(payload, dict) and "ips" in payload:
        src = payload["ips"]
        text = "\n".join(map(str, src)) if isinstance(src, list) else str(src)
    elif isinstance(payload, list):
        text = "\n".join(map(str, payload))
    else:
        text = str(payload)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out, estado = [], None

    for ln in lines:
        low = ln.lower()
        # encabezados
        if low.startswith("tag:"):
            continue
        if "sims online" in low:
            estado = "online"
            continue
        if "sims offline" in low:
            estado = "offline"
            continue

        # 1) Preferente: línea con dict Python {'id': '...', 'ip': '...'}
        if ln.startswith("{") and ln.endswith("}"):
            try:
                d = ast.literal_eval(ln)
                ip = d.get("ip") or d.get("IP")
                sim_id = d.get("id") or d.get("ID")
                if ip or sim_id:
                    out.append({"id": str(sim_id) if sim_id else "-",
                                "ip": str(ip) if ip else "-",
                                "estado": estado})
                    continue
            except Exception:
                pass  # caemos al regex

        # 2) Fallback regex (IP e ID con o sin comillas)
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
    Acepta:
      - str con el bloque "Tag: ... ID: 123, Status: ..., Usado: 1.2 MB, Periodo: monthly"
      - list[str] con ese mismo bloque
      - {"consumos": "..."} envoltorio
      - list[dict] ya normalizado (lo devuelve tal cual)

    Devuelve: (items:list[dict], raw:any)   # raw != None si no se pudo normalizar
    """
    # Caso ya normalizado
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload, None

    # Extraer el texto
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
    # acepta: str | list[str] | {"limites": "..."}
    if isinstance(payload, dict) and "limites" in payload:
        text = str(payload["limites"])
    elif isinstance(payload, list):
        text = "\n".join(map(str, payload))
    else:
        text = str(payload)

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
    Página principal: carga los 'tags' al abrir.
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
    Fragmento HTMX: pide JSON a /consumos/{tag} y lo renderiza.
    No reescribe lógica, solo traduce JSON -> HTML.
    """
    try:
        async with httpx.AsyncClient(timeout=50) as client:
            c = await client.get(f"{BACKEND_URL}/consumos/{tag}")
            c.raise_for_status()

            i = await client.get(f"{BACKEND_URL}/all_ips/{tag}")
            i.raise_for_status()

            li = await client.get(f"{BACKEND_URL}/limites/{tag}")
            li.raise_for_status()

            cons_items, cons_raw = _parse_consumos_payload(c.json())
            ips_items = _parse_ips_payload(i.json())
            lim_items = _parse_limites_payload(li.json())
    except httpx.HTTPStatusError as he:
        raise HTTPException(status_code=he.response.status_code, detail=str(he))
    except Exception as e:
        # Devuelve el parcial con un bloque de error
        return templates.TemplateResponse(
            "_router_info_tag_tabla.html",
            {"request": request, "raw": None, "error": f"Error: {e}", "tag": tag},
            status_code=200,
        )

    # Fusionar por ID
    idx = {}
    for it in cons_items:
        idx.setdefault(it["id"], {}).update({
            "id": it["id"],
            "usage_mb": it.get("usage_mb"),
            "period": it.get("period"),
            "conn_state": it.get("status"),  # por si ya viene
        })

    for it in ips_items:
        idx.setdefault(it["id"], {}).update({
            "id": it["id"],
            "ip": it.get("ip"),
            "conn_state": it.get("estado") or idx.get(it["id"], {}).get("conn_state"),
        })

    for it in lim_items:
        idx.setdefault(it["id"], {}).update({
            "id": it["id"],
            "limit_mb": it.get("limit_mb"),
            "limit_state": it.get("limit_state"),
        })

    rows = sorted(idx.values(), key=lambda x: x.get("id", ""))
    return templates.TemplateResponse(
        "_router_info_tag_tabla.html",
        {"request": request, "rows": rows, "error": None, "tag": tag},
    )
