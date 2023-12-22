from flask_login import current_user, login_user
from flask import session
from datetime import datetime, timezone, timedelta
from app.api_v1.api_v1 import api_v1
from app.api_v1.app import socketio, app


app.register_blueprint(api_v1, url_prefix="/api/v1")


from app.api_v1.events.time_events import start_time_emitter


@app.route("/check")
def check():
    if current_user.is_authenticated:
        end_time: timedelta = session["end_time"] - datetime.now(timezone.utc)
        return f"User is authenticated. Remaining session time:  {end_time.total_seconds()}"
    else:
        return "User is not authenticated"


# @app.route("/login")
# def login():
#     user = User.get(id="admin")
#     login_user(user)
#     session["end_time"] = datetime.now(timezone.utc) + timedelta(minutes=5)
#     return "User logged in"



if __name__ == "__main__":
    start_time_emitter()
    socketio.run(app)
