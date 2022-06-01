from django.contrib.auth.models import AbstractUser
import os
import uuid
from d3_bakcend.utils.storage import MinioStorage
from django.db import models


def image_path(id, imagename):
    ext = imagename.split('.')[-1]
    image_name = '{0}.{1}'.format(str(uuid.uuid4()), ext)
    return os.path.join('image', 'avator', image_name)


class UserInfo(AbstractUser):
    GENDER_TYPE = (
        (0, '男'),
        (1, '女'),
    )
    phone = models.CharField(default='',
                             max_length=20,
                             unique=True,
                             verbose_name='手机号')
    gender = models.SmallIntegerField(choices=GENDER_TYPE,
                                      verbose_name='性别',
                                      default=0)
    avatar = models.ImageField(default='',
                               max_length=120,
                               storage=MinioStorage(),
                               upload_to='image/avator',
                               verbose_name='用户头像',
                               null=True)

    def realName(self):
        return self.last_name + self.first_name

    class Meta:
        db_table = 'userinfo'
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'