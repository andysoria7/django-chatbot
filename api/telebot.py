import os
import openai
import redis
import json
import numpy as np
from typing import List, Tuple
from django.conf import settings
from django.http import HttpResponse

class Message:    
    def __init__(self,role,content):        
        self.role = role
        self.content = content        
    def message(self):        
        return {"role": self.role,"content": self.content}

class Assistant:
    def __init__(self):
        self.r = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB, 
            password=settings.REDIS_PASSWORD, 
            ssl=settings.REDIS_SSL)
        self.history = [["",""], ["",""], ["",""], ["",""], ["",""]]

    def encode_text(self, text: str) -> np.ndarray:
        response = openai.Embedding.create(engine="text-embedding-ada-002", input=[text])
        return np.array(response['data'][0]['embedding'])

    def upload_knowledge_base(self, file_path: str):
        with open(file_path, encoding="utf8") as f:
            paragraphs = f.read().split(';\n')

        for i, paragraph in enumerate(paragraphs):
            key = f"paragraph:{i}"
            key2 = f"{key}:embedding"
            vector = self.encode_text(paragraph)

            self.r.set(name=key, value=paragraph) 
            self.r.set(name=key2, value=vector.tobytes())
            print ("Saving: " + paragraph + "\n")
            
    def delete_knowledge_base(self):
        self.r.flushdb()

    def find_similar_texts(self, query: str, top_k: int = 7) -> List[Tuple[str, float]]:
        query_vector = self.encode_text(query)
        similarities = []

        for key in self.r.scan_iter("paragraph:*:embedding"):
            paragraph_key = key.decode("utf-8").replace(":embedding", "")
            paragraph = self.r.get(paragraph_key).decode("utf-8")
            embedding = np.frombuffer(self.r.get(key))

            similarity = np.dot(query_vector, embedding) / (np.linalg.norm(query_vector) * np.linalg.norm(embedding))
            similarities.append((paragraph, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_assistant_response(self, prompt, question):
        completion = openai.ChatCompletion.create(
            model = settings.OPENAI_MODEL,
            temperature=0.1, 
            top_p=0.1,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": self.history[0][0]},
                {"role": "assistant", "content": self.history[0][1]},
                {"role": "user", "content": self.history[1][0]},
                {"role": "assistant", "content": self.history[1][1]},
                {"role": "user", "content": self.history[2][0]},
                {"role": "assistant", "content": self.history[2][1]},
                {"role": "user", "content": self.history[3][0]},
                {"role": "assistant", "content": self.history[3][1]},
                {"role": "user", "content": self.history[4][0]},
                {"role": "assistant", "content": self.history[4][1]},
                {"role": "user", "content": question}
            ]
        )

        response_message = Message(completion['choices'][0]['message']['role'],completion['choices'][0]['message']['content'])
        return response_message.content.strip()

    def add_item_to_history(self, question, response): 
        self.history[0] = self.history[1]
        self.history[1] = self.history[2]
        self.history[2] = self.history[3]
        self.history[3] = self.history[4]
        self.history[4] = [question, response]

    def ask_question(self, question):
        similar_texts = self.find_similar_texts(question)

        knowledge_base = ""
        separator = ""
        for text in similar_texts:
            knowledge_base += f"{separator}{text[0]}"
            separator = "\n"

        with open("./api/prompt-template.txt", encoding="utf8") as f:
            template = f.read()

        prompt = template.replace("[KNOWLEDGE_BASE]", knowledge_base)

        response = self.get_assistant_response(prompt, question)

        self.add_item_to_history(question, response)

        return response
    
    def to_json(self):
        return json.dumps(self.history)


    @classmethod
    def from_json(cls, data):
        instance = cls()
        instance.history = json.loads(data)
        return instance
    
    def save_text(self, request):
        route_doc = os.path.join(os.path.dirname(__file__), 'questions.txt')

        with open(route_doc, 'a') as archivo:
            archivo.write(request + '\n')
    
        return HttpResponse("Request ", request)

