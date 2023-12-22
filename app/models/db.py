import redis
from secrets import token_hex
from pickle import dumps, loads


class RedisDB:
    def __init__(self):
        self.rd = redis.Redis(host="localhost", port=6379, db=0)

        if not self.rd.exists("app:config"):
            print("Key app:config not found. Creating it...")
            self.rd.hset(name="app:config", key="secret_key", value=token_hex(16))
            print("Key app:config created successfully")

        self.secret_key = self.rd.hget("app:config", "secret_key")

    def get_user_api_keys(self, user_id):
        api_keys = self.rd.hget(name=f"account:{user_id}", key="api_keys")
        return loads(api_keys) if api_keys else []

    def get_user(self, user_id):
        return self.rd.hgetall(f"account:{user_id}")

    def get_user_permission(self, user_id):
        return self.rd.hget(name=f"account:{user_id}", key="permission").decode("utf-8")

    def get_api_key_info(self, api_key):
        return {
            attr: self.rd.hget(f"key:{api_key}", attr).decode("utf-8")
            for attr in ["creation_date", "status", "uses", "author"]
        }

    def get_api_keys(self, current_user, permission):
        return (
            self.rd.keys("key:*")
            if permission == "admin"
            else self.get_user_api_keys(user_id=current_user.id)
        )

    def check_temp_key_exist(self, temp_key):
        return self.rd.exists(f"temp_key:{temp_key}")
