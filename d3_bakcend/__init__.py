from __future__ import absolute_import, unicode_literals
import pymysql
from .celery.celeryCenter import app as celery_app

__all__ = ['celery_app']
pymysql.install_as_MySQLdb()