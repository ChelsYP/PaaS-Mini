def test_healthz_endpoint(client):
    """Pengujian FR/NFR: Endpoint /healthz dapat diakses tanpa autentikasi."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "paas-dashboard"

