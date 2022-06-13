import json
from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from backend import models


class SubProjectFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectFiles
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class ProjectFileTypesSerializer(serializers.ModelSerializer):
    children = SubProjectFilesSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProjectFiles
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class ProjectFilesSerializer(serializers.ModelSerializer):
    children = ProjectFileTypesSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProjectFiles
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'is_delete']


class SubProjectFilesStructureTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectFiles
        fields = ['id', 'file_name']


class ProjectFilesStructureTreeSerializer(serializers.ModelSerializer):
    children = SubProjectFilesStructureTreeSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProjectFiles
        fields = ['id', 'file_name', 'children']


# TODO 进一步完善
class JsonSerializer(serializers.JSONField):
    default_error_messages = {'invalid_json': '无效的json数据格式'}

    def to_representation(self, value):
        return json.loads(value)

    # 传入json字符串
    def to_internal_value(self, data):
        return data


class ListSerializer(serializers.ListField):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return ','.join(data)


class CatelogueTreeMapDatasValueListSerializer(serializers.ListField):
    def to_representation(self, value):
        if len(value):
            return list(map(float, value.split(',')))
        return []

    def to_internal_value(self, data):
        return ','.join(map(str, data))


class SubCatelogueDatasSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['structure_file'].write_only = True
        self.fields['parent_catelogue'].write_only = True
        self.fields['catelogue_type'].write_only = True

    relation = JsonSerializer()

    class Meta:
        model = models.CatelogueDatas
        exclude = ['timestamp']


class CatelogueDatasSerializer(serializers.ModelSerializer):
    children = SubCatelogueDatasSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['structure_file'].write_only = True

    class Meta:
        model = models.CatelogueDatas
        fields = ['id', 'name', 'children', 'catelogue_type', 'structure_file']


class CatelogueTreeMapDatasSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['structure_file'].write_only = True

    relation = JsonSerializer()
    value = CatelogueTreeMapDatasValueListSerializer()

    class Meta:
        model = models.CatelogueTreeMapDatas
        fields = '__all__'


class CatelogueTreeMapDatasWriteFileSerializer(serializers.ModelSerializer):
    relation = JsonSerializer()
    value = CatelogueTreeMapDatasValueListSerializer()

    class Meta:
        model = models.CatelogueTreeMapDatas
        fields = ['id', 'name', 'color', 'qualifiedName', 'relation', 'value']


class CatelogueTreeMapDatasWritePackageSerializer(serializers.ModelSerializer):
    value = CatelogueTreeMapDatasValueListSerializer()

    class Meta:
        model = models.CatelogueTreeMapDatas
        fields = ['id', 'name', 'color', 'qualifiedName', 'value', 'children']


class CatelogueTreeMapDatasWriteRootSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CatelogueTreeMapDatas
        fields = ['name', 'children']


class ClusterDatasSerializer(serializers.ModelSerializer):
    relation = JsonSerializer()

    class Meta:
        model = models.ClusterDatas
        fields = '__all__'


class ClusterReadFileSerializer(serializers.ModelSerializer):
    relation = JsonSerializer()

    class Meta:
        model = models.ClusterDatas
        fields = ['name', 'color', 'relation', 'value']


class ClusterDatasReadTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClusterDatas
        fields = ['name', 'color', 'children']


class ClusterDatasReadRootSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClusterDatas
        fields = ['name', 'children']


class SubSectionFilesReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SectionFiles
        exclude = ['is_delete', 'qualifiedName']


class SectionFilesReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SectionFiles
        exclude = ['is_delete', 'qualifiedName', 'status', ]


class SectionFilesWriteSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_file'].write_only = True

    class Meta:
        model = models.SectionFiles
        fields = '__all__'
        read_only_fields = ['timestamp', 'is_delete']


class SubSectionFilesStructureTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SectionFiles
        fields = ['id', 'file_name']


class SectionFilesStructureTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SectionFiles
        fields = ['id', 'file_name', 'children']


class SectionNodesSerializer(serializers.ModelSerializer):
    mode_type = ListSerializer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origin_file_id'].write_only = True

    class Meta:
        model = models.SectionNodes
        exclude = ['id', 'timestamp', 'is_delete']
        read_only_fields = ['timestamp', 'is_delete']


class SectionEdgesSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origin_file_id'].write_only = True

    class Meta:
        model = models.SectionEdges
        exclude = ['id', 'timestamp', 'is_delete']
        read_only_fields = ['timestamp', 'is_delete']
