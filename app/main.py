# webapp/main.py
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from api_onomondo import onomondo
from ssh import utils, api_petitions as api

app = FastAPI(title="Remote Manager", version="0.1.0")

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

