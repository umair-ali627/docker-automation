# from fastapi import status
# from fastapi.testclient import TestClient
# from pytest_mock import MockerFixture
# from sqlalchemy.orm import Session

# from src.app.api.dependencies import get_current_user
# from src.app.api.v1.users import oauth2_scheme
# from tests.conftest import fake, override_dependency

# from .helpers import generators, mocks


# def test_post_user(client: TestClient) -> None:
#     response = client.post(
#         "/api/v1/user",
#         json={
#             "name": fake.name(),
#             "username": fake.user_name(),
#             "email": fake.email(),
#             "password": fake.password(),
#         },
#     )
#     assert response.status_code == status.HTTP_201_CREATED


# def test_get_user(db: Session, client: TestClient) -> None:
#     user = generators.create_user(db)

#     response = client.get(f"/api/v1/user/{user.username}")
#     assert response.status_code == status.HTTP_200_OK

#     response_data = response.json()

#     assert response_data["id"] == user.id
#     assert response_data["username"] == user.username


# def test_get_multiple_users(db: Session, client: TestClient) -> None:
#     for _ in range(5):
#         generators.create_user(db)

#     response = client.get("/api/v1/users")
#     assert response.status_code == status.HTTP_200_OK

#     response_data = response.json()["data"]
#     assert len(response_data) >= 5


# def test_update_user(db: Session, client: TestClient) -> None:
#     user = generators.create_user(db)
#     new_name = fake.name()

#     override_dependency(get_current_user, mocks.get_current_user(user))

#     response = client.patch(f"/api/v1/user/{user.username}", json={"name": new_name})
#     assert response.status_code == status.HTTP_200_OK


# def test_delete_user(db: Session, client: TestClient, mocker: MockerFixture) -> None:
#     user = generators.create_user(db)

#     override_dependency(get_current_user, mocks.get_current_user(user))
#     override_dependency(oauth2_scheme, mocks.oauth2_scheme())

#     mocker.patch("src.app.core.security.jwt.decode", return_value={"sub": user.username, "exp": 9999999999})

#     response = client.delete(f"/api/v1/user/{user.username}")
#     assert response.status_code == status.HTTP_200_OK


# def test_delete_db_user(db: Session, mocker: MockerFixture, client: TestClient) -> None:
#     user = generators.create_user(db)
#     super_user = generators.create_user(db, is_super_user=True)

#     override_dependency(get_current_user, mocks.get_current_user(super_user))
#     override_dependency(oauth2_scheme, mocks.oauth2_scheme())

#     mocker.patch("src.app.core.security.jwt.decode", return_value={"sub": user.username, "exp": 9999999999})

#     response = client.delete(f"/api/v1/db_user/{user.username}")
#     assert response.status_code == status.HTTP_200_OK


# tests/v1/test_users.py - UPDATED

from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.app.api.dependencies import get_current_user
# REMOVED: No longer importing oauth2_scheme here
from tests.conftest import fake, override_dependency

from .helpers import generators, mocks

# ... (test_post_user, test_get_user, test_get_multiple_users, test_update_user are fine) ...
def test_post_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/user",
        json={
            "name": fake.name(),
            "username": fake.user_name(),
            "email": fake.email(),
            "password": fake.password(),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_get_user(db: Session, client: TestClient) -> None:
    user = generators.create_user(db)

    response = client.get(f"/api/v1/user/{user.username}")
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()

    assert response_data["id"] == user.id
    assert response_data["username"] == user.username


def test_get_multiple_users(db: Session, client: TestClient) -> None:
    for _ in range(5):
        generators.create_user(db)

    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()["data"]
    assert len(response_data) >= 5


def test_update_user(db: Session, client: TestClient) -> None:
    user = generators.create_user(db)
    new_name = fake.name()

    override_dependency(get_current_user, mocks.get_current_user(user))

    response = client.patch(f"/api/v1/user/{user.username}", json={"name": new_name})
    assert response.status_code == status.HTTP_200_OK


def test_delete_user(db: Session, client: TestClient, mocker: MockerFixture) -> None:
    user = generators.create_user(db)
    override_dependency(get_current_user, mocks.get_current_user(user))
    # REMOVED: The override for oauth2_scheme is no longer needed
    # override_dependency(oauth2_scheme, mocks.oauth2_scheme())
    
    mocker.patch("src.app.core.security.jwt.decode", return_value={"sub": user.username, "exp": 9999999999})
    
    # ADDED: We need to pass a valid Authorization header for the test
    headers = {"Authorization": "Bearer testtoken"}
    response = client.delete(f"/api/v1/user/{user.username}", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_delete_db_user(db: Session, mocker: MockerFixture, client: TestClient) -> None:
    user = generators.create_user(db)
    super_user = generators.create_user(db, is_super_user=True)
    override_dependency(get_current_user, mocks.get_current_user(super_user))
    # REMOVED: The override for oauth2_scheme is no longer needed
    # override_dependency(oauth2_scheme, mocks.oauth2_scheme())

    mocker.patch("src.app.core.security.jwt.decode", return_value={"sub": user.username, "exp": 9999999999})
    
    # ADDED: We need to pass a valid Authorization header for the test
    headers = {"Authorization": "Bearer testtoken"}
    response = client.delete(f"/api/v1/db_user/{user.username}", headers=headers)
    assert response.status_code == status.HTTP_200_OK