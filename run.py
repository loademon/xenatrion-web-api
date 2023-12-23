from flask_login import current_user, login_user
from flask import session
from datetime import datetime, timezone, timedelta
from app.api_v1.api_v1 import api_v1
from app.api_v1.app import socketio, app


app.register_blueprint(api_v1, url_prefix="/api/v1")


from app.api_v1.events.time_events import start_time_emitter

if __name__ == "__main__":
    start_time_emitter()
    socketio.run(app)
