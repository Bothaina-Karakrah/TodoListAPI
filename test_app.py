"""
Run it using "pytest -v"
"""
import pytest
from main import app, db, User, Task

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
    client = app.test_client()
    yield client
    with app.app_context():
        db.drop_all()

def test_register_and_login(client):
    # --- Register ---
    register = client.post("/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert register.status_code == 201
    data = register.get_json()
    assert "token" in data

    # --- Login ---
    login = client.post("/login", json={
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert login.status_code == 200
    token = login.get_json()["token"]
    assert token

def test_create_and_get_todo(client):
    # Register and get token
    register = client.post("/register", json={
        "name": "Bob",
        "email": "bob@example.com",
        "password": "1234"
    })
    token = register.get_json()["token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Create a todo
    create_task = client.post("/todos", json={
        "title": "Buy milk",
        "description": "2 liters"
    }, headers=headers)
    assert create_task.status_code == 201
    todo = create_task.get_json()
    assert todo["title"] == "Buy milk"

    # Get all todos
    todo_list = client.get("/todos", headers=headers)
    assert todo_list.status_code == 200
    todos = todo_list.get_json()["data"]
    assert len(todos) == 1
    assert todos[0]["title"] == "Buy milk"

    # Delete the task
    delete_task = client.delete(f"/todos/{todos[0]['id']}", headers=headers)
    assert delete_task.status_code == 204

    # Check all the to-do list again
    todo_list = client.get("/todos", headers=headers)
    assert todo_list.status_code == 200
    todos = todo_list.get_json()["data"]
    assert len(todos) == 0