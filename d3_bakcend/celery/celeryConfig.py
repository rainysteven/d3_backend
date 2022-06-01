# 任务存储
broker_url = 'amqp://d3Coder:wang120638@localhost:5672/d3Vhost'


# 时区
timezone = 'Asia/Shanghai'
task_ignore_result = True
# 任务序列化数据格式
task_serializer = 'json'
# 结果序列化数据格式
result_serializer = 'json'

# 为防止内存泄漏，一个进程执行过N次之后杀死，建议是100次，我没听
worker_max_tasks_per_child = 10
# 错误 DatabaseWrapper objects created in a thread can only be used in that same thread
CELERY_TASK_ALWAYS_EAGER = True