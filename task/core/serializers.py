from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Location, Review

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email' , 'password']
    
    def validate_email(self, value):
        if User.objects.filter(email = value).exists():
            raise ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password')
        )
        return user
    
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["name", "description" , "latitude" , "longitude" , "rating" , "category", "owner"]
        read_only_fields = ["rating" , "owner"]

    def validate_name(self, name):
        qs = Location.objects.filter(name=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Location already exists")
        return name

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise ValidationError("Wrong coordinates")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise ValidationError("Wrong coordinates")
        return value
    
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model=Review
        fields=["text", "value", "user", "location", "created_at"]
        read_only_fields = ["user", "location"]

    def validate_value(self, value):
        if not 1 <= value <=5:
            raise ValidationError("Wrong value")
        return value