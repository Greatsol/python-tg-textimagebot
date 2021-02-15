from tortoise import Model, fields


class Pics(Model):
    id = fields.IntField(pk=True)
    category = fields.TextField()
    gender = fields.TextField(null=True)
    pic_path = fields.TextField(null=True)
    font_path = fields.TextField(null=True)
    font_color = fields.TextField(null=True)
    file_id = fields.TextField(null=True)

    def __str__(self):
        return self.pic_path
