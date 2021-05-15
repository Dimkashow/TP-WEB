from django.contrib import admin
from app.models import Question, Tag, Answer, Like, Profile

# Register your models here.
admin.site.register(Tag)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Profile)
admin.site.register(Like)
