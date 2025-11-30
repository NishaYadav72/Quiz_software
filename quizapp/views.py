from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import Quiz, QuizResult
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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

    # ⭐ STORE QUIZ IN SESSION (for PDF download)
    request.session["quiz_data"] = quiz.questions
    request.session["quiz_title"] = quiz.title

    if request.method == "POST":
        user_name = request.POST.get('user_name', '').strip()
        total = len(quiz.questions)
        score = 0
        details = []

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

        # ⭐ STORE RESULT IN SESSION (for PDF)
        request.session["result_details"] = details
        request.session["score"] = score
        request.session["total"] = total
        request.session["user_name"] = user_name

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

def download_quiz_details_pdf(request):
    quiz_data = request.session.get("quiz_data")

    if not quiz_data:
        return HttpResponse("No quiz data found.")

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="quiz.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Quiz Questions")
    y -= 40

    for i, q in enumerate(quiz_data, start=1):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"Q{i}. {q['question']}")
        y -= 20

        p.setFont("Helvetica", 11)
        for opt in q["options"]:
            p.drawString(70, y, f"- {opt}")
            y -= 15

        y -= 10

        if y < 80:
            p.showPage()
            y = height - 50

    p.save()
    return response


def download_quiz_pdf(request):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from django.http import HttpResponse

    quiz_title = request.session.get("quiz_title")
    quiz_data = request.session.get("quiz_data")
    result_details = request.session.get("result_details")
    user_name = request.session.get("user_name")
    score = request.session.get("score")
    total = request.session.get("total")

    if not quiz_data:
        return HttpResponse("No quiz data found in session.")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="quiz_result.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"<b>{quiz_title}</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    # User and Score
    story.append(Paragraph(f"Name: {user_name}", styles["Normal"]))
    story.append(Paragraph(f"Score: {score} / {total}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Loop through QUESTION + RESULT
    for q in result_details:
        story.append(Paragraph(f"<b>Q: {q['question']}</b>", styles["Heading4"]))

        # Options
        for opt in q["options"]:
            story.append(Paragraph(f"• {opt}", styles["Normal"]))

        story.append(Paragraph(f"<b>Your Answer:</b> {q['user_answer']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Correct Answer:</b> {q['correct_answer']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Explanation:</b> {q['explanation']}", styles["Normal"]))
        story.append(Spacer(1, 15))

    doc.build(story)
    return response
