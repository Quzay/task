from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import RegisterView, LoginView, LogoutView, LocationViewSet, ReviewViewSet, ExportLocationView,SubscribeLocationView

router = DefaultRouter()
router.register(r"locations", LocationViewSet, basename='location')

location_router = NestedDefaultRouter(router, r"locations", lookup = 'locations')
location_router.register(r"reviews", ReviewViewSet, basename='location-reviews')


urlpatterns =[
    path("auth/register/", RegisterView.as_view(), name='register'),
    path("auth/login/", LoginView.as_view(), name= 'login'),
    path("auth/logout/", LogoutView.as_view(), name='logout'),
    path("locations/export/", ExportLocationView.as_view(), name='locations-export'),
    path("locations/<int:location_id>/subscribe/", SubscribeLocationView.as_view(), name='locations-subsribe'),
    path("", include(router.urls)),
    path("", include(location_router.urls))
]