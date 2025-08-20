# from fastapi import FastAPI
from app.main import app
from fastapi.testclient import TestClient
# from unittest.mock import patch
# from ssh import utils, api_petitions as api

client = TestClient(app)


# Test de root
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

##############################################################
# GUI_API
##############################################################
# Obtener tags de las instalaciones
