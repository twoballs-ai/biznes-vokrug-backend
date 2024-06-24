import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from madsoft.main import app
from madsoft.database import Base, get_db
from madsoft import schemas, crud

# Создаем тестовую базу данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Используем тестовую базу данных для зависимостей
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)  # Создаем таблицы
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)  # Удаляем таблицы после тестов

@pytest.fixture(scope="module")
def db():
    db = TestingSessionLocal()
    yield db
    db.close()

@patch('madsoft.routers.upload_image')
def test_create_meme(mock_upload_image, client, db):
    # Мокаем функцию upload_image для предсказуемого поведения
    mock_upload_image.return_value = "http://mocked_url"

    # Подготавливаем тестовые данные
    meme_data = {
        "title": "Test Meme",
        "description": "A test meme",
    }

    # Отправляем POST запрос для создания мема
    response = client.post(
        "/memes/",
        data=meme_data,
        files={"file": ("test.jpg", b"file_content", "image/jpeg")},
    )

    # Проверяем, что запрос завершился успешно (статус код 200)
    assert response.status_code == 200

    # Проверяем данные в JSON-ответе
    data = response.json()
    assert data["title"] == "Test Meme"
    assert data["description"] == "A test meme"
    assert "image_url" in data

    # Проверяем вызов функции upload_image с ожидаемыми аргументами
    mock_upload_image.assert_called_once_with("test.jpg", b"file_content", "image/jpeg")

    # Проверяем, что возвращаемый URL изображения соответствует ожидаемому
    assert data["image_url"] == "http://mocked_url"

    # Дополнительно можно проверить другие ожидаемые атрибуты или значения, если такие есть

    # Дополнительные проверки могут включать проверку ID мема, если он возвращается в ответе
    assert "id" in data and isinstance(data["id"], int)

    # Дополнительно можно проверить, что поле "image_url" является строкой и не пустое
    assert isinstance(data["image_url"], str) and data["image_url"]

@patch('madsoft.routers.upload_image')
def test_update_meme(mock_upload_image, client, db):
    # Мокаем функцию upload_image для предсказуемого поведения
    mock_upload_image.return_value = "http://mocked_updated_url"

    # Создаем мем для обновления
    meme = schemas.MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = crud.create_meme(db, meme=meme)

    # Отправляем PUT запрос для обновления мема
    response = client.put(
        f"/memes/{db_meme.id}",
        data={"title": "Updated Meme", "description": "Updated description"},
        files={"file": ("updated.jpg", b"new_file_content", "image/jpeg")},
    )

    # Проверяем, что запрос завершился успешно (статус код 200)
    assert response.status_code == 200

    # Проверяем данные в JSON-ответе
    data = response.json()
    assert data["title"] == "Updated Meme"
    assert data["description"] == "Updated description"
    assert "image_url" in data

    # Проверяем вызов функции upload_image с ожидаемыми аргументами для нового файла
    mock_upload_image.assert_called_once_with("updated.jpg", b"new_file_content", "image/jpeg")

    # Проверяем, что возвращаемый URL изображения соответствует ожидаемому после обновления
    assert data["image_url"] == "http://mocked_updated_url"

    # Дополнительно можно проверить другие ожидаемые атрибуты или значения, если такие есть

    # Дополнительные проверки могут включать проверку ID мема, если он возвращается в ответе
    assert "id" in data and isinstance(data["id"], int)

    # Дополнительно можно проверить, что поле "image_url" является строкой и не пустое
    assert isinstance(data["image_url"], str) and data["image_url"]

def test_read_meme(client, db):
    meme = schemas.MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = crud.create_meme(db, meme=meme)

    response = client.get(f"/memes/{db_meme.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Meme"
    assert data["description"] == "A test meme"
    assert data["image_url"] == "http://test_url"

def test_delete_meme(client, db):
    meme = schemas.MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = crud.create_meme(db, meme=meme)

    response = client.delete(f"/memes/{db_meme.id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Мем с ID {db_meme.id} успешно удален"}

    response = client.get(f"/memes/{db_meme.id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Мем не найден"}
