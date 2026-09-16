from django.contrib import admin

from fatwas.models import Answer, AnswerRevision, AuditEvent, Bookmark, Category, Methodology, Publication, Report, ReviewDecision

for model in (Category, Methodology, Answer, AnswerRevision, ReviewDecision, Publication, Bookmark, Report, AuditEvent):
    admin.site.register(model)
