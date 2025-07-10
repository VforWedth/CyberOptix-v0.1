# from django.db import models
# from django.contrib.auth.models import AbstractUser
# # Create your models here.

# class User(AbstractUser):
#     email = models.EmailField(unique=True, null=False)
#     username = models.CharField(max_length=100)
#     bio = models.CharField(max_length=100)
#     # title = models.CharField()
#     # decs = models.TextField()
    
#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ['username']
    
#     def __str__(self):
#         return self.username

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False)
    username = models.CharField(max_length=100, unique=True)  # Ensure username is unique
    bio = models.CharField(max_length=100, blank=True)  # Optional field
    
    is_shop_admin = models.BooleanField(default=False)
    
    USERNAME_FIELD = "username"  # Use username for authentication
    REQUIRED_FIELDS = ['email']  # Email is required for user creation

    def __str__(self):
        return self.username
