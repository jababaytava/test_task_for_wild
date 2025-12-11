from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .views import TaskViewSet, WorkerViewSet, StatsSummaryView, StatsWorkersView


router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"workers", WorkerViewSet, basename="worker")

urlpatterns = [
    path("", include(router.urls)),
    path("stats/summary/", StatsSummaryView.as_view(), name="stats-summary"),
    path("stats/workers/", StatsWorkersView.as_view(), name="stats-workers"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
    re_path(
        r"^schema\.(?P<format>json|yaml)$",
        SpectacularAPIView.as_view(),
        name="schema-formatted",
    ),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
