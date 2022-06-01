import os.path
import re
from backend import models
from backend import serializers
from backend.paginations import ProjectFilesPagination
from backend.tasks import storeProjectFiles, storeSectionFiles
from backend.utils import dataUtil
from backend.utils import fileUtil
from d3_bakcend.utils.response import APIResponse
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

authentication_class_list = [SessionAuthentication, BasicAuthentication]


class ProjectFilesFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        is_delete = False if request.query_params.get('is_delete') == 'false' else True
        if request.query_params.get('parent_file_id') is None:
            return queryset.filter(is_delete=is_delete).exclude(parent_file__isnull=False)
        parent_file_id = int(request.query_params.get('parent_file_id'))
        return queryset.filter(Q(is_delete=is_delete) & Q(parent_file=parent_file_id))


# 项目文件和切面文件共同父类
class FilesViewSet(GenericViewSet):
    def uploadZip(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        file_extension = re.findall('(?<=/).*$', file.content_type)[0]
        file_name = file.name.replace('.{}'.format(file_extension), '')
        data = {
            'file': file,
            'file_extension': re.findall('(?<=/).*$', file.content_type)[0],
            'file_name': file_name
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        url = serializer.data['file']
        ori_file = serializer.data['id']
        return data, ori_file, url


class ProjectFilesViewSet(FilesViewSet):
    authentication_classes = authentication_class_list
    # permission_classes = [IsAuthenticated, ]
    parser_classes = [
        JSONParser,
        FormParser,
        MultiPartParser,
    ]
    queryset = models.ProjectFiles.objects.all()
    serializer_class = serializers.ProjectFilesSerializer
    filter_backends = [ProjectFilesFilter]
    pagination_class = ProjectFilesPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.query_params.get('parent_file_id') is None:
            serializer = self.get_serializer(queryset, many=True)
        elif len(queryset.filter(Q(file_name__in=settings.PROJECTFILE_SUB_FOLDER))):
            serializer = serializers.ProjectFileTypesSerializer(queryset, many=True)
        else:
            serializer = serializers.SubProjectFilesSerializer(queryset, many=True)
        return APIResponse(HTTP_200_OK, 'list success', serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(HTTP_200_OK, 'retrieve success', serializer.data)

    def create(self, request, *args, **kwargs):
        channel_id = request.query_params.get('channel_id')
        data, ori_file, url = super().uploadZip(request)
        sub_folder_data = [{
            'file_name': item, 'parent_file': ori_file
        } for item in settings.PROJECTFILE_SUB_FOLDER]
        serializer = self.get_serializer(data=sub_folder_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        parent_file_dict = dict([(item['file_name'], item['id']) for item in serializer.data])
        storeProjectFiles.delay(ori_file, data['file_name'], parent_file_dict, channel_id)
        # dataUtil.post_projectFiles_data(ori_file, file_name, parent_file_dict, channel_id)
        return APIResponse(HTTP_201_CREATED, 'create success',
                           data={'name': data['file_name'], 'type': data['file_extension'], 'url': url})

    def destroy(self, request, *args, **kwargs):
        project_file = self.get_object()
        if project_file.is_delete:
            raise ValidationError
        project_file.is_delete = True
        project_file.save()
        return APIResponse(HTTP_204_NO_CONTENT, 'destroy success', '')

    def get_serializer_context(self):
        return {
            'format': self.format_kwarg,
            'view': self,
        }


class ProjectFilesStructureTreeViewSet(GenericViewSet):
    queryset = models.ProjectFiles.objects.all()
    serializer_class = serializers.ProjectFilesStructureTreeSerializer
    filter_backends = [ProjectFilesFilter]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(HTTP_200_OK, 'list success', serializer.data)


class CatelogueDatasViewSet(GenericViewSet):
    queryset = models.CatelogueDatas.objects.all()
    serializer_class = serializers.CatelogueDatasSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['catelogue_type', 'structure_file']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(HTTP_200_OK, 'list success', serializer.data)


class CatelogueTreeMapDatasFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        structure_file = int(request.query_params.get('structure_file'))
        return queryset.filter(Q(catelogue_type=1) & Q(structure_file_id=structure_file))


class CatelogueTreeMapDatasViewSet(GenericViewSet):
    queryset = models.CatelogueTreeMapDatas.objects.all()
    serializer_class_list = [serializers.CatelogueTreeMapDatasWriteRootSerializer,
                             serializers.CatelogueTreeMapDatasWritePackageSerializer,
                             serializers.CatelogueTreeMapDatasWriteFileSerializer]
    filter_backends = [CatelogueTreeMapDatasFilter]

    def get_serializer_class_from_list(self, item):
        type_num = item.catelogue_type
        end = item.end
        if type_num == 1:
            return self.serializer_class_list[0](item)
        else:
            if end:
                return self.serializer_class_list[2](item)
            else:
                return self.serializer_class_list[1](item)

    def serialize_tree(self, queryset):
        for obj in queryset:
            data = self.get_serializer_class_from_list(obj).data
            if not obj.end:
                data['children'] = self.serialize_tree(obj.children.all())
            yield data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.serialize_tree(queryset)
        return APIResponse(HTTP_200_OK, 'list success', data)


class SectionFilesFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        is_delete = False if request.query_params.get('is_delete') == 'false' else True
        return queryset.filter(Q(section_type=1) & Q(is_delete=is_delete))


class SectionFilesViewSet(FilesViewSet):
    authentication_classes = authentication_class_list
    # permission_classes = [IsAuthenticated, ]
    parser_classes = [
        JSONParser,
        FormParser,
        MultiPartParser,
    ]
    queryset = models.SectionFiles.objects.all()
    serializer_class = serializers.SectionFilesWriteSerializer
    serializer_class_list = [serializers.SectionFilesReadSerializer, serializers.SubSectionFilesReadSerializer]
    filter_backends = [SectionFilesFilter]

    def get_serializer_class_from_list(self, item):
        end = item.end
        return self.serializer_class_list[end](item)

    def serialize_tree(self, queryset):
        for obj in queryset:
            data = self.get_serializer_class_from_list(obj).data
            if not obj.end:
                data['children'] = self.serialize_tree(obj.children.all())
            yield data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.serialize_tree(queryset)
        return APIResponse(HTTP_200_OK, 'list success', data)

    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return APIResponse(HTTP_200_OK, 'retrieve success', serializer.data)

    def create(self, request, *args, **kwargs):
        channel_id = request.query_params.get('channel_id')
        data, ori_file, url = super().uploadZip(request)
        storeSectionFiles.delay(ori_file, channel_id)
        # dataUtil.post_sectionFiles_data(ori_file)
        return APIResponse(HTTP_201_CREATED, 'create success',
                           data={'name': data['file_name'], 'type': data['file_extension'], 'url': url})

    # @action(methods=['get'], detail=False)
    # def list_categories(self, request, *args, **kwargs):
    #     parent_pk = request.query_params.get('parent_pk', None)
    #     queryset = self.filter_queryset(self.get_queryset()).filter(id=parent_pk)
    #     serializer = self.get_serializer(queryset, many=True)
    #     categories = dataUtil.get_section_categories(serializer.data)
    #     return APIResponse(HTTP_200_OK, 'list success', categories)


class SectionFilesStructureTreeViewSet(GenericViewSet):
    queryset = models.SectionFiles.objects.all()
    serializer_class_list = [serializers.SectionFilesStructureTreeSerializer,
                             serializers.SubSectionFilesStructureTreeSerializer]
    filter_backends = [SectionFilesFilter]

    def get_serializer_class_from_list(self, item):
        subEnd = item.subEnd
        return self.serializer_class_list[subEnd](item)

    def serialize_tree(self, queryset):
        for obj in queryset:
            data = self.get_serializer_class_from_list(obj).data
            if not obj.subEnd:
                data['children'] = self.serialize_tree(obj.children.all())
            yield data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.serialize_tree(queryset)
        return APIResponse(HTTP_200_OK, 'list success', data)


class SectionNodesViewSet(GenericViewSet):
    queryset = models.SectionNodes.objects.all()
    serializer_class = serializers.SectionNodesSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['origin_file_id', 'is_delete']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(HTTP_200_OK, 'list success', serializer.data)


class SectionEdgesViewSet(GenericViewSet):
    queryset = models.SectionEdges.objects.all()
    serializer_class = serializers.SectionEdgesSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['origin_file_id', 'is_delete']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(HTTP_200_OK, 'list success', serializer.data)
