import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from madsoft.database import Base
from madsoft.models import Meme
from madsoft.crud import get_memes, create_meme, get_meme, update_meme, delete_meme
from madsoft.schemas import MemeCreate, MemeUpdate

# Создаем тестовую базу данных SQLite в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_meme(db):
    meme_data = MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = create_meme(db, meme=meme_data)
    assert db_meme.title == meme_data.title
    assert db_meme.description == meme_data.description
    assert db_meme.image_url == meme_data.image_url

def test_get_memes(db):
    meme_data1 = MemeCreate(title="Test Meme 1", description="First test meme", image_url="http://test_url1")
    meme_data2 = MemeCreate(title="Test Meme 2", description="Second test meme", image_url="http://test_url2")
    create_meme(db, meme=meme_data1)
    create_meme(db, meme=meme_data2)

    memes = get_memes(db, skip=0, limit=10)
    assert len(memes) == 2
    assert memes[0].title == meme_data1.title
    assert memes[1].title == meme_data2.title

def test_get_meme(db):
    meme_data = MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = create_meme(db, meme=meme_data)

    fetched_meme = get_meme(db, meme_id=db_meme.id)
    assert fetched_meme is not None
    assert fetched_meme.title == meme_data.title
    assert fetched_meme.description == meme_data.description
    assert fetched_meme.image_url == meme_data.image_url

def test_update_meme(db):
    meme_data = MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = create_meme(db, meme=meme_data)

    update_data = MemeUpdate(title="Updated Meme", description="Updated description")
    updated_meme = update_meme(db, meme_id=db_meme.id, meme=update_data)
    assert updated_meme.title == update_data.title
    assert updated_meme.description == update_data.description

def test_delete_meme(db):
    meme_data = MemeCreate(title="Test Meme", description="A test meme", image_url="http://test_url")
    db_meme = create_meme(db, meme=meme_data)

    delete_meme(db, meme_id=db_meme.id)
    fetched_meme = get_meme(db, meme_id=db_meme.id)
    assert fetched_meme is None
