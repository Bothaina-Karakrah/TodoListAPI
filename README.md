# To-Do List API

This project is part of the [Backend roadmap](https://roadmap.sh/backend)
- https://roadmap.sh/projects/todo-list-api
<br>
A simple To-do List API implemented using Flask, SQLite, and JWT-based authentication.

---

## Getting Started

### Installation

1. Clone the repository:

```bash
git clone <repo_url>
cd <repo_folder>
```

2. Install dependencies:

```bash
pip install Flask flask_sqlalchemy flask_jwt_extended werkzeug
```

3. Run the server:

```bash
flask --app main run --debug
```

By default, the API runs at `http://127.0.0.1:5000/`.

---

## API Endpoints

### 1. Register a New User

**Endpoint:** `POST /register`
**Description:** Register a new user in the system.

**Request JSON:**

```json
{
  "name": "John Doe",
  "email": "john@doe.com",
  "password": "password"
}
```

**Response (201 Created):**

```json
{
  "token": "<jwt_token>",
  "user": {
    "id": 1,
    "email": "john@doe.com",
    "name": "John Doe"
  }
}
```

---

### 2. Login

**Endpoint:** `POST /login`
**Description:** Authenticate a user and receive a JWT token.

**Request JSON:**

```json
{
  "email": "john@doe.com",
  "password": "password"
}
```

**Response (200 OK):**

```json
{
  "token": "<jwt_token>",
  "user": {
    "id": 1,
    "email": "john@doe.com",
    "name": "John Doe"
  }
}
```

---

### 3. Add a New Task

**Endpoint:** `POST /todos`
**Description:** Create a new task.
**Authentication:** Required (Bearer token in `Authorization` header)

**Request JSON:**

```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "owner_id": 1,
  "created_at": "2025-10-30T12:34:56.789Z",
  "updated_at": "2025-10-30T12:34:56.789Z"
}
```

---

### 4. Update a Task

**Endpoint:** `PUT /todos/<task_id>`
**Description:** Update a task's title, description, or completion status.
**Authentication:** Required

**Request JSON:**

```json
{
  "title": "Buy groceries and fruits",
  "completed": true
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "title": "Buy groceries and fruits",
  "description": "Milk, eggs, bread",
  "completed": true,
  "owner_id": 1,
  "created_at": "2025-10-30T12:34:56.789Z",
  "updated_at": "2025-10-30T12:50:00.123Z"
}
```

---

### 5. Delete a Task

**Endpoint:** `DELETE /todos/<task_id>`
**Description:** Delete a task.
**Authentication:** Required

**Response (204 No Content):**
No body returned.

---

### 6. Get Tasks (with Pagination, Filtering, Sorting, Search)

**Endpoint:** `GET /todos`
**Description:** Retrieve tasks for the logged-in user.
**Authentication:** Required

**Query Parameters:**

* `page` (default: 1)
* `limit` (default: 10, max: 100)
* `completed` (`true` or `false`)
* `sort` (`created_at`, `updated_at`, `title`)
* `order` (`asc` or `desc`)
* `search` (string to search in title or description)

**Example Request:**

```
GET /todos?page=1&limit=5&completed=false&sort=created_at&order=desc&search=groceries
```

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": 1,
      "title": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "owner_id": 1,
      "created_at": "2025-10-30T12:34:56.789Z",
      "updated_at": "2025-10-30T12:34:56.789Z"
    }
  ],
  "page": 1,
  "limit": 5,
  "total": 1
}
```

---

## Error Responses

| Status Code | Description                                      |
| ----------- | ------------------------------------------------ |
| 400         | Bad request (missing or invalid parameters)      |
| 401         | Unauthorized (missing or invalid token)          |
| 403         | Forbidden (trying to access another user's task) |
| 404         | Not found (task or endpoint does not exist)      |
| 500         | Server error                                     |

