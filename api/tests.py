from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.conf import settings
from .serializers import CodeSerializer, GithubRepoSerializer, AppDetailSerializer, PlanSerializer, AppPlanSerializer
from .models import AppDetail, GithbRepo, AuthUser, Plan, AppPlan

class GitHubAuthTestCase(TestCase):
    def setUp(self):
        # Initialize the test client
        self.client = APIClient()

        # Define the URL for the GitHub authorization
        self.github_auth_url = reverse('github_auth')

    @patch.object(settings, 'CLIENT_ID', 'your_github_client_id')
    @patch.object(settings, 'HOST_URL', 'http://localhost:8000')
    def test_github_auth_url(self):
        """
        Test that the GitHub authorization URL is generated correctly.
        """
        # Make a GET request to the GitHubAuth API
        response = self.client.get(self.github_auth_url)

        # Check that the status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Get the expected authorization URL based on the test data
        expected_auth_url = 'https://github.com/login/oauth/authorize?client_id=your_github_client_id&scope=user&redirect_uri=http://localhost:8000/api/auth/github/callback/'

        # Check if the response data contains the correct URL
        self.assertEqual(response.json(), {"Authorize URL": expected_auth_url})

class GitHubCallbackTestCase(TestCase):
    
    def setUp(self):
        # Initialize the APIClient for making HTTP requests
        self.client = APIClient()
        
        # Define the URL for the GitHub callback endpoint
        self.github_callback_url = reverse('github_callback')

    def test_github_callback_without_code(self):
        """
        Test that the API returns a 400 error when no 'code' is provided in the query params.
        """
        # Make a GET request to the callback without a 'code' parameter
        response = self.client.get(self.github_callback_url)
        
        # Assert that the status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Assert that the error message is correct
        self.assertEqual(response.json(), {'error': 'Code not provided'})

    def test_github_callback_with_code(self):
        """
        Test that the API returns the 'code' in the response when it is provided.
        """
        # Make a GET request to the callback with a 'code' parameter
        response = self.client.get(self.github_callback_url, {'code': 'test_code_123'})
        
        # Assert that the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert that the response contains the correct 'code'
        self.assertEqual(response.json(), {'code': 'test_code_123'})

class GenerateAccessTokenTestCase(TestCase):
    
    def setUp(self):
        # Initialize the APIClient for making HTTP requests
        self.client = APIClient()
        
        # Define the URL for the GenerateAccessToken endpoint
        self.generate_token_url = reverse('access-token')
        self.serializer = CodeSerializer

    @patch('requests.post')
    @patch.object(settings, 'CLIENT_ID', 'your_github_client_id')
    @patch.object(settings, 'CLIENT_SECRET', 'your_github_client_secret')
    def test_generate_access_token_valid_code(self, mock_post):
        """
        Test that the API returns the token data when a valid 'code' is provided.
        """
        # Mock the response from GitHub when exchanging the code for an access token
        mock_response_data = {
            'access_token': 'fake_token_123',
            'token_type': 'bearer',
            'scope': 'repo'
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response_data
        
        # Make a GET request with valid 'code'
        request_data = {'code': 'valid_code_123'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            data = {
                'code': code
            }
            response = self.client.get(self.generate_token_url, data=data)
            print('response: ', response.json())
            
            # Assert that the status code is 200 OK
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Assert that the token data is returned in the response
            self.assertEqual(response.json()['data'], mock_response_data)

    def test_generate_access_token_invalid_code(self):
        """
        Test that the API returns a 400 error when no 'code' is provided in the request.
        """
        # Make a GET request without 'code' in the data
        response = self.client.get(self.generate_token_url, data={})
        
        # Assert that the status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Assert that the error message is about the missing 'code'
        self.assertIn('code', response.json())

class FetchUserDetailsTests(APITestCase):
    def setUp(self):
        self.fetch_user_details_url = reverse('fetch-details')  # Ensure this matches your URL pattern name
        self.serializer = GithubRepoSerializer

    @patch('requests.get')
    def test_fetch_user_details_success(self, mock_get):
        """
        Test that the API returns user info and repositories when a valid access token is provided.
        """
        # Mock user info response
        mock_user_info_response = {
            'id': 123,
            'login': 'testuser',
            'name': 'Test User',
            'email': 'testuser@example.com'
        }
        mock_repos_response = [
            {
                'id': 1,
                'name': 'Repo1',
                'clone_url': 'https://github.com/testuser/repo1.git',
                'private': False,
                'url': 'https://api.github.com/repos/testuser/repo1'
            },
            {
                'id': 2,
                'name': 'Repo2',
                'clone_url': 'https://github.com/testuser/repo2.git',
                'private': True,
                'url': 'https://api.github.com/repos/testuser/repo2'
            }
        ]
        mock_branches_response = [{'name': 'main'}, {'name': 'dev'}]

        # Setup mock return values
        mock_get.side_effect = [
            mock_user_info_response,  # First call for user info
            mock_repos_response,       # Second call for repositories
            mock_branches_response,     # Third call for branches of Repo1
            mock_branches_response      # Fourth call for branches of Repo2
        ]

        request_data = {'access_token': 'valid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            data = {'access_token': access_token}
            response = self.client.get(self.fetch_user_details_url, data=data)

            # Assert that the status code is 200 OK
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Assert that user info and repositories are returned in the response
            self.assertEqual(response.data['user_info'], mock_user_info_response)
            self.assertEqual(len(response.data['repositories']), 2)
            self.assertEqual(response.data['repositories'][0]['name'], 'Repo1')
            self.assertEqual(response.data['repositories'][1]['name'], 'Repo2')

    @patch('requests.get')
    def test_fetch_user_details_invalid_access_token(self, mock_get):
        """
        Test that the API returns an error when an invalid access token is provided.
        """
        # Mock response to indicate failure
        mock_get.side_effect = [
            {'error': 'invalid_token'},  # User info fails
            {'error': 'invalid_token'}   # Repos fail
        ]

        request_data = {'access_token': 'invalid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            data = {'access_token': access_token}
            response = self.client.get(self.fetch_user_details_url, data=data)

            # Assert that the status code is 400 Bad Request
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)

    def test_fetch_user_details_missing_access_token(self):
        """
        Test that the API returns an error when the access token is missing.
        """
        request_data = {}
        response = self.client.get(self.fetch_user_details_url, data=request_data)

        # Assert that the status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that the response contains the appropriate error message
        self.assertNotIn('access_token', response.data['access_token'])
        self.assertEqual(response.data['access_token'][0], 'This field is required.')

    @patch('requests.get')
    @patch.object(settings, 'USER_REPO_URL', 'https://example.com')
    def test_fetch_user_details_user_not_found(self, mock_get):
        """
        Test that the API handles a case where the user is not found.
        """
        # Mock user info response to simulate not found
        mock_get.side_effect = [
            {'message': 'Not Found'},  # User info fails
            []                          # Repos return empty
        ]

        request_data = {'access_token': 'valid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            data = {'access_token': access_token}
            response = self.client.get(self.fetch_user_details_url, data=data)
            print('response: ', response.json())

            # Assert that the status code is 400 Bad Request
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)

class GithubRepositoryTests(APITestCase):
    def setUp(self):
        self.github_repository_url = reverse('github-repo')  # Ensure this matches your URL pattern name
        self.serializer = GithubRepoSerializer

    @patch('requests.get')
    @patch.object(settings, 'USER_REPO_URL', 'https://example.com')
    def test_fetch_repositories_success(self, mock_get):
        """
        Test that the API returns repositories when a valid access token is provided.
        """
        # Mock repositories response
        mock_repositories_response = [
            {
                'id': 1,
                'name': 'Repo1',
                'clone_url': 'https://github.com/testuser/repo1.git',
                'private': False
            },
            {
                'id': 2,
                'name': 'Repo2',
                'clone_url': 'https://github.com/testuser/repo2.git',
                'private': True
            }
        ]

        # Setup mock return value for requests.get
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_repositories_response

        request_data = {'access_token': 'valid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            request_data = {'access_token': access_token}
            response = self.client.post(self.github_repository_url, data=request_data)

            # Assert that the status code is 200 OK
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Assert that the repository data is returned in the response
            self.assertEqual(response.data['Repository'], mock_repositories_response)

    @patch('requests.get')
    def test_fetch_repositories_invalid_access_token(self, mock_get):
        """
        Test that the API returns a login required message when an invalid access token is provided.
        """
        # Mock response to indicate failure
        mock_get.return_value.status_code = 401  # Unauthorized

        request_data = {'access_token': 'invalid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            request_data = {'access_token': access_token}
            response = self.client.post(self.github_repository_url, data=request_data)

            # Assert that the status code is 200 OK
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Assert that the message indicates login is required
            self.assertEqual(response.data['msg'], "Login Required")
            self.assertIn('URL', response.data)

    def test_fetch_repositories_missing_access_token(self):
        """
        Test that the API returns an error when the access token is missing.
        """
        request_data = {}
        response = self.client.post(self.github_repository_url, data=request_data)

        # Assert that the status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that the response contains the appropriate error message
        self.assertNotIn('access_token', response.data['access_token'])
        self.assertEqual(response.data['access_token'][0], 'This field is required.')

    @patch('requests.get')
    def test_fetch_repositories_other_error(self, mock_get):
        """
        Test that the API handles other types of errors from the GitHub API.
        """
        # Mock response for a different error
        mock_get.return_value.status_code = 500  # Internal Server Error

        request_data = {'access_token': 'valid_access_token'}
        serializer = self.serializer(data=request_data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            request_data = {'access_token': access_token}
            response = self.client.post(self.github_repository_url, data=request_data)

            # Assert that the status code is 200 OK
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Assert that the message indicates a login requirement
            self.assertEqual(response.data['msg'], "Login Required")
            self.assertIn('URL', response.data)

class OrganizerGithubViewSetTests(APITestCase):
    def setUp(self):
        self.user = AuthUser.objects.create(uid=1, provider='github')  # Create a test user
        self.github_repo_url = reverse('organizer-repo-list')  # Ensure this matches your URL pattern name
        self.github_repo = GithbRepo.objects.create(
            organizer=self.user,
            repository='TestRepo',
            branches='main'
        )

    def test_create_github_repo(self):
        """
        Test that a new GitHub repository can be created.
        """
        request_data = {
            'organizer': self.user.id,
            'repository': 'NewRepo',
            'branches': 'develop'
        }
        response = self.client.post(self.github_repo_url, data=request_data)

        # Assert that the status code is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that the repository was created in the database
        self.assertEqual(GithbRepo.objects.count(), 2)  # One existing repo plus the new one
        self.assertEqual(GithbRepo.objects.last().repository, 'NewRepo')

    def test_list_github_repos(self):
        """
        Test that the list of GitHub repositories can be retrieved.
        """
        response = self.client.get(self.github_repo_url)

        # Assert that the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response contains the existing repository
        self.assertEqual(len(response.data), 1)  # We have one repo in the setup
        self.assertEqual(response.data[0]['repository'], self.github_repo.repository)

    def test_retrieve_github_repo(self):
        """
        Test that a specific GitHub repository can be retrieved.
        """
        url = reverse('organizer-repo-detail', args=[self.github_repo.id])  # Ensure this matches your URL pattern name
        response = self.client.get(url)

        # Assert that the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response data matches the repository
        self.assertEqual(response.data['repository'], self.github_repo.repository)

    def test_update_github_repo(self):
        """
        Test that an existing GitHub repository can be updated.
        """
        url = reverse('organizer-repo-detail', args=[self.github_repo.id])  # Ensure this matches your URL pattern name
        request_data = {
            'repository': 'UpdatedRepo',
            'branches': 'main'
        }
        response = self.client.put(url, data=request_data)

        # Assert that the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the repository was updated in the database
        self.github_repo.refresh_from_db()
        self.assertEqual(self.github_repo.repository, 'UpdatedRepo')

    def test_delete_github_repo(self):
        """
        Test that an existing GitHub repository can be deleted.
        """
        url = reverse('organizer-repo-detail', args=[self.github_repo.id])  # Ensure this matches your URL pattern name
        response = self.client.delete(url)

        # Assert that the status code is 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Assert that the repository was deleted from the database
        self.assertEqual(GithbRepo.objects.count(), 0)

class AppDetailViewSetTestCase(APITestCase):
    
    def setUp(self):
        # Setup required data for tests
        self.client = APIClient()
        self.organizer_user = AuthUser.objects.create(uid=1, provider="github")
        self.repo = GithbRepo.objects.create(
            organizer=self.organizer_user,
            repository="sample-repo",
            branches="main"
        )
        self.app_detail = AppDetail.objects.create(
            organizer=self.repo,
            region="us-west",
            framework="react"
        )
        self.app_detail_url = reverse('apps-detail', args=[self.app_detail.id])
        self.apps_list_url = reverse('apps-list')
    
    def test_list_app_details(self):
        # Test listing all app details
        response = self.client.get(self.apps_list_url)
        app_details = AppDetail.objects.all()
        serializer = AppDetailSerializer(app_details, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_retrieve_app_detail(self):
        # Test retrieving a single app detail by id
        response = self.client.get(self.app_detail_url)
        app_detail = AppDetail.objects.get(id=self.app_detail.id)
        serializer = AppDetailSerializer(app_detail)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_app_detail(self):
        # Test creating a new app detail
        data = {
            'organizer': self.repo.id,
            'region': 'us-east',
            'framework': 'vuejs'
        }
        response = self.client.post(self.apps_list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AppDetail.objects.count(), 2)
        self.assertEqual(AppDetail.objects.last().region, 'us-east')
    
    def test_update_app_detail(self):
        # Test updating an existing app detail
        data = {
            'region': 'eu-central',
            'framework': 'rubyonrails'
        }
        response = self.client.put(self.app_detail_url, data)
        self.app_detail.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.app_detail.region, 'eu-central')
        self.assertEqual(self.app_detail.framework, 'rubyonrails')
    
    def test_delete_app_detail(self):
        # Test deleting an existing app detail
        response = self.client.delete(self.app_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AppDetail.objects.count(), 0)

class PlanViewSetTestCase(APITestCase):

    def setUp(self):
        # Setup required data for tests
        self.client = APIClient()
        
        # Create two sample Plan objects
        self.plan1 = Plan.objects.create(
            plan_type="starter",
            storage=50,
            bandwidth=100,
            memory=4,
            cpu=2,
            monthly_cost=10.00,
            price_per_hour=0.01
        )
        
        self.plan2 = Plan.objects.create(
            plan_type="pro",
            storage=200,
            bandwidth=500,
            memory=16,
            cpu=4,
            monthly_cost=30.00,
            price_per_hour=0.05
        )
        
        # URLs for the PlanViewSet
        self.plan_list_url = reverse('plans-list')
        self.plan_detail_url = reverse('plans-detail', args=[self.plan1.id])
    
    def test_list_plans(self):
        # Test listing all plans
        response = self.client.get(self.plan_list_url)
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_retrieve_plan(self):
        # Test retrieving a single plan by id
        response = self.client.get(self.plan_detail_url)
        plan = Plan.objects.get(id=self.plan1.id)
        serializer = PlanSerializer(plan)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
    
    def test_create_plan(self):
        # Test creating a new plan
        data = {
            'plan_type': 'enterprise',
            'storage': 1000,
            'bandwidth': 2000,
            'memory': 64,
            'cpu': 8,
            'monthly_cost': 100.00,
            'price_per_hour': 0.10
        }
        response = self.client.post(self.plan_list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Plan.objects.count(), 3)
        self.assertEqual(Plan.objects.last().plan_type, 'enterprise')
    
    def test_update_plan(self):
        # Test updating an existing plan
        data = {
            'plan_type': 'pro',
            'storage': 500,
            'bandwidth': 1000,
            'memory': 32,
            'cpu': 6,
            'monthly_cost': 50.00,
            'price_per_hour': 0.02
        }
        response = self.client.put(self.plan_detail_url, data)
        self.plan1.refresh_from_db()  # Refresh the object from database
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.plan1.plan_type, 'pro')
        self.assertEqual(self.plan1.storage, 500)
        self.assertEqual(self.plan1.bandwidth, 1000)
    
    def test_partial_update_plan(self):
        # Test partially updating an existing plan (PATCH)
        data = {
            'memory': 32,
            'cpu': 8
        }
        response = self.client.patch(self.plan_detail_url, data)
        self.plan1.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.plan1.memory, 32)
        self.assertEqual(self.plan1.cpu, 8)
    
    def test_delete_plan(self):
        # Test deleting an existing plan
        response = self.client.delete(self.plan_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Plan.objects.count(), 1)

class AppPlanViewSetTestCase(APITestCase):

    def setUp(self):
        # Setup required data for tests
        self.client = APIClient()
        
        # Create sample data for AppDetail, Plan, and AppPlan models
        self.auth_user = AuthUser.objects.create(uid=1, provider="github")
        self.repo = GithbRepo.objects.create(organizer=self.auth_user, repository="sample-repo")
        self.app_detail = AppDetail.objects.create(
            organizer=self.repo,
            region="us-west",
            framework="react"
        )
        self.plan = Plan.objects.create(
            plan_type="starter",
            storage=50,
            bandwidth=100,
            memory=4,
            cpu=2,
            monthly_cost=10.00,
            price_per_hour=0.01
        )
        self.app_plan = AppPlan.objects.create(app=self.app_detail, plan=self.plan)

        # URLs
        self.app_plan_list_url = reverse('app-plans-list')
        self.app_plan_detail_url = reverse('app-plans-detail', args=[self.app_plan.id])
        self.assign_plan_url = reverse('app-plans-assign-plan', args=[self.app_detail.id])

    def test_list_app_plans(self):
        # Test listing all app plans
        response = self.client.get(self.app_plan_list_url)
        app_plans = AppPlan.objects.all()
        serializer = AppPlanSerializer(app_plans, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_app_plan(self):
        # Test retrieving a single app plan
        response = self.client.get(self.app_plan_detail_url)
        app_plan = AppPlan.objects.get(id=self.app_plan.id)
        serializer = AppPlanSerializer(app_plan)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_app_plan(self):
        # Test creating a new app plan
        data = {
            'app': self.app_detail.id,
            'plan': self.plan.id
        }
        response = self.client.post(self.app_plan_list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AppPlan.objects.count(), 2)

    def test_update_app_plan(self):
        # Test updating an existing app plan
        new_plan = Plan.objects.create(
            plan_type="pro",
            storage=200,
            bandwidth=500,
            memory=16,
            cpu=4,
            monthly_cost=30.00,
            price_per_hour=0.05
        )
        data = {
            'app': self.app_detail.id,
            'plan': new_plan.id
        }
        response = self.client.put(self.app_plan_detail_url, data)
        self.app_plan.refresh_from_db()  # Refresh the object from database
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.app_plan.plan, new_plan)

    def test_delete_app_plan(self):
        # Test deleting an app plan
        response = self.client.delete(self.app_plan_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AppPlan.objects.count(), 0)

    def test_assign_plan_success(self):
        # Test assigning a plan to an app
        new_plan = Plan.objects.create(
            plan_type="enterprise",
            storage=1000,
            bandwidth=2000,
            memory=64,
            cpu=8,
            monthly_cost=100.00,
            price_per_hour=0.10
        )
        data = {'plan_id': new_plan.id}
        response = self.client.post(self.assign_plan_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AppPlan.objects.last().plan, new_plan)
        self.assertEqual(response.data, {"status": "Plan assigned successfully"})

    def test_assign_plan_failure(self):
        # Test assigning a plan with invalid plan_id (Plan does not exist)
        data = {'plan_id': 999}  # Non-existing Plan ID
        response = self.client.post(self.assign_plan_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Plan not found"})



