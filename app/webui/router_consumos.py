# webui/router_consumos.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os
import re


router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="./app/templates")

# URL del backend.
BACKEND_URL = os.environ.get("UI_BACKEND_URL", "http://localhost:8000")


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


@router.get("/consumos", response_class=HTMLResponse)
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
            "consumos.html",
            {"request": request, "tags": tags, "error": error},
            status_code=200,
        )

    return templates.TemplateResponse(
        "consumos.html", {"request": request, "tags": tags, "error": None}
    )


@router.get("/consumos/_list", response_class=HTMLResponse)
async def ui_consumos_list(request: Request, tag: str):
    """
    Fragmento HTMX: pide JSON a /consumos/{tag} y lo renderiza.
    No reescribe lógica, solo traduce JSON -> HTML.
    """
    try:
        async with httpx.AsyncClient(timeout=50) as client:
            r = await client.get(f"{BACKEND_URL}/consumos/{tag}")
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as he:
        raise HTTPException(status_code=he.response.status_code, detail=str(he))
    except Exception as e:
        # Devuelve el parcial con un bloque de error
        return templates.TemplateResponse(
            "_consumos_list.html",
            {"request": request, "items": [], "raw": None, "error": f"Error: {e}"},
            status_code=200,
        )

    items, raw = _parse_consumos_payload(data)
    return templates.TemplateResponse(
        "_consumos_list.html",
        {"request": request, "items": items, "raw": raw, "error": None, "tag": tag},
    )
