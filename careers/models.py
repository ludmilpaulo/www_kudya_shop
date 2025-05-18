from django.db import models


class Career(models.Model):
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    description = models.TextField()      # ← Accepts HTML from CKEditor in frontend
    requirements = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('processing', 'Processing'),
        ('review', 'Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('pt', 'Português'),
]

    career = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='applications')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    def __str__(self):
        return f"{self.full_name} - {self.career.title}"

