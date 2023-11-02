from django.urls import path
from .views import botView, uploadKbView, deleteKbView, unansweredQuestions, hello

urlpatterns = [
    path('bot/', botView.as_view()),
    path('upload-kb/', uploadKbView.as_view()),
    path('delete-kb/', deleteKbView.as_view()),
    path('unanswered-questions/', unansweredQuestions.as_view()),     
    path('hello/', hello.as_view()),     
]
