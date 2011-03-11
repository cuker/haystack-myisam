from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

class SearchableObjectManager(models.Manager):
    def filter_by_model(self, model):
        content_type = ContentType.objects.get_for_model(model)
        return self.filter(content_type=content_type)

    def filter_by_obj(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        return self.filter(content_type=content_type, object_id=object_id)
    
    def get_or_init(self, obj):
        try:
            searchable = self.filter_by_obj(obj).get()
        except self.model.DoesNotExist:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.pk
            searchable = self.model(content_type=content_type, object_id=object_id)
        return searchable

class SearchableObject(models.Model):
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    search_text    = models.TextField() #fulltext
    
    objects = SearchableObjectManager()
    
    def __unicode__(self):
        return u"Searchable Content for %s-%s" % (self.content_type.name, self.content_object)

