# webui/router_ips.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os
import re, ast

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


@router.get("/ips", response_class=HTMLResponse)
async def ui_ips_home(request: Request):
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
            "ips.html",
            {"request": request, "tags": tags, "error": error},
            status_code=200,
        )

    return templates.TemplateResponse(
        "ips.html", {"request": request, "tags": tags, "error": None}
    )


@router.get("/ips/_list", response_class=HTMLResponse)
async def ui_ips_list(request: Request, tag: str):
    """
    Fragmento HTMX: pide JSON a /ips/{tag} y lo renderiza.
    No reescribe lógica, solo traduce JSON -> HTML.
    """
    try:
        async with httpx.AsyncClient(timeout=50) as client:
            r = await client.get(f"{BACKEND_URL}/all_ips/{tag}")
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as he:
        raise HTTPException(status_code=he.response.status_code, detail=str(he))
    except Exception as e:
        # Devuelve el parcial con un bloque de error
        return templates.TemplateResponse(
            "_ips_list.html",
            {"request": request, "ips": [], "error": f"Error: {e}", "tag": tag},
            status_code=200,
        )

    ips = _parse_ips_payload(data)
    return templates.TemplateResponse("_ips_list.html",
                                      {"request": request, "ips": ips, "error": None, "tag": tag})
