from tortoise import Model, fields


class Promo(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    attempts = fields.SmallIntField()
    activate = fields.IntField(default=0)

    def __str__(self):
        return f"{self.name} - {self.attempts}"
