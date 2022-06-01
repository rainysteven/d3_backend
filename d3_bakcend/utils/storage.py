import json
import os
import uuid
import mimetypes

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from minio import Minio
from minio.error import MinioException


# TODO minio使用nginx反向代理 可以下载json文件
@deconstructible
class MinioStorage(Storage):
    def __init__(self) -> None:
        if not settings.MINIO_CONF:
            raise ValueError('required MINIO_CONF  config in django.settings: format is:\n{}'.format(
                {'endpoint': '127.0.0.1:9000',
                 'access_key': 'username',
                 'secret_key': 'password',
                 'secure': False,
                 }
            ))
        self.minio_conf = settings.MINIO_CONF
        self.endpoint = settings.MINIO_CONF.get('endpoint')
        self.minio_client = Minio(**self.minio_conf)
        if not self.minio_client.bucket_exists(settings.MINIO_BUCKET):
            self.minio_client.make_bucket(settings.MINIO_BUCKET)
        self.bucket_name = settings.MINIO_BUCKET

    def _open(self, name, mode='rb'):
        if mode != 'rb':
            raise ValueError(
                'minio files can only be opened in read-only mode')
        data = self.get_minio_object(self.bucket_name, name)
        return ContentFile(data)

    def _save(self, name, content):
        content_type = mimetypes.guess_type(name, strict=False)[0]
        content_type = content_type or "application/octet-stream"
        self.set_bucket_policy_public(self.bucket_name)
        try:
            self.minio_client.get_bucket_policy(self.bucket_name)
        except MinioException:
            self.set_bucket_policy_public(self.bucket_name)
        self.minio_client.put_object(self.bucket_name,
                                     name,
                                     content,
                                     content.size,
                                     content_type=content_type)
        return name

    def set_bucket_policy_public(self, bucket_name):
        policy = {
            'Version': '2012-10-17',
            'Statement': [
                {'Effect': 'Allow',
                 'Principal': '*',
                 'Action': ['s3:GetBucketLocation', 's3:ListBucket'],
                 'Resource': ['arn:aws:s3:::{}'.format(bucket_name)]},
                {'Effect': 'Allow',
                 'Principal': '*',
                 'Action': ['s3:GetObject'],
                 'Resource': ['arn:aws:s3:::{}/*'.format(bucket_name)]}
            ]
        }
        self.minio_client.set_bucket_policy(bucket_name, json.dumps(policy))

    def get_valid_name(self, name: str) -> str:
        return super(MinioStorage, self).get_valid_name(name)

    def get_available_name(self, name: str, max_length=None) -> str:
        """
        使用<upload_to>/<uuid>.<file_ext>作为object_name上传到minio上
        """
        if name.find('zip') != -1:
            dir_name = name
            file_extension = os.path.split(name)[1]
        else:
            dir_name = os.path.split(name)[0]
            file_extension = os.path.splitext(name)[1].strip('.')
        object_name = os.path.join(dir_name,
                                   str(uuid.uuid4()) + '.{}'.format(file_extension)).replace(
            "\\", '/').lstrip('/')
        while self.exists(object_name):
            object_name = os.path.join(dir_name,
                                       str(uuid.uuid4()) + '.{}'.format(file_extension)).replace(
                "\\", '/').lstrip('/')
        return object_name

    def url(self, name) -> str:
        return 'http://{}/{}/{}'.format(self.endpoint, self.bucket_name, name)

    def exists(self, name):
        return False

    def get_minio_object(self, bucket_name, object_name):
        response = None
        try:
            response = self.minio_client.get_object(bucket_name, object_name)
            return response.data
        except MinioException as err:
            print(err)

    def delete(self, name):
        pass
