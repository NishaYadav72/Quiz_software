from django.db import models

class UploadFile(models.Model):
    file = models.FileField(upload_to='uploads/')  # Uploaded files yahan store honge
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name  # Admin panel me naam dikhega

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    questions = models.JSONField()  # [{"question":"", "options":["a","b","c"], "answer":""}]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class QuizResult(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    user_name = models.CharField(max_length=100)
    score = models.IntegerField()
    total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.score}/{self.total}"
