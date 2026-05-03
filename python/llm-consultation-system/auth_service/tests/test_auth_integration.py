import pytest


@pytest.mark.asyncio
async def test_register_and_login_and_me(client):
    # Register
    register_resp = await client.post(
        "/auth/register",
        json={"email": "student@email.com", "password": "testpass123"},
    )
    assert register_resp.status_code == 201
    user_data = register_resp.json()
    assert user_data["email"] == "student@email.com"
    assert user_data["role"] == "user"
    assert "id" in user_data

    # Login
    login_resp = await client.post(
        "/auth/login",
        data={"username": "student@email.com", "password": "testpass123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # Me
    me_resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "student@email.com"
    assert me_data["id"] == user_data["id"]


@pytest.mark.asyncio
async def test_duplicate_registration(client):
    await client.post(
        "/auth/register",
        json={"email": "duplicate@email.com", "password": "testpass123"},
    )
    resp = await client.post(
        "/auth/register",
        json={"email": "duplicate@email.com", "password": "testpass123"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "correctpass"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "test@email.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client):
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
