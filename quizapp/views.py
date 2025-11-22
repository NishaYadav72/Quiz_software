from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import Quiz, QuizResult
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from .ai_utils import (
    extract_text_from_pdf,
    extract_text_from_image,
    extract_text_from_video,
    generate_text_questions
)
import json


def home(request):
    return render(request, 'home.html')


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save()
            file_path = file_instance.file.path
            ext = file_path.split('.')[-1].lower()

            # --------------------------------
            # 1️⃣ Extract Text From File
            # --------------------------------
            if ext == 'pdf':
                text = extract_text_from_pdf(file_path)
            elif ext in ['png', 'jpg', 'jpeg']:
                text = extract_text_from_image(file_path)
            elif ext in ['mp4', 'mov', 'avi']:
                text = extract_text_from_video(file_path)
            else:
                text = ""

            if not text.strip():
                text = "No readable content found."

            # --------------------------------
            # 2️⃣ Generate MCQs using AI
            # --------------------------------
            questions_data = generate_text_questions(text, num_questions=5)

            # --------------------------------
            # 3️⃣ Store Quiz in DB
            # --------------------------------
            quiz = Quiz.objects.create(
                title="AI Generated Quiz",
                questions=questions_data
            )

            return redirect('quiz_detail', quiz_id=quiz.id)

    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})


def quiz_detail(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)

    if request.method == "POST":
        user_name = request.POST.get('user_name', '').strip()
        total = len(quiz.questions)
        score = 0
        details = []   # <-- yaha store karenge har question ka result

        for i, q in enumerate(quiz.questions):
            user_ans = request.POST.get(f"q{i}", "").strip()
            correct_ans = q.get('answer', '').strip()
            is_correct = (user_ans == correct_ans)

            if is_correct:
                score += 1

            details.append({
                "question": q.get("question"),
                "options": q.get("options"),
                "user_answer": user_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "explanation": q.get("explanation", "No explanation")
            })

        QuizResult.objects.create(
            quiz=quiz,
            user_name=user_name,
            score=score,
            total=total
        )

        return render(request, 'quiz_result.html', {
            'score': score,
            'total': total,
            'details': details
        })

    return render(request, 'quiz_detail.html', {'quiz': quiz})


def quiz_history(request):
    history = QuizResult.objects.filter(user=request.user).order_by('-date')
    return render(request, "history.html", {"history": history})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            auth_login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        User.objects.create_user(username=username, password=password)
        return redirect("login")

    return render(request, "register.html")


def user_logout(request):
    auth_logout(request)
    return redirect("home")