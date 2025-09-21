from django.db import models

class Client (models.Model):
    id = models.AutoField(primary_key = True)
    name = models.CharField(max_length = 64)
    employees = models.IntegerField(default = 0)
