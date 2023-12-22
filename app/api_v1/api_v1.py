from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_login import current_user
from werkzeug.security import check_password_hash
from pickle import loads, dumps
from secrets import token_hex
from app.api_v1.app import redis
import time
import datetime

api_v1 = Blueprint("api_v1", __name__)
api = Api(api_v1)


class Ping(Resource):
    """Ping resource"""

    def get(self):
        return {"status": "success", "message": "pong!"}


class ApıKey(Resource):
    def get(self):
        if current_user.is_authenticated:
            api_key = token_hex(16)
            author = current_user.id
            api_keys = redis.get_user_api_keys(user_id=author)
            api_keys.append(api_key)
            creation_date = datetime.datetime.now().strftime("%d.%m.%Y %H.%M")
            status = "Disabled"
            uses = 0
            mapping = {
                "author": author,
                "creation_date": creation_date,
                "status": status,
                "uses": uses,
            }
            redis.rd.hset(name=f"key:{api_key}", mapping=mapping)
            redis.rd.hset(
                name=f"account:{author}", key="api_keys", value=dumps(api_keys)
            )
            mapping["api_key"] = api_key
            return mapping

    def put(self):
        if current_user.is_authenticated:
            current_user_permission = redis.get_user_permission(user_id=current_user.id)
            if current_user_permission != "admin":
                return {
                    "status": "failed",
                    "message": "permission denied",
                    "data": {},
                }, 403

            api_key = request.json.get("api_key")
            api_keys = redis.get_api_keys(
                current_user=current_user, permission=current_user_permission
            )
            api_keys = [api_key[4:].decode("utf-8") for api_key in api_keys]
            if api_key in api_keys:
                status = "Enabled"
                redis.rd.hset(name=f"key:{api_key}", key="status", value=status)
                return {
                    "status": "success",
                    "message": "api key updated",
                    "data": {},
                }

    def delete(self):
        if current_user.is_authenticated:
            api_key = request.json.get("api_key")
            api_keys = redis.get_user_api_keys(user_id=current_user.id)
            if api_key in api_keys:
                api_keys.remove(api_key)
                redis.rd.hset(
                    name=f"account:{current_user.id}",
                    key="api_keys",
                    value=dumps(api_keys),
                )
                redis.rd.delete(f"key:{api_key}")
                return {
                    "status": "success",
                    "message": "api key deleted",
                    "data": {},
                }


class User(Resource):
    def get(self):
        if current_user.is_authenticated:
            temp_key = token_hex(16)
            redis.rd.setex(name=f"temp_key:{temp_key}", time=30, value=current_user.id)
            return (
                {
                    "status": "success",
                    "message": "user",
                    "data": {
                        "id": current_user.id,
                        "temp_key": temp_key,
                    },
                },
            )
        return {
            "status": "failed",
            "message": "permission denied",
            "data": {},
        }, 403


class Time(Resource):
    """Time resource"""

    def get(self):
        user_id = request.headers.get("X-USER-ID")
        api_key = request.headers.get("X-API-KEY")

        if not user_id or not api_key:
            return {
                "status": "failed",
                "message": "missing required headers",
                "data": {},
            }, 400

        if not redis.rd.exists(f"account:{user_id}"):
            return {
                "status": "failed",
                "message": "user not found",
                "data": {},
            }, 404

        if not redis.rd.hexists(f"account:{user_id}", "api_keys"):
            return {
                "status": "failed",
                "message": "api keys not found",
                "data": {},
            }, 404

        api_keys = redis.get_user_api_keys(user_id=user_id)

        if api_key not in api_keys:
            return {
                "status": "failed",
                "message": "invalid api key",
                "data": {},
            }, 401

        api_key_status = redis.rd.hget(f"key:{api_key}", "status").decode("utf-8")

        if api_key_status == "Disabled":
            return {
                "status": "failed",
                "message": "api key disabled, please contact with admin",
                "data": {},
            }, 401

        posix_time = time.time()
        readable_time = time.ctime(posix_time)
        iso_time = datetime.datetime.now().isoformat()
        raw_time = time.strftime("%H:%M:%S")

        return {
            "status": "success",
            "message": "time",
            "data": {
                "posix_time": posix_time,
                "readable_time": readable_time,
                "iso_time": iso_time,
                "raw_time": raw_time,
            },
        }


api.add_resource(Ping, "/ping")
api.add_resource(Time, "/time")
api.add_resource(User, "/user")
api.add_resource(ApıKey, "/api_key")
