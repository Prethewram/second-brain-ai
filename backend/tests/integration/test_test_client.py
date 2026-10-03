from app.models.user import User


def test_client_registration_persists_in_fixture_database(client, db_session):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "test-password-123",
        },
    )
    assert response.status_code in (200, 201)
    user = db_session.query(User).filter_by(email="test@example.com").one()
    assert response.json()["id"] == user.id
    assert user.password_hash != "test-password-123"
