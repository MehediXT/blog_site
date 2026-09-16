from django.contrib import admin

from questions.models import ClarificationMessage, Question

admin.site.register(Question)
admin.site.register(ClarificationMessage)
