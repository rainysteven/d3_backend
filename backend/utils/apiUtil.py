import os
from functools import wraps
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST


class logit(object):

    def __init__(self, logfile=os.path.join(os.getcwd(),
                                            'static/log/out.log')):
        self.logfile = logfile

    def __call__(self, func):

        @wraps(func)
        def wrapped_function(*args, **kwargs):
            log_string = func.__name__ + " was called"
            # 打开logfile并写入
            with open(self.logfile, 'a') as opened_file:
                # 现在将日志打到指定的文件
                opened_file.write(log_string + '\n')
            response = None
            try:
                response = func(*args, **kwargs)
            except ValidationError:
                response = Response(
                    **get_response(func.__name__ +
                                   ' fail', '', HTTP_400_BAD_REQUEST))
            finally:
                return response

        return wrapped_function
