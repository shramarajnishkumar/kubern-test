from django.shortcuts import redirect
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from .models import AppDetail, Plan, AppPlan, AuthUser,GithbRepo
from django.conf import settings
import requests
from .serializers import AppDetailSerializer, PlanSerializer, AppPlanSerializer, GithubRepoSerializer, CodeSerializer, OrganizerGithubSerializer

class GitHubAuth(APIView):
    def get(self, request):
        client_id = settings.CLIENT_ID  # Replace with your GitHub client ID
        scope = 'user'
        redirect_uri = f'{settings.HOST_URL}/api/auth/github/callback/'  # Ensure this matches GitHub settings
        auth_url = f'https://github.com/login/oauth/authorize?client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}'
        return Response({"Authorize URL": auth_url}, status=status.HTTP_200_OK)

class GitHubCallback(APIView):
    def get(self, request):
        code = request.GET.get('code')
        print('code: ', code)
        if not code:
            return Response({'error': 'Code not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"code":code}, status=status.HTTP_200_OK)
    
class GenerateAccessToken(APIView):
    serializers_class  = CodeSerializer 
    def get(self, request):
        serializer = self.serializers_class(data = request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']

            # Exchange the code for an access token
            token_url = settings.TOKEN_URL
            data = {
                'client_id': settings.CLIENT_ID,  # Replace with your GitHub client ID
                'client_secret': settings.CLIENT_SECRET,  # Replace with your GitHub client secret
                'code': code
            }
            headers = {'Accept': 'application/json'}
            response = requests.post(token_url, data=data, headers=headers)
            token_data = response.json()
            return Response({"data": token_data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=400)
    
class FetchUserDetails(APIView):
    serializers_class  = GithubRepoSerializer 
    def get(self, request):
        serializer = self.serializers_class(data = request.data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']

            if access_token:
                user_info_url = settings.USER_INFO_URL
                headers = {
                    "Authorization": f"token {access_token}"
                }
                user_response = requests.get(user_info_url, headers=headers)
                user_info = user_response.json()

                url = settings.USER_REPO_URL
                response = requests.get(url, headers=headers)
                repositories = []
                for data in response.json():
                    repo_url = f"{data.get('url')}/branches"
                    branches_response = requests.get(repo_url, headers=headers)
                    repositories.append({"id":data.get('id'), "name":data.get('name'), "clone_url":data.get('clone_url'), "private": data.get("private"), 'branches':branches_response.json()})

                print(f"Failed to fetch repositories: {response.status_code}")

                # Create or get the user in your database
                user, created = AuthUser.objects.get_or_create(
                    uid=user_info['id'],
                    provider='github',
                    defaults={
                        'extra_data': user_info
                    }
                )


                user.backend = 'django.contrib.auth.backends.ModelBackend'

                login(request, user)  # Log the user in (this requires that user is a valid Django user)
                user.access_token = str(access_token)
                user.save()
                return Response({
                    'user_info': user_info,
                    'repositories': repositories
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Failed to obtain access token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=400)

class GithubRepository(APIView):
    serializers_class  = GithubRepoSerializer 
    def post(self, request):
        serializer = self.serializers_class(data = request.data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            url = settings.USER_REPO_URL
            headers = {
                "Authorization": f"token {access_token}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                repositories = response.json()
                return Response({"Repository":repositories}, status=status.HTTP_200_OK)
            else:
                print(f"Failed to fetch repositories: {response.status_code}")
                return Response({"msg": "Login Required", "URL":f"{settings.HOST_URL}/api/auth/github/"})
        else:
            # Return validation errors if serializer is not valid
            return Response(serializer.errors, status=400)

class OrganizerGithubViewSet(viewsets.ModelViewSet):
    queryset = GithbRepo.objects.all()
    serializer_class = OrganizerGithubSerializer

class AppDetailViewSet(viewsets.ModelViewSet):
    queryset = AppDetail.objects.all()
    serializer_class = AppDetailSerializer

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

class AppPlanViewSet(viewsets.ModelViewSet):
    queryset = AppPlan.objects.all()
    serializer_class = AppPlanSerializer

    @action(detail=True, methods=['post'])
    def assign_plan(self, request, pk=None):
        app = self.get_object()
        plan_id = request.data.get('plan_id')
        try:
            plan = Plan.objects.get(id=plan_id)
            app_plan = AppPlan.objects.create(app=app, plan=plan)
            return Response({"status": "Plan assigned successfully"}, status=status.HTTP_201_CREATED)
        except Plan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
