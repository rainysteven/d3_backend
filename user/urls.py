from django.urls import path
from .views import LoginViewSet, GetUserInfoViewSet
from rest_framework.routers import SimpleRouter
from rest_framework_jwt.views import obtain_jwt_token

router = SimpleRouter()
router.register(r'login', LoginViewSet, 'login')
router.register(r'getUserInfo', GetUserInfoViewSet, 'getUesrInfo')

urlpatterns = [path('obtain/', obtain_jwt_token)]
urlpatterns += router.urls
