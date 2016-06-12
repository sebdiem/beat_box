from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Suggestion(models.Model):
    SUGGESTION_STATES = [
        ('open', _('open')),
        ('closed', _('closed')),
    ]

    title = models.TextField(null=False, verbose_name=_('title'))
    description = models.TextField(null=False, verbose_name=_('description'))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='suggestions', null=False,
        verbose_name=_('author'))
    created_at = models.DateTimeField(default=timezone.now, null=False, verbose_name=_('created at'), db_index=True)
    state = models.TextField(null=False, default=SUGGESTION_STATES[0][0], choices=SUGGESTION_STATES,
        verbose_name=_('state'))
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Like', related_name='liked_suggestions',
        verbose_name=_('likes'))


class Like(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    suggestion = models.ForeignKey(Suggestion)

    class Meta:
        unique_together = ('author', 'suggestion')
