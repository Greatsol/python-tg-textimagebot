from tortoise import Model, fields

from app import env


class Users(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField(unique=True)
    attempts = fields.SmallIntField(default=env.START_ATTEMPTS)
    category = fields.TextField(null=True)
    gender = fields.TextField(null=True)
    referals = fields.SmallIntField(default=0)
    step = fields.TextField(null=True)
    role = fields.TextField(default="user")
    pic_id = fields.SmallIntField(null=True)
    text = fields.TextField(null=True)
    message_id = fields.IntField(default=0)
    promocode_ids = fields.TextField(null=True)

    def __str__(self):
        return self.user_id
