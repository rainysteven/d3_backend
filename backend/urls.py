from django.urls import path, include
from rest_framework.routers import SimpleRouter
from backend import views

router = SimpleRouter()
router.register('records', views.ProjectFilesViewSet)
router.register('records_structureTree', views.ProjectFilesStructureTreeViewSet)
router.register('catelogues', views.CatelogueDatasViewSet)
router.register('catelogues/TreeMap', views.CatelogueTreeMapDatasViewSet)
router.register('clusters', views.ClusterDatasViewSet)
router.register('recordsEdges', views.ProjectFileEdgesViewSet)
router.register('sections', views.SectionFilesViewSet)
router.register('sections_structureTree', views.SectionFilesStructureTreeViewSet)
router.register('sectionNodes', views.SectionNodesViewSet)
router.register('sectionEdges', views.SectionEdgesViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
