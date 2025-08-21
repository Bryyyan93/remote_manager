# app/main.py
from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel, Field
from api_onomondo import onomondo
from ssh import utils, api_petitions as api, comandos_ssh as ssh

app = FastAPI(title="Remote Manager", version="0.1.0")


# Body del request para envio de comandos
class RunCmdReq(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    cmds: List[str] = Field(..., min_items=1)   # comandos a ejecutar
    ips: List[str] = Field(..., min_items=1)    # lista de IPs destino


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


# Obtener IPs de un tag
@app.get("/ips/{tag}")
def get_ips(tag):
    try:
        ips = api.ip_list_api_mono(tag)
        return {"ips": ips}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Ver los consumos de datos del tag
@app.get("/consumos/{tag}")
def get_consumos(tag):
    try:
        consumos = api.get_usage(tag)
        return {"Uso": consumos}
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


##############################################################
# GUI_COMMANDS
##############################################################
# Enviar comandos a los dispositivos
@app.post("/comandos")
def post_comandos(req: RunCmdReq):
    try:
        result = ssh.command_all_ips(req.cmds, req.username, req.password, req.ips)

        # Muchas implementaciones de gui/ssh imprimen por logger y no retornan nada.
        # Si `result` es None, al menos devuelve OK.
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


##############################################################
# GUI_UPDATE
##############################################################
