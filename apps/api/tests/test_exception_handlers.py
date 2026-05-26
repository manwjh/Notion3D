"""Global exception handler tests."""


def test_design_turn_error_returns_400(client, project_id):
    res = client.post(
        f"/api/projects/{project_id}/design/plan",
        json={
            "task_class": "A",
            "summary": "test",
            "strategy": "from_scratch",
            "turn_id": "missing-turn",
        },
    )
    assert res.status_code == 400
    assert "detail" in res.json()


def test_cad_error_returns_400(client, project_id):
    res = client.post(
        f"/api/projects/{project_id}/render-forge",
        json={"forge_code": "   ", "label": "empty"},
    )
    assert res.status_code == 400
    assert res.json()["detail"]


def test_cad_not_found_returns_404(client, project_id):
    res = client.get(f"/api/projects/{project_id}/versions/99/forge-sources")
    assert res.status_code == 404
    assert res.json()["detail"]


def test_template_not_found_returns_404(client):
    res = client.get("/api/templates/does-not-exist-xyz")
    assert res.status_code == 404
    assert res.json()["detail"]


def test_template_error_returns_400(client):
    res = client.post(
        "/api/templates/hello-assembly/apply",
        json={"params": {"nonexistent_param": 1}},
    )
    assert res.status_code == 400
    assert res.json()["detail"]
