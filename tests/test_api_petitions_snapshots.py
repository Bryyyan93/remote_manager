from unittest.mock import patch

from ssh import api_petitions


def _sim_info(sim_id, online=True):
    base = int(sim_id)
    return {
        "ipv4": f"10.0.0.{base}",
        "online": online,
        "data_limit": {"used": 5_000_000, "total": 50_000_000, "type": "monthly"},
    }


@patch("ssh.api_petitions.utils.api_headers")
@patch("ssh.api_petitions.onomondo.get_sim_info")
@patch("ssh.api_petitions.onomondo.get_ids_by_tag")
def test_get_tag_snapshot_returns_rows_and_errors(mock_ids_by_tag, mock_get_sim_info, mock_headers):
    mock_headers.return_value = {"authorization": "Bearer fake"}
    mock_ids_by_tag.return_value = ["2", "1", "3"]

    def side_effect(_headers, sim_id):
        if sim_id == "2":
            return None
        return _sim_info(sim_id, online=(sim_id != "3"))

    mock_get_sim_info.side_effect = side_effect

    snapshot = api_petitions.get_tag_snapshot("site-a")

    assert snapshot["tag"] == "site-a"
    assert [row["id"] for row in snapshot["rows"]] == ["1", "3"]
    assert snapshot["errors"] == [
        {"tag": "site-a", "sim_id": "2", "error": "No se pudo obtener información de la SIM"}
    ]


@patch("ssh.api_petitions.BATCH_PAUSE_SECONDS", 0)
@patch("ssh.api_petitions.utils.api_headers")
@patch("ssh.api_petitions.onomondo.get_sim_info")
@patch("ssh.api_petitions.onomondo.get_ids_by_tag")
def test_get_tag_snapshot_retries_failed_sims(mock_ids_by_tag, mock_get_sim_info, mock_headers):
    mock_headers.return_value = {"authorization": "Bearer fake"}
    mock_ids_by_tag.return_value = ["1", "2"]
    calls_by_id = {"1": 0, "2": 0}

    def side_effect(_headers, sim_id):
        calls_by_id[sim_id] += 1
        if sim_id == "2" and calls_by_id[sim_id] == 1:
            return None
        return _sim_info(sim_id)

    mock_get_sim_info.side_effect = side_effect

    snapshot = api_petitions.get_tag_snapshot("site-a")

    assert [row["id"] for row in snapshot["rows"]] == ["1", "2"]
    assert snapshot["errors"] == []
    assert calls_by_id["2"] == 2


@patch("ssh.api_petitions.utils.api_headers")
@patch("ssh.api_petitions.onomondo.get_sim_info")
@patch("ssh.api_petitions.onomondo.get_all_sims")
@patch("ssh.api_petitions.onomondo.get_tags")
def test_get_all_tags_snapshot_keeps_shared_sims_and_reports_missing(
    mock_get_tags,
    mock_get_all_sims,
    mock_get_sim_info,
    mock_headers,
):
    mock_headers.return_value = {"authorization": "Bearer fake"}
    mock_get_tags.return_value = ["site-a", "site-b"]
    mock_get_all_sims.return_value = {
        "sims": [
            {"id": "1", "tags": [{"name": "site-a"}]},
            {"id": "2", "tags": [{"name": "site-a"}, {"name": "site-b"}]},
            {"id": "3", "tags": [{"name": "site-b"}]},
        ],
        "next_page": None,
    }

    def side_effect(_headers, sim_id):
        if sim_id == "3":
            return None
        return _sim_info(sim_id)

    mock_get_sim_info.side_effect = side_effect

    snapshot = api_petitions.get_all_tags_snapshot()

    assert snapshot["items"] == [
        {
            "tag": "site-a",
            "rows": [
                api_petitions._build_row("1", _sim_info("1")),
                api_petitions._build_row("2", _sim_info("2")),
            ],
        },
        {
            "tag": "site-b",
            "rows": [api_petitions._build_row("2", _sim_info("2"))],
        },
    ]
    assert {"sim_id": "3", "error": "No se pudo obtener información de la SIM"} in snapshot["errors"]
    assert {"tag": "site-b", "sim_id": "3", "error": "La SIM no pudo incluirse en el snapshot"} not in snapshot["errors"]
