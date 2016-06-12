import copy

from rest_framework import pagination
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Case, Count, Value, When
from django.utils import timezone

from . import models


class _AuthorField(serializers.Serializer):
    """A simple representation of an author."""
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class _UserReadOnly(serializers.BooleanField):
    """Whether the user can edit the object or not."""
    def to_representation(self, obj):
        return not can_edit(self.context['request'].user, obj)


class Suggestion(serializers.ModelSerializer):
    """The suggestion serializer used for reading/writing suggestions from/to the database."""

    # Read-only fields
    url = serializers.HyperlinkedIdentityField(view_name='api:suggestion-detail', lookup_field='pk', read_only=True)
    uid = serializers.CharField(source='id', read_only=True)
    author = _AuthorField(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    liked = serializers.BooleanField(read_only=True)
    read_only = _UserReadOnly(source='*', read_only=True)

    # Editable fields
    title = serializers.CharField(read_only=False)
    description = serializers.CharField(read_only=False)
    created_at = serializers.DateTimeField(read_only=False, default=timezone.now)
    state = serializers.ChoiceField(
        read_only=False,
        choices=models.Suggestion.SUGGESTION_STATES,
        default=models.Suggestion.SUGGESTION_STATES[0][0],
    )

    class Meta:
        model = models.Suggestion

    def get_fields(self):
        # I don't like the magic that happens with model serializer.
        # I prefer an explicit declaration of fields, even though it duplicates a few fields.
        # TODO: create a base class ExplicitModelSerializer with less magic than the default serializer.
        return copy.deepcopy(self._declared_fields)


def make_read_only(serializer, new_class_name):
    """Return a new serializer class based on ``serializer`` but with all fields read-only."""
    fields = {}
    for k, v in serializer._declared_fields.items():
        args = v._args
        kwargs = v._kwargs
        kwargs['read_only'] = True
        fields[k] = v.__class__(*args, **kwargs)
    fields['Meta'] = type('Meta', (serializer.Meta,), {})

    return type(new_class_name, (serializer,), fields)


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    """
    Object-level permission to only allow the owner of an object to edit it.
    Assumes the model instance has an `author_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        view = request.parser_context.get('view')
        if view and view.action in ('like', 'unlike'):
            return True

        return can_edit(request.user, obj)


class SuggestionPagination(pagination.CursorPagination):
    """Default pagination."""
    ordering = '-created_at'
    page_size = 100


class SuggestionViewSet(viewsets.ModelViewSet):
    """
    A viewset for the Suggestion resource.

    Available endpoints:
        list: list, create
        detail: retrieve, update, delete, like, unlike
    """
    serializer_class = Suggestion
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = SuggestionPagination
    lookup_field = 'pk'
    #template_name = 'beat_box/suggestions.html'

    def get_queryset(self):
        return (models.Suggestion.objects
            .select_related('author')
            .annotate(likes=Count('liked_by'))
            .annotate(liked=Case(
                When(liked_by=self.request.user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ))
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        # empty override to show explicitly that update is available on the viewset
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # empty override to show explicitly that destroy is available on the viewset
        super().perform_destroy(instance)

    @detail_route(methods=['post'])
    def like(self, request, pk):
        suggestion = self.get_object()
        try:
            models.Like.objects.create(suggestion=suggestion, author=request.user)
            # update instance directly without querying the db once again
            suggestion.likes += 1
            suggestion.liked = True
        except Exception as e:
            print(e)
        return Response(self.get_serializer(suggestion).data)

    @detail_route(methods=['post'])
    def unlike(self, request, pk):
        suggestion = self.get_object()
        try:
            models.Like.objects.get(suggestion=suggestion, author=request.user).delete()
            # update instance directly without querying the db once again
            suggestion.likes -= 1
            suggestion.liked = False
        except Exception as e:
            print(e)
        return Response(self.get_serializer(suggestion).data)


def can_edit(user, obj):
    return user.id == obj.author_id
