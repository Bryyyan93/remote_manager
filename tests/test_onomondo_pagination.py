from unittest.mock import Mock, patch

import pytest

from api_onomondo import onomondo


def _response(status_code=200, payload=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = payload
    return response


@patch("api_onomondo.onomondo._get")
def test_get_all_sims_single_page(mock_get):
    mock_get.return_value = _response(payload={"sims": [{"id": "1"}], "next_page": None})

    data = onomondo.get_all_sims({"authorization": "Bearer fake"})

    assert data == {"sims": [{"id": "1"}], "next_page": None}
    mock_get.assert_called_once()
    assert "limit=5000" in mock_get.call_args.args[0]


@patch("api_onomondo.onomondo._get")
def test_get_all_sims_multiple_pages(mock_get):
    mock_get.side_effect = [
        _response(payload={"sims": [{"id": "1"}], "next_page": "cursor-1"}),
        _response(payload={"sims": [{"id": "2"}], "next_page": None}),
    ]

    data = onomondo.get_all_sims({"authorization": "Bearer fake"})

    assert data == {"sims": [{"id": "1"}, {"id": "2"}], "next_page": None}
    assert mock_get.call_count == 2
    first_url = mock_get.call_args_list[0].args[0]
    second_url = mock_get.call_args_list[1].args[0]
    assert "limit=5000" in first_url
    assert "next_page=cursor-1" in second_url


@patch("api_onomondo.onomondo._get")
def test_get_all_sims_invalid_payload_raises(mock_get):
    mock_get.return_value = _response(payload={"next_page": None})

    with pytest.raises(ValueError, match="lista válida de SIMs"):
        onomondo.get_all_sims({"authorization": "Bearer fake"})


@patch("api_onomondo.onomondo.get_all_sims")
def test_get_ids_by_tag_uses_full_inventory(mock_all_sims):
    mock_all_sims.return_value = {
        "sims": [
            {"id": "1", "tags": [{"name": "site-a"}]},
            {"id": "2", "tags": [{"name": "site-b"}]},
            {"id": "3", "tags": [{"name": "site-a"}]},
        ],
        "next_page": None,
    }

    ids = onomondo.get_ids_by_tag({"authorization": "Bearer fake"}, "site-a")

    assert ids == ["1", "3"]
