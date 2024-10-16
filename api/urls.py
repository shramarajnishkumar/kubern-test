from django.urls import path, include
from .views import GitHubAuth, GitHubCallback,GithubRepository, AppDetailViewSet, PlanViewSet, AppPlanViewSet, FetchUserDetails, GenerateAccessToken, OrganizerGithubViewSet
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'apps', AppDetailViewSet, basename="apps")
router.register(r'plans', PlanViewSet, basename="plans")
router.register(r'app-plans', AppPlanViewSet, basename="app-plans")
router.register(r'organizer-repo', OrganizerGithubViewSet, basename="organizer-repo")



urlpatterns = [
    path('auth/github/', GitHubAuth.as_view(), name='github_auth'),
    path('auth/github/callback/', GitHubCallback.as_view(), name='github_callback'),
    path('auth/github/fetch-details/', FetchUserDetails.as_view(), name="fetch-details"),
    path('auth/github/access-token/', GenerateAccessToken.as_view(), name="access-token"),
    path('auth/github/repo/', GithubRepository.as_view(), name="github-repo"),
    path('', include(router.urls)),
]
