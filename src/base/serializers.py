from rest_framework import serializers
from rest_framework.utils import html
from rest_framework.fields import empty

from django.db import models
from django.db.models import query
from django.core.exceptions import ObjectDoesNotExist


class QuerySetSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = data.all() if isinstance(data, (models.Manager, query.QuerySet)) else data

        # The queryset will be modified to add select_related for fields which need a separate query
        # Such fields include:
        # 1. Embeddable ForeignKey fields
        # 2. Reverse foreign keys
        # An inherited serializer can define a `select_related_fields` in the Meta class
        if isinstance(data, query.QuerySet):
            child = self.child
            meta = getattr(child, 'Meta', None)
            embeddable_fields = [fieldname for fieldname, field in child.fields.items() if isinstance(field, ModelSerializer) and field.is_embeddable()]
            select_related_fields = getattr(meta, 'select_related_fields', [])
            select_related_fields = embeddable_fields + list(select_related_fields)
            iterable = iterable.select_related(*select_related_fields)
        return [
            self.child.to_representation(item) for item in iterable
        ]


class ModelSerializer(serializers.ModelSerializer):
    """
    Model serializer which supports optionally embedding the resource in the parent

    - By default, primary key of the resource will be returned.
    - If the `query_params` has an `embed` parameter with this field's name, then
    the resource will be embedded in the response
    """
    def __init__(self, *args, **kwargs):
        # The default for ModelSerializer is to embed the values
        self.always_embed = kwargs.pop("always_embed", True)
        super(ModelSerializer, self).__init__(*args, **kwargs)
        self.error_messages.update({
            'incorrect_type': 'Incorrect type. Expected id value, received {data_type}.',
        })

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        This method implements the creation of a `ListSerializer` parent
        class when `many=True` is used. You can customize it if you need to
        control which keyword arguments are passed to the parent, and
        which are passed to the child.

        Most of this code is based on rest_framework/serializers.py

        """
        child_serializer = cls(*args, **kwargs)
        list_kwargs = {'child': child_serializer}
        list_kwargs.update(dict([
            (key, value) for key, value in kwargs.items()
            if key in serializers.LIST_SERIALIZER_KWARGS
        ]))
        meta = getattr(cls, 'Meta', None)
        list_serializer_class = getattr(meta, 'list_serializer_class', QuerySetSerializer)
        return list_serializer_class(*args, **list_kwargs)

    def is_embeddable(self):
        # If the serializer should always be embedded
        if self.always_embed is True:
            return True

        # Check if the client is requesting to embed the resource
        request = self.context.get('request', None)
        assert request is not None, (
            "`%s` requires the request in the serializer if it is optionally embeddable"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
        )

        embed_fields = request.query_params.getlist("embed")
        return self.field_name in embed_fields

    def get_value(self, dictionary):
        """
        Given the *incoming* primitive data, return the value for this field
        that should be validated and transformed to a native value.
        """
        # If the serializer should always be embedded
        if self.is_embeddable():
            # Client requested to embed this resource
            # Assume the value to be an embedded instance
            return super(ModelSerializer, self).get_value(dictionary)

        # If the resource need not be embedded, then parse the value like a primitive
        if html.is_html_input(dictionary):
            # HTML forms will represent empty fields as '', and cannot
            # represent None or False values directly.
            if self.field_name not in dictionary:
                if getattr(self.root, 'partial', False):
                    return empty
                return self.default_empty_html
            ret = dictionary[self.field_name]
            if ret == '' and self.allow_null:
                # If the field is blank, and null is a valid value then
                # determine if we should use null instead.
                return '' if getattr(self, 'allow_blank', False) else None
            return ret
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if self.is_embeddable():
            # Assume the value to be an embedded instance
            return super(ModelSerializer, self).to_internal_value(data)

        # If the resource need not be embedded, then deserialize the value from a primitive value
        ModelClass = self.Meta.model

        # Assume the value to be a primary key
        try:
            return ModelClass.objects.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, instance):
        if self.is_embeddable():
            # Return the full resource
            return super(ModelSerializer, self).to_representation(instance)

        # If the resource need not be embedded, then serialize the value into a primitive value
        # Return the primary key of the related object
        return instance.pk


class SawaggerResponseSerializer(serializers.Serializer):
   status = serializers.BooleanField(default=True)
   message = serializers.CharField()
   data = serializers.ListField(allow_empty=True)