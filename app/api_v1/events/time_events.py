from app.api_v1.app import socketio, redis
import time
import datetime
import threading
from flask import request
from flask_socketio import disconnect


def time_emitter():
    while True:
        posix_time = time.time()
        readable_time = time.ctime(posix_time)
        iso_time = datetime.datetime.now().isoformat()
        socketio.emit(
            "time_event",
            {
                "posix_time": posix_time,
                "readable_time": readable_time,
                "iso_time": iso_time,
            },
        )
        time.sleep(0.5)


def start_time_emitter():
    threading.Thread(target=time_emitter, daemon=True).start()


@socketio.on("connect")
def handle_connect():
    temp_key = request.args.get("temp_key")
    print(f"Temp key: {temp_key}")
    if redis.check_temp_key_exist(temp_key=temp_key):
        redis.rd.delete(f"temp_key:{temp_key}")
        return True
    else:
        disconnect()
