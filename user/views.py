import json
from .models import UserInfo
from .serializers import LoginSerializer, UserInfoSerializer
from .utils.decode import base64_decode
from d3_bakcend.utils.response import APIResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import GenericViewSet, ViewSet


class LoginViewSet(ViewSet):

    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {'token': serializer.context.get('token')}
        return APIResponse(HTTP_200_OK, '登录成功', data)


class GetUserInfoViewSet(GenericViewSet):

    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer

    def list(self, request, *args, **kwargs):
        auth = request.META.get('HTTP_AUTHORIZATION')
        payload = auth.split('.')[1]
        res = base64_decode(payload)
        userId = json.loads(res).get('user_id')
        queryset = self.get_queryset().filter(id=userId).first()
        serializer = self.get_serializer(queryset)
        return APIResponse(HTTP_200_OK, '获取用户信息成功', serializer.data)

    def get_serializer_context(self):
        return {
            'format': self.format_kwarg,
            'view': self,
        }
