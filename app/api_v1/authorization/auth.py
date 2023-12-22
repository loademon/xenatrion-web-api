from app.models.db import RedisDB
from flask_login import UserMixin

redis = RedisDB()

class User(UserMixin):
    def __init__(self, id, password):
        self.id = id
        self.password = password

    @staticmethod
    def get(id):
        passw = redis.rd.hget(f"account:{id}", "password")
        if passw:
            return User(id, passw)
        return None

