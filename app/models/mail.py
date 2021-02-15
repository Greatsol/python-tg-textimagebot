from tortoise import Model, fields


class Mail(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField(unique=True)
    text = fields.TextField()
    url = fields.TextField(null=True)
    btn_name = fields.TextField(null=True)

    def __str__(self):
        return self.text
