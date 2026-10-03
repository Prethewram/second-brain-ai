import pytest

from app.models.profile import Profile
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def profile_access(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users, [
        {"Authorization": f"Bearer {create_access_token(user.id)}"} for user in users
    ]


def test_create_get_and_duplicate_response(client, profile_access, db_session):
    users, headers = profile_access
    response = client.post(
        "/profile", headers=headers[0], json={"name": "Ada", "skills": "Python"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "id": data["id"],
        "user_id": users[0].id,
        "name": "Ada",
        "skills": "Python",
        "occupation": None,
        "company": None,
        "timezone": None,
        "language": None,
        "bio": None,
        "goals": None,
        "interests": None,
    }
    assert client.get("/profile", headers=headers[0]).json() == data
    response = client.post("/profile", headers=headers[0], json={"name": "Changed"})
    assert response.status_code == 409
    db_session.expire_all()
    assert db_session.query(Profile).one().name == "Ada"


def test_patch_upserts_then_preserves_omitted_fields_and_clears_null(
    client, profile_access, db_session
):
    _, headers = profile_access
    response = client.patch(
        "/profile", headers=headers[0], json={"company": "Example", "skills": "Python"}
    )
    assert response.status_code == 200
    profile_id = response.json()["id"]
    response = client.patch(
        "/profile", headers=headers[0], json={"name": "Ada", "company": None}
    )
    assert response.status_code == 200
    assert response.json()["id"] == profile_id
    assert (
        response.json()["name"],
        response.json()["company"],
        response.json()["skills"],
    ) == ("Ada", None, "Python")
    db_session.expire_all()
    assert db_session.query(Profile).count() == 1
    assert db_session.get(Profile, profile_id).company is None


def test_profiles_are_isolated_and_body_cannot_override_owner(
    client, profile_access, db_session
):
    users, headers = profile_access
    response = client.post(
        "/profile", headers=headers[0], json={"name": "Owner", "user_id": users[1].id}
    )
    assert response.status_code == 201
    assert response.json()["user_id"] == users[0].id
    assert client.get("/profile", headers=headers[1]).status_code == 404
    response = client.patch(
        "/profile", headers=headers[1], json={"name": "Other", "user_id": users[0].id}
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == users[1].id
    assert client.delete("/profile", headers=headers[1]).status_code == 204
    db_session.expire_all()
    assert db_session.query(Profile).one().name == "Owner"


def test_delete_persists_and_returns_empty_response(client, profile_access, db_session):
    _, headers = profile_access
    assert client.post("/profile", headers=headers[0], json={}).status_code == 201
    response = client.delete("/profile", headers=headers[0])
    assert response.status_code == 204
    assert response.content == b""
    assert db_session.query(Profile).count() == 0
    assert client.get("/profile", headers=headers[0]).status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_authentication_required(client, method):
    assert client.request(method, "/profile", json={}).status_code == 401


@pytest.mark.parametrize("method", ["get", "delete"])
def test_missing_profile_returns_404(client, profile_access, method):
    _, headers = profile_access
    response = client.request(method, "/profile", headers=headers[0])
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "method,body,status",
    [
        ("post", {"company": "x" * 256}, 400),
        ("patch", {"bio": "x" * 1001}, 400),
        ("post", {"name": 123}, 422),
    ],
)
def test_invalid_fields_do_not_create_profile(
    client, profile_access, db_session, method, body, status
):
    _, headers = profile_access
    response = client.request(method, "/profile", headers=headers[0], json=body)
    assert response.status_code == status
    assert db_session.query(Profile).count() == 0


def test_invalid_patch_preserves_existing_fields(client, profile_access, db_session):
    _, headers = profile_access
    client.post("/profile", headers=headers[0], json={"name": "Original", "bio": "Bio"})
    response = client.patch(
        "/profile", headers=headers[0], json={"name": "Changed", "bio": "x" * 1001}
    )
    assert response.status_code == 400
    db_session.expire_all()
    profile = db_session.query(Profile).one()
    assert (profile.name, profile.bio) == ("Original", "Bio")
