from django.http.response import JsonResponse
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Bot
import json
from .telebot import Assistant
import random
import string
from django.views.generic import TemplateView


# Create your views here.
class botView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    
    def post(self, request):
        body_json = json.loads(request.body)
        Bot.objects.create(ask=body_json['ask'], session_id=body_json['session_id'])
               

        if body_json['session_id'] == "":

            caracteres = string.ascii_letters + string.digits + string.punctuation
            session_id = 'SessionID:' + ''.join(random.choice(caracteres) for i in range(12))
            assistant = Assistant()            

        else:
            session_id = body_json['session_id']
            asistente_json = cache.get(session_id)
            assistant = Assistant.from_json(asistente_json)
        
        response = assistant.ask_question(body_json['ask'])
        cache.set(session_id, assistant.to_json())

        print (assistant.to_json())

        question = body_json['ask']
        text = "No tengo información para responder esta pregunta ahora, pero si esta relacionado con nuestro servicio, me llevo la pregunta para ampliar mi base de conocimientos."
        if text == response:
            assistant.save_text(question)

        datos = {'author':'bot', 'answer': response, 'session_id': session_id}  # Creamos un nuevo objeto JSON solo con la clave 'ask'
        return JsonResponse(datos)
    

class uploadKbView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    session_id = None
    def get(self, request):
        # aqui llaman al metodo de la carga de la base de conocimiento
        assistant = Assistant()
        assistant.upload_knowledge_base("./api/knowledge-base.txt")

        return HttpResponse("Base de conocimiento cargada con exito")


class deleteKbView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    session_id = None
    def get(self, request):
        # aqui llaman al metodo que borra la base de conocimiento
        assistant = Assistant()
        assistant.delete_knowledge_base()

        return HttpResponse("Base de datos borrada con exito")

class unansweredQuestions(TemplateView):
    template_name = 'readkb.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        with open('./api/questions.txt','r') as file:
            contenido = file.read()
        context['contenido'] = contenido
        return context

class hello(View):
    def get(self, request):
        return HttpResponse("Hello World!")
    
