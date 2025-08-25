# from fastapi import FastAPI
from app.main import app
from fastapi.testclient import TestClient
from unittest.mock import patch
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
@patch("app.main.onomondo.get_tags")
@patch("app.main.utils.api_headers")
def test_get_tags(mock_headers, mock_tags):
    mock_headers.return_value = {'authorization': "fake"}
    mock_tags.return_value = ["tag1", "tag2"]

    response = client.get("/tags")

    assert response.status_code == 200
    assert response.json() == {"tags": ["tag1", "tag2"]}


# Obtener IPs de un tag
@patch("app.main.api.ip_list_api_mono")
def test_get_ips(mock_tag):
    mock_tag.return_value = ["ip1", "ip2"]

    response = client.get("/ips/pedroso")

    assert response.status_code == 200
    assert response.json() == {"ips": ["ip1", "ip2"]}


# Ver los consumos de datos del tag
@patch("app.main.api.get_usage")
def test_get_consumos(mock_tag):
    mock_tag.return_value = ["ID", "status", "uso", "periodo"]

    response = client.get("/consumos/pedroso")

    assert response.status_code == 200
    assert response.json() == {"Uso": ["ID", "status", "uso", "periodo"]}


# Ver los limites de datos del tag
@patch("app.main.api.get_limit")
def test_get_limites(mock_tag):
    mock_tag.return_value = ["Usado", "Limite", "Estado"]

    response = client.get("/limites/pedroso")

    assert response.status_code == 200
    assert response.json() == {"limites": ["Usado", "Limite", "Estado"]}
