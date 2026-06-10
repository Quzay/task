from django.contrib.auth import authenticate , login, logout
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from .serializers import RegisterSerializer, LocationSerializer, ReviewSerializer
from .models import Location, Review
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

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    

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