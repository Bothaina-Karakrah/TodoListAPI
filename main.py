"""
Run: flask --app main run --debug
Dependencies:
    pip install Flask flask_sqlalchemy flask_jwt_extended werkzeug
"""
import secrets
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------- APP SETUP -------------------------
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Refresh token mechanism for the authentication
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

@jwt.unauthorized_loader
def custom_unauthorized_response(err_str):
    return jsonify({"error": "Missing or invalid token"}), 401

# ------------------------- DATABASE MODELS -------------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship("Task", back_populates="author", cascade="all, delete-orphan")

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    author = db.relationship("User", back_populates="tasks")

with app.app_context():
    db.create_all()

# ------------------------- HELPERS -------------------------
def task_to_dict(task: Task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": bool(task.completed),
        "owner_id": task.owner_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }

def user_to_dict(user: User):
    return {"id": user.id, "email": user.email, "name": user.name}

def paginate_query(query, page: int, limit: int):
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total

# ------------------------- ROUTES -------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing required fields: name, email, password"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
    new_user = User(email=email, name=name, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id))
    return jsonify({"token": access_token, "user": user_to_dict(new_user)}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing required fields: email, password"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": user_to_dict(user)}), 200


@app.route("/todos", methods=["POST"])
@jwt_required()
def add_new_task():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description", "")

    if not title:
        return jsonify({"error": "Missing required field: title"}), 400

    task = Task(title=title, description=description, owner_id=current_user_id)
    db.session.add(task)
    db.session.commit()
    return jsonify(task_to_dict(task)), 201


@app.route("/todos/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    if task.owner_id != current_user_id:
        return jsonify({"message": "Forbidden"}), 403

    title = data.get("title")
    description = data.get("description")
    completed = data.get("completed")

    if title is not None:
        if not isinstance(title, str) or title.strip() == "":
            return jsonify({"error": "Invalid title"}), 400
        task.title = title.strip()

    if description is not None:
        task.description = description

    if completed is not None:
        if not isinstance(completed, bool):
            return jsonify({"error": "completed must be boolean"}), 400
        task.completed = completed

    db.session.commit()
    return jsonify(task_to_dict(task)), 200


@app.route("/todos/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    current_user_id = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    if task.owner_id != current_user_id:
        return jsonify({"message": "Forbidden"}), 403

    db.session.delete(task)
    db.session.commit()
    return "", 204


@app.route("/todos", methods=["GET"])
@jwt_required()
def get_tasks():
    """
    GET /todos?page=1&limit=10&completed=true&sort=created_at&order=desc&search=groceries
    """
    # Implement rate limiting and throttling for the API
    current_user_id = int(get_jwt_identity())
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=10, type=int)
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    # filters
    q = Task.query.filter_by(owner_id=current_user_id)

    completed_param = request.args.get("completed")
    if completed_param is not None:
        if completed_param.lower() in ("true", "1"):
            q = q.filter_by(completed=True)
        elif completed_param.lower() in ("false", "0"):
            q = q.filter_by(completed=False)
        else:
            return jsonify({"error": "Invalid 'completed' query parameter, use true/false"}), 400

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Task.title.ilike(like), Task.description.ilike(like)))

    # sorting
    sort = request.args.get("sort", "created_at") # Sort by created_at by default
    order = request.args.get("order", "desc").lower()
    if sort not in ("created_at", "title", "updated_at"):
        sort = "created_at"

    sort_col = getattr(Task, sort)
    if order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    items, total = paginate_query(q, page, limit)
    return jsonify(
        {
            "data": [task_to_dict(t) for t in items],
            "page": page,
            "limit": limit,
            "total": total,
        }
    ), 200


# ------------------------- ERROR HANDLERS -------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)