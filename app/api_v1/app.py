from flask import Flask, render_template, request, session, redirect, url_for
from flask_login import current_user, login_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
from datetime import timedelta

from flask_login import LoginManager
from flask_socketio import SocketIO
from app.models.db import RedisDB
from app.api_v1.authorization.auth import User


redis = RedisDB()

app = Flask(__name__)
app.secret_key = redis.secret_key
app.permanent_session_lifetime = timedelta(minutes=5)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(id):
    return User.get(id=id)


socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)
print("Login manager initialized successfully")


@app.route("/")
def index():
    return redirect(url_for("user" if current_user.is_authenticated else "login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    id, password = request.form.get("id"), request.form.get("password")
    user, user_db = User.get(id=id), redis.get_user(user_id=id)
    db_password = user_db[b"password"].decode("utf-8") if user_db else None

    if user and check_password_hash(db_password, password):
        login_user(user=user)
        session["end_time"] = (
            datetime.now(timezone.utc) + app.permanent_session_lifetime
        )
        return redirect(url_for("user"))

    return redirect(url_for("login"))


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    id, password = request.form.get("id"), request.form.get("password")
    user = User.get(id=id)
    if user:
        return redirect(url_for("register"))
    else:
        redis.rd.hset(
            name=f"account:{id}", key="password", value=generate_password_hash(password)
        )
        redis.rd.hset(name=f"account:{id}", key="permission", value="user")
        return redirect(url_for("login"))


@app.route("/user")
def user():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    end_time: timedelta = session["end_time"] - datetime.now(timezone.utc)
    user_permission = redis.get_user_permission(user_id=current_user.id)
    api_keys = redis.get_api_keys(permission=user_permission, current_user=current_user)
    page, uses = generate_api_key_page(api_keys)

    return render_template(
        "user.html",
        api_list=page,
        initial_seconds=end_time.total_seconds(),
        user_id=current_user.id,
        api_count=len(api_keys),
        request_count=uses,
    )


def generate_api_key_page(api_keys):
    page, uses = "", 0
    for key in api_keys:
        api_key = key.decode("utf-8").split(":")[1] if isinstance(key, bytes) else key
        key_info = redis.get_api_key_info(api_key)
        uses += int(key_info["uses"])
        page += render_api_key_html(api_key, key_info)
    return page, uses


def render_api_key_html(api_key, key_info):
    return (
        f'<li class="list-group-item">'
        f'<div class="row align-items-center no-gutters">'
        f'<div class="col me-2">'
        f'<h6 class="mb-0"><strong>{api_key}</strong></h6>'
        f'<span id="creation-date" class="text-xs">Creation Date: {key_info["creation_date"]}</span>'
        f'<span id="key-status" class="text-xs" style="padding-left: 31px;">Key status: {key_info["status"]}</span>'
        f'<span id="key-uses" class="text-xs" style="padding-left: 31px;">Key uses: {key_info["uses"]}</span>'
        f'<span id="key-author" class="text-xs" style="padding-left: 31px;">Key author: {key_info["author"]}</span>'
        f"</div>"
        f'<div class="col-auto"><button class="btn btn-danger" type="button"><i class="fas fa-trash"></i></button></div>'
        f'<div class="col-auto"><button class="btn btn-primary" type="button"><i class="fas fa-check"></i></button></div>'
        f"</div>"
        f"</li>"
    )
