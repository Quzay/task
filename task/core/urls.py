from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import RegisterView, LoginView, LogoutView, LocationViewSet, ReviewViewSet, ExportLocationView,SubscribeLocationView, PasswordResetConfirmView,PasswordResetRequestView, LikeReviewView

router = DefaultRouter()
router.register(r"locations", LocationViewSet, basename='location')

location_router = NestedDefaultRouter(router, r"locations", lookup = 'locations')
location_router.register(r"reviews", ReviewViewSet, basename='location-reviews')


urlpatterns =[
    path("auth/register/", RegisterView.as_view(), name='register'),
    path("auth/login/", LoginView.as_view(), name= 'login'),
    path("auth/logout/", LogoutView.as_view(), name='logout'),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("locations/export/", ExportLocationView.as_view(), name='locations-export'),
    path("locations/<int:location_id>/subscribe/", SubscribeLocationView.as_view(), name='locations-subscribe'),
    path("locations/<int:location_id>/reviews/<int:review_id>/like/", LikeReviewView.as_view(), name="like-review"),
    path("", include(router.urls)),
    path("", include(location_router.urls))
]