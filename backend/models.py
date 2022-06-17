import re
import os
from django.db import models
from d3_bakcend.utils.storage import MinioStorage


def projectFiles_folder_path(instance, file_name):
    ext = re.findall(
        '[^\.]\w*$',
        file_name)[0] if file_name.find('zip') != -1 else file_name
    return os.path.join('projectFile', ext)


class CommonAttribute(models.Model):
    timestamp = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        abstract = True


class FileAttribute(CommonAttribute):
    file_extension = models.CharField(default='',
                                      max_length=10,
                                      verbose_name='文件类型')
    file_name = models.CharField(default='',
                                 max_length=100,
                                 verbose_name='文件名称')
    status = models.BooleanField(verbose_name='是否解析', null=True)
    parent_file = models.ForeignKey(to='self',
                                    on_delete=models.CASCADE,
                                    null=True,
                                    blank=True,
                                    verbose_name='上级文件',
                                    related_name='children')

    class Meta:
        abstract = True


class ProjectFiles(FileAttribute):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_dict = {0: '结构文件', 1: '统计文件', 2: '依赖文件'}

    file = models.FileField(default='',
                            max_length=120,
                            storage=MinioStorage(),
                            upload_to=projectFiles_folder_path,
                            verbose_name='文件',
                            null=True)
    file_type = models.SmallIntegerField(verbose_name='文件类别', null=True)

    class Meta:
        db_table = '项目文件表'
        verbose_name = '项目文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file_name


class CatelogueAttributes(CommonAttribute):
    name = models.CharField(default='',
                            max_length=150,
                            verbose_name='文件名称',
                            null=True)
    color = models.CharField(default='#FFFFFF',
                             max_length=30,
                             verbose_name='圆圈颜色',
                             null=True)
    relation = models.CharField(default='',
                                max_length=600,
                                verbose_name='依赖变化',
                                null=True,
                                blank=True)
    structure_file = models.ForeignKey(ProjectFiles,
                                       on_delete=models.CASCADE,
                                       null=True,
                                       blank=True,
                                       verbose_name='结构文件')

    class Meta:
        abstract = True


class CatelogueDatas(CatelogueAttributes):
    # TODO 采用递归序列化recursive
    CATELOGUE_TYPE = (
        (1, '一级目录'),
        (2, '二级目录'),
    )
    _id = models.IntegerField(default=0, verbose_name='原始ID', null=True)
    changeLoc = models.IntegerField(default=0, verbose_name='修改频率', null=True)
    value = models.FloatField(default=0.0, verbose_name='半径', null=True)
    parent_catelogue = models.ForeignKey(to='self',
                                         on_delete=models.CASCADE,
                                         null=True,
                                         blank=True,
                                         verbose_name='父类目录',
                                         related_name='children')
    catelogue_type = models.SmallIntegerField(choices=CATELOGUE_TYPE,
                                              verbose_name='目录级别',
                                              default=1,
                                              null=False)
    cells = models.CharField(default='',
                             max_length=3000,
                             verbose_name='依赖情况',
                             null=True,
                             blank=True)

    class Meta:
        db_table = '目录数据表'
        verbose_name = '目录数据'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class CatelogueTreeMapDatas(CatelogueAttributes):
    end = models.BooleanField(default=False, null=True, blank=True)
    value = models.CharField(default='', max_length=50, null=True, blank=True)
    qualifiedName = models.CharField(default='',
                                     max_length=150,
                                     verbose_name='文件完整名称',
                                     null=True,
                                     blank=True)
    parent_catelogue = models.ForeignKey(to='self',
                                         on_delete=models.CASCADE,
                                         null=True,
                                         blank=True,
                                         verbose_name='父类目录',
                                         related_name='children')
    catelogue_type = models.SmallIntegerField(verbose_name='目录级别',
                                              default=1,
                                              null=False)

    class Meta:
        db_table = '目录树状数据表'
        verbose_name = '目录树状数据表'
        verbose_name_plural = verbose_name
        ordering = ['id']


class ClusterDatas(CatelogueAttributes):
    changeLoc = models.IntegerField(default=0, verbose_name='修改频率', null=True)
    value = models.FloatField(default=0.0, verbose_name='半径', null=True)
    parent_node = models.ForeignKey(to='self',
                                    on_delete=models.CASCADE,
                                    null=True,
                                    blank=True,
                                    verbose_name='父类结点',
                                    related_name='children')
    cluster = models.SmallIntegerField(verbose_name='目录级别',
                                       default=0,
                                       null=False)

    class Meta:
        db_table = '聚类数据表'
        verbose_name = '聚类数据'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class ProjectFileEdges(CommonAttribute):
    source = models.IntegerField(default=0, null=False)
    target = models.IntegerField(default=0, null=False)
    values = models.CharField(default='',
                              max_length=200,
                              verbose_name='依赖类型',
                              null=True,
                              blank=True)
    structure_file = models.ForeignKey(ProjectFiles,
                                       on_delete=models.CASCADE,
                                       null=True,
                                       blank=True,
                                       verbose_name='结构文件')

    class Meta:
        db_table = '代码依赖边表'
        verbose_name = '代码依赖边'
        verbose_name_plural = verbose_name
        ordering = ['id']

        def __str__(self):
            return self.id


def sectionFiles_folder_path(instance, file_name):
    ext = re.findall(
        '[^\.]\w*$',
        file_name)[0] if file_name.find('zip') != -1 else file_name
    return os.path.join('sectionFile', ext)


class SectionFiles(FileAttribute):
    file = models.FileField(default='',
                            max_length=120,
                            storage=MinioStorage(),
                            upload_to=sectionFiles_folder_path,
                            verbose_name='文件',
                            null=True)
    section_type = models.SmallIntegerField(default=1, null=False)
    mode_type = models.CharField(default='',
                                 max_length=100,
                                 verbose_name='模式类型')
    qualifiedName = models.CharField(default='', max_length=200, null=False)
    end = models.BooleanField(default=False, null=True, blank=True)
    subEnd = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        db_table = '依赖切面文件表'
        verbose_name = '依赖切面文件'
        verbose_name_plural = verbose_name
        ordering = ['id']

        def __str__(self):
            return self.file_name


class SectionAttribute(CommonAttribute):
    origin_file_id = models.IntegerField(default=1, null=False)

    class Meta:
        abstract = True


class SectionNodes(SectionAttribute):
    _id = models.IntegerField(default=0, null=False)
    isHonor = models.SmallIntegerField(default=0, null=False)
    category = models.CharField(default='', max_length=30, null=False)
    qualifiedName = models.CharField(default='', max_length=200, null=False)
    name = models.CharField(default='', max_length=100, null=False)
    File = models.CharField(default='', max_length=150, null=True)
    packageName = models.CharField(default='', max_length=100, null=True)
    hidden = models.BooleanField(default=False)
    modifiers = models.CharField(max_length=30, null=True)
    _global = models.BooleanField(null=True)
    mode_type = models.CharField(default='',
                                 max_length=100,
                                 verbose_name='模式类型',
                                 null=True)

    class Meta:
        db_table = '依赖切面结点表'
        verbose_name = '依赖切面结点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self._id


class SectionEdges(SectionAttribute):
    source = models.IntegerField(default=0, null=False)
    target = models.IntegerField(default=0, null=False)
    sourceFile = models.CharField(default='', max_length=150, null=True)
    sourcePackageName = models.CharField(default='', max_length=100, null=True)
    # 0 原生 1 伴生
    sourceIsHonor = models.SmallIntegerField(default=0, null=False)
    targetFile = models.CharField(default='', max_length=150, null=True)
    targetPackageName = models.CharField(default='', max_length=100, null=True)
    targetIsHonor = models.SmallIntegerField(default=0, null=False)
    value = models.CharField(default='',
                             max_length=30,
                             null=True,
                             verbose_name='依赖关系')
    mode_type = models.CharField(default='',
                                 max_length=50,
                                 verbose_name='模式类型',
                                 null=True)

    class Meta:
        db_table = '依赖切面边表'
        verbose_name = '依赖切面边'
        verbose_name_plural = verbose_name
