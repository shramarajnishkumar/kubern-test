from rest_framework import serializers
from .models import AppDetail, AppPlan, AuthUser, Plan, GithbRepo


class GithubRepoSerializer(serializers.Serializer):
    access_token = serializers.CharField(min_length=40,allow_blank=False)

class CodeSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=20, allow_blank=False, required=True)


class OrganizerGithubSerializer(serializers.ModelSerializer):
    class Meta:
        model = GithbRepo
        fields = '__all__'

class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppDetail
        fields = '__all__'


class AppDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppDetail
        fields = '__all__'

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class AppPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppPlan
        fields = '__all__'