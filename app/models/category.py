from tortoise import Model, fields


class Category(Model):
    id = fields.IntField(pk=True)
    category = fields.TextField()

    def __str__(self):
        return self.category
