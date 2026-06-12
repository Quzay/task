import pandas as pd
import json
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate , login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter , OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import RegisterSerializer, LocationSerializer, ReviewSerializer
from .models import Location, Review, Subscription, Like
from .permissions import IsOwnerOrReadOnly, IsReviewOwnerOrReadOnly

# Create your views here.

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":'User successful created'}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes =[]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({'message':"Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"Wrong username or password"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message":"Logout successful"}, status=status.HTTP_200_OK)
    
class LocationViewSet(ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category" , "rating"]
    search_fields = ["name" , "description"]
    ordering_fields = ["rating" , "name"]
    ordering = ["id"]
    
    CACHE_KEY_LIST='locations_list'

    def get_cache_key_detail(self, pk):
        return f'locations_detail_{pk}'

    def clear_locations_cache(self, pk=None):
        cache.delete(self.CACHE_KEY_LIST)
        if pk:
            cache.delete(self.get_cache_key_detail(pk))

    def list(self, request, *args, **kwargs):
        cached_data = cache.get(self.CACHE_KEY_LIST)
        if cached_data is not None:
            return Response(cached_data)
        response = super().list(request, *args, **kwargs)
        cache.set(self.CACHE_KEY_LIST, response.data, timeout=900)
        return response
    
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        cache_key = self.get_cache_key_detail(pk)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=900)
        return response

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        self.clear_locations_cache()

    def perform_update(self, serializer):
        instance = serializer.save()
        self.clear_locations_cache(pk=instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        super().perform_destroy(instance)
        self.clear_locations_cache(pk=pk)

class ReviewViewSet(ModelViewSet):
    queryset=Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]

    def perform_create(self, serializer):
        location_id = self.kwargs.get("locations_pk")
        serializer.save(user=self.request.user, location_id=location_id)
    
    def get_queryset(self):
        location_id = self.kwargs.get("locations_pk")
        if location_id:
            return Review.objects.filter(location_id=location_id)
        return Review.objects.all()

class ExportLocationView(APIView):
    format_kwarg = None
    def get(self, request):
        export_format = request.query_params.get('export_format', 'json').lower()
        locations_queryset = Location.objects.values("id", "name", "description", "latitude", "longitude", "rating", "category__name" , "owner__username")

        if not locations_queryset:
            return JsonResponse({"detail" : "No data to export"}, status=400)
        
        df = pd.DataFrame(list(locations_queryset))

        df.rename(columns={
            "category__name" : "category",
            "owner__username" : "owner"
        }, inplace=True)

        if export_format == 'csv' :
            response = HttpResponse(content_type = "text/csv")
            response["Content-Disposition"] = 'attachment; filename="locations.csv"'
            df.to_csv(path_or_buf=response, index=False, encoding="utf-8")
            return response
        else:
            df[["latitude", "longitude"]] = df[["latitude", "longitude"]].astype(float) 
            data = df.to_dict(orient="records")
            response = HttpResponse(content_type = "application/json")
            response["Content-Disposition"] = 'attachment; filename="locations.json"'
            response.write(json.dumps(data, ensure_ascii=False, indent=4))
            return response
        
class SubscribeLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, location_id):
        location = get_object_or_404(Location, id=location_id)
        user = request.user
        subscription, created = Subscription.objects.get_or_create(user = user , location = location)
        if not created:
            subscription.delete()
            return Response({"detail" : "Successful unsubscribed"}, status=status.HTTP_200_OK)
        return Response({"detail" : f"Successful subscribed to '{location.name}'."}, status=status.HTTP_201_CREATED)

class LikeReviewView(APIView):
    def post(self, request, location_id, review_id):
        location = get_object_or_404(Location, pk=location_id)
        review = get_object_or_404(Review, pk=review_id)
        user = request.user
        like = Like.objects.filter(user = user, review=review).first()
        if like:
            if like.is_like == True:
                like.is_like = False
                like.save()
            else:
                like.is_like = True
                like.save()
            return Response({"detail" : "Successful change like"} , status=status.HTTP_200_OK)
        else:
            Like.objects.create(user=user, review=review, is_like = True)
            return Response({"detail" : "Successful liked"}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes= [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url=f"http://localhost:8000/api/auth/password-reset/confirm/{uid}/{token}/"

            send_mail(
                "Password reset",
                f"To reset password follow the url {reset_url}",
                "noreply@yourdomain.com",
                [user.email],
                fail_silently=False,
            )

        return Response({"detail" : 'The link send'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, uidb64, token):
        new_password = request.data.get("new_password")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"detail":"Password was successful changed"}, status=status.HTTP_200_OK)
        return Response({"error":"Not valid token or uid"}, status=status.HTTP_400_BAD_REQUEST)