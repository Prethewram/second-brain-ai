from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.models.user import User
from app.modules.auth.security import create_access_token, verify_password


@pytest.fixture
def registered_user(client):
    body = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "correct-password",
    }
    response = client.post("/auth/register", json=body)
    assert response.status_code == 200
    return body, response.json()


def test_registration_hashes_password_and_does_not_expose_it(
    client, registered_user, db_session
):
    body, data = registered_user
    assert set(data) == {"id", "name", "email"}
    user = db_session.get(User, data["id"])
    assert user.password_hash != body["password"]
    assert verify_password(body["password"], user.password_hash)


def test_login_token_authenticates_current_user(client, registered_user):
    body, data = registered_user
    response = client.post(
        "/auth/login", json={"email": body["email"], "password": body["password"]}
    )
    assert response.status_code == 200
    token = response.json()
    assert set(token) == {"access_token", "token_type"}
    assert token["token_type"] == "bearer"
    claims = jwt.decode(
        token["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert claims["sub"] == str(data["id"])
    assert claims["exp"] > datetime.now(UTC).timestamp()
    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json() == data


def test_duplicate_registration_preserves_original_user(
    client, registered_user, db_session
):
    body, data = registered_user
    response = client.post(
        "/auth/register",
        json={**body, "name": "Changed", "password": "changed-password"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
    assert db_session.query(User).count() == 1
    assert db_session.get(User, data["id"]).name == body["name"]
    assert verify_password(
        body["password"], db_session.get(User, data["id"]).password_hash
    )


@pytest.mark.parametrize(
    "email,password",
    [("test@example.com", "wrong"), ("missing@example.com", "correct-password")],
)
def test_bad_login_credentials_have_same_response(
    client, registered_user, email, password
):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.parametrize(
    "changes",
    [
        {"email": "invalid"},
        {"name": " "},
        {"name": "x" * 101},
        {"password": ""},
        {"password": "x" * 73},
        {"password": "é" * 37},
    ],
)
def test_invalid_registration_is_rejected_without_persistence(
    client, db_session, changes
):
    body = {"name": "Test", "email": "test@example.com", "password": "password"}
    body.update(changes)
    response = client.post("/auth/register", json=body)
    assert response.status_code in (400, 422)
    assert db_session.query(User).count() == 0


@pytest.mark.parametrize(
    "subject",
    [None, "", "abc", "1.5", "-1", "0", "99999999999999999999999999999999999"],
)
def test_invalid_subject_is_401_not_server_error(client, subject):
    claims = {"exp": datetime.now(UTC) + timedelta(minutes=5)}
    if subject is not None:
        claims["sub"] = subject
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "kind", ["expired", "wrong-signature", "missing-expiration", "malformed"]
)
def test_invalid_token_is_rejected(client, registered_user, kind):
    _, user = registered_user
    claims = {"sub": str(user["id"]), "exp": datetime.now(UTC) + timedelta(minutes=5)}
    key = settings.SECRET_KEY
    if kind == "expired":
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
    elif kind == "wrong-signature":
        key = "different-secret"
    elif kind == "missing-expiration":
        del claims["exp"]
    token = (
        "not-a-jwt"
        if kind == "malformed"
        else jwt.encode(claims, key, algorithm=settings.ALGORITHM)
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_deleted_user_token_is_rejected(client, registered_user, db_session):
    _, data = registered_user
    token = create_access_token(data["id"])
    db_session.delete(db_session.get(User, data["id"]))
    db_session.commit()
    assert (
        client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_missing_token_is_rejected(client):
    assert client.get("/users/me").status_code == 401


def test_login_does_not_accept_passwords_that_only_match_bcrypt_prefix(client):
    # bcrypt only processes 72 UTF-8 bytes. Long login input must not be truncated.
    body = {"name": "Test", "email": "test@example.com", "password": "x" * 72}
    assert client.post("/auth/register", json=body).status_code == 200
    response = client.post(
        "/auth/login", json={"email": body["email"], "password": "x" * 73}
    )
    assert response.status_code == 401
