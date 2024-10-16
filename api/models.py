from django.db import models

# Create your models here.

class AuthUser(models.Model):
    uid = models.IntegerField()
    provider = models.CharField(max_length=255, choices="", default="github")
    extra_data = models.JSONField(default={})
    access_token = models.CharField(max_length=255, null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Add last_login field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AuthUser_{self.uid}"
    
class GithbRepo(models.Model):
    organizer = models.ForeignKey(AuthUser, on_delete=models.CASCADE, blank=True, null=True)
    repository = models.CharField(max_length=255, null=True, blank=True)
    branches = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organizer.uid}_{self.repository}"
    

class AppDetail(models.Model):
    organizer = models.ForeignKey(GithbRepo, on_delete=models.CASCADE, blank=True, null=True) 
    region = models.CharField(max_length=255, blank=True, null=True)
    framework = models.CharField(max_length=255, blank=True, null=True, choices=[
        ('vuejs', 'Vue.js'),
        ('react', 'React'),
        ('expressjs', 'Express.js'),
        ('rubyonrails', 'Ruby on Rails')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organizer.repository} ({self.region} - {self.framework})"
    


class Plan(models.Model):
    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    plan_type = models.CharField(max_length=255, choices=PLAN_CHOICES)
    storage = models.IntegerField(help_text="Storage in GB")
    bandwidth = models.IntegerField(help_text="Bandwidth in GB")
    memory = models.IntegerField(help_text="Memory (RAM) in GB")
    cpu = models.IntegerField(help_text="CPU cores")
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan_type} Plan"
    

class AppPlan(models.Model):
    app = models.ForeignKey(AppDetail, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.app.region} - {self.plan.plan_type}"
    

class DatabasePlan(models.Model):
    PLAN_CHOICES = [
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('oracle', 'Oracle'),
    ]
    owner = models.ForeignKey(AuthUser, on_delete=models.CASCADE, null=True, blank=True)
    database_type = models.CharField(max_length=255, choices=PLAN_CHOICES, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner.uid} Database Plan of {self.database_type}"