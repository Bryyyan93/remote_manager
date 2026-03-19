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
# Usamos el decorador @patch para simular (mockear) funciones concretas.
@patch("app.main.onomondo.get_tags")  # Simula la función get_tags() que obtiene los tags desde la API
@patch("app.main.utils.api_headers")  # Simula la función api_headers() que crea los headers de autenticación
# La función de test recibe los mocks como argumentos (en orden inverso)
def test_get_tags(mock_headers, mock_tags):
    # Simulamos que api_headers() devuelve un diccionario de autorización falso
    mock_headers.return_value = {'authorization': "fake"}
    # Simulamos que get_tags() devuelve una lista de tags estática
    mock_tags.return_value = ["tag1", "tag2"]

    # Usamos un cliente de pruebas (TestClient) para hacer una petición HTTP GET a la ruta "/tags"
    response = client.get("/tags")

    # Verificamos que la respuesta tenga codigo 200
    assert response.status_code == 200
    # Verificamos que el JSON devuelto sea el esperado
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
    assert response.json() == {"consumos": ["ID", "status", "uso", "periodo"]}


# Ver los limites de datos del tag
@patch("app.main.api.get_limit")
def test_get_limites(mock_tag):
    mock_tag.return_value = ["Usado", "Limite", "Estado"]

    response = client.get("/limites/pedroso")

    assert response.status_code == 200
    assert response.json() == {"limites": ["Usado", "Limite", "Estado"]}


@patch("app.main.api.get_tag_snapshot")
def test_get_tag_data_single(mock_snapshot):
    mock_snapshot.return_value = {"tag": "site-a", "rows": [], "errors": []}

    response = client.get("/tag_data/site-a")

    assert response.status_code == 200
    assert response.json() == {"tag": "site-a", "rows": [], "errors": []}
    mock_snapshot.assert_called_once_with("site-a")


@patch("app.main.api.get_all_tags_snapshot")
def test_get_tag_data_all_success(mock_all):
    mock_all.return_value = {"items": [{"tag": "site-a", "rows": []}], "errors": []}

    response = client.get("/tag_data/all")

    assert response.status_code == 200
    assert response.json() == {"items": [{"tag": "site-a", "rows": []}], "errors": []}
    mock_all.assert_called_once_with()
