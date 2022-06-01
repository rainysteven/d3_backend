import re
from django.db import models
from rest_framework.serializers import ModelSerializer, CharField, IntegerField
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler
from . import models


class LoginSerializer(ModelSerializer):

    username = CharField()

    class Meta:
        model = models.UserInfo
        fields = ['username', 'password']

    def validate(self, attrs):
        user = self.many_method_login(attrs)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        self.context['token'] = token
        return attrs

    def many_method_login(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if re.match('^1[3-9]\d{9}$', username):
            user = models.UserInfo.objects.filter(phone=username).first()
        elif re.match('^.+@.+$', username):
            user = models.UserInfo.objects.filter(email=username).first()
        else:
            user = models.UserInfo.objects.filter(username=username).first()
        if not user or not user.check_password(password):
            raise ValidationError('账号或密码错误')
        return user


class UserInfoSerializer(ModelSerializer):

    userId = IntegerField(source='id')

    class Meta:
        model = models.UserInfo
        fields = [
            'userId',
            'username',
            'realName',
            'avatar',
        ]
