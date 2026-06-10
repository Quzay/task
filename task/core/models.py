from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    rating = models.FloatField(default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Review(models.Model):
    text = models.TextField(blank=False)
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user' , 'location'], name='uq_user_location_review')
        ]

    def __str__(self):
        return f'Review form {self.user.username} to {self.location}'

class Like(models.Model):
    is_like = models.BooleanField(default=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE) #unique

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'review'], name='uq_user_review_like')
        ]

    def __str__(self):
        status = 'Like' if self.is_like else 'Dislike'
        return f'{status} from {self.user.username} to review №{self.review.id}'

class Subscription(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'location'], name='uq_user_location_sub')
        ]
    def __str__(self):
        return f'Sub {self.user.username} to {self.location}'