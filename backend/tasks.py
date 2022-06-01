from backend.utils.dataUtil import post_projectFiles_data, post_sectionFiles_data
from d3_bakcend.celery.celeryCenter import app as celeryApp


@celeryApp.task(bind=True, name='tasks.storeProjectFiles')
def storeProjectFiles(self, ori_file, file_name, parent_file_dict, channel_id):
    post_projectFiles_data(ori_file, file_name, parent_file_dict, channel_id)
    return 'store projectFiles finished'


@celeryApp.task(bind=True, name='tasks.storeSectionFiles')
def storeSectionFiles(self, ori_file, channel_id):
    post_sectionFiles_data(ori_file, channel_id)
    return 'store sectionFiles finished'
