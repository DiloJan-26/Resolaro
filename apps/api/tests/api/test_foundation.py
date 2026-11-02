from resolaro.main import app


def test_health_is_public(sample):
    client, *_ = sample
    assert client.get("/healthz").json() == {"status": "ok"}


def test_malformed_token_rejected(sample):
    client, *_ = sample
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_missing_membership_denies_other_org(signed_in):
    client, _, _, other_org = signed_in
    assert client.get(f"/api/v1/organizations/{other_org}/context").status_code == 404
    assert client.get("/api/v1/cases", params={"organization_id": str(other_org)}).status_code == 404


def test_case_list_is_scoped_to_verified_membership(signed_in):
    client, user_id, org_id, _ = signed_in
    me = client.get("/api/v1/me")
    assert me.status_code == 200
    assert me.json()["user_id"] == str(user_id)
    assert [entry["name"] for entry in me.json()["organizations"]] == ["Demo"]
    response = client.get("/api/v1/cases", params={"organization_id": str(org_id)})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert [item["title"] for item in response.json()["items"]] == ["Allowed case"]
    forged = client.get("/api/v1/me", params={"role": "ADMIN"})
    assert forged.json()["organizations"][0]["role"] == "OPERATOR"


def test_schema_validation(signed_in):
    client, _, org_id, _ = signed_in
    response = client.get("/api/v1/cases", params={"organization_id": str(org_id), "limit": 1000})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_no_org_state(sample):
    client, *_ = sample
    from uuid import uuid4
    from resolaro.auth import Identity, get_identity

    app.dependency_overrides[get_identity] = lambda: Identity(user_id=uuid4())
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["organizations"] == []
