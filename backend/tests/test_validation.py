async def test_empty_message_returns_422_not_500(client):
    response = await client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422
    assert "detail" in response.json()


async def test_whitespace_only_message_returns_422(client):
    response = await client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 422


async def test_overly_long_message_returns_422(client):
    response = await client.post("/api/chat", json={"message": "a" * 2001})

    assert response.status_code == 422


async def test_missing_message_field_returns_422(client):
    response = await client.post("/api/chat", json={})

    assert response.status_code == 422


async def test_null_byte_only_message_returns_422_not_500(client):
    response = await client.post("/api/chat", json={"message": "\x00\x00"})

    assert response.status_code == 422


async def test_malformed_json_body_returns_422_not_500(client):
    response = await client.post(
        "/api/chat",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


async def test_non_string_message_returns_422(client):
    response = await client.post("/api/chat", json={"message": 12345})

    assert response.status_code == 422


async def test_health_check(client):
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
