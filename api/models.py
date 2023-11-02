from django.db import models

# Create your models here.

class Bot(models.Model):
    ask = models.TextField()
    session_id = models.TextField()
    
