# app/main.py
from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel, Field
from api_onomondo import onomondo
from ssh import utils, api_petitions as api, comandos_ssh as ssh
from app.version import VERSION
from app.webui.router_info_tag import router as ui_router


app = FastAPI(title="Remote Manager", version=VERSION)
app.include_router(ui_router)
utils.configurar_logger("cmds")


# Body del request para envio de comandos
class RunCmdReq(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    cmds: List[str] = Field(..., min_length=1)   # comandos a ejecutar
    ips: List[str] = Field(..., min_length=1)    # lista de IPs destino


# Pantalla principla
@app.get("/")
def root():
    return {"message": "Hello"}


##############################################################
# GUI_API
##############################################################
# Obtener tags de las instalaciones
@app.get("/tags")
def get_tags():
    try:
        tags = onomondo.get_tags(utils.api_headers())
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Obtener lista de IPs online de un tag
@app.get("/ips/{tag}")
def get_ips(tag):
    try:
        ips = api.ip_list_api_mono(tag)
        return {"ips": ips}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Obtener IPs online y offline de un tag
@app.get("/all_ips/{tag}")
def get_all_ips(tag):
    try:
        all_ips = onomondo.get_ips_status(utils.api_headers(), tag)
        return all_ips
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Ver los consumos de datos del tag
@app.get("/consumos/{tag}")
def get_consumos(tag):
    try:
        consumos = api.get_usage(tag)
        return {"consumos": consumos}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Ver los limites de datos del tag
@app.get("/limites/{tag}")
def get_limites(tag):
    try:
        limites = api.get_limit(tag)
        return {"limites": limites}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Dataset unificado por tag (optimizado para Web UI)
@app.get("/tag_data/all")
def get_all_tag_data():
    try:
        return api.get_all_tags_snapshot()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Dataset unificado por tag (optimizado para Web UI)
@app.get("/tag_data/{tag}")
def get_tag_data(tag):
    try:
        return api.get_tag_snapshot(tag)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


##############################################################
# GUI_COMMANDS
##############################################################
# Enviar comandos a los dispositivos
@app.post("/comandos")
def post_comandos(req: RunCmdReq):
    try:
        return ssh.command_all_ips(req.cmds, req.username, req.password, req.ips)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
