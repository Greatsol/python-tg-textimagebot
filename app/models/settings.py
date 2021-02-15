from tortoise import Model, fields

class Settings(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)
    value = fields.TextField(null=True)
    type = fields.TextField(null=True)
    description = fields.TextField(null=True)

    def __str__(self):
        return self.user_id
