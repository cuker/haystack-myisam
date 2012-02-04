from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder

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
    
    def search(self, query):
        max_term_size = max([len(term) for term in query.split()])
        #mysql fulltext search does not support search terms of a size 3 or less
        #TODO handle routing
        if 'mysql' in settings.DATABASES['default']['ENGINE'] and max_term_size > 3:
            return self.extra(
                select={'relevance': 'MATCH(search_text) AGAINST (%s IN NATURAL LANGUAGE MODE)'},
                select_params=[query],
                where=['MATCH(search_text) AGAINST (%s IN NATURAL LANGUAGE MODE)'],
                params=[query],
                order_by=['-relevance']
            )
        else:
            return self.filter(search_text__icontains=query)

class SearchableObject(models.Model):
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    search_text    = models.TextField() #fulltext
    _document = models.TextField(db_column='document')
    
    def get_document(self):
        if self._document:
            #return DjangoJSONEncoder().decode(self._document)
            return json.loads(self._document)
        else:
            return {}
    
    def set_document(self, data):
        self._document = DjangoJSONEncoder().encode(data)
        #self._document = json.dumps(data)
    
    document = property(get_document, set_document)
    
    objects = SearchableObjectManager()
    
    def __unicode__(self):
        return u"Searchable Object for %s-%s" % (self.content_type.name, self.content_object)
    
    class Meta:
        unique_together = [('content_type', 'object_id')]
    
    def populate_index(self, search_index):
        self.index.all().delete()
        for key, value in self.document.iteritems():
            if key in search_index.fields:
                field = search_index.fields[key]
                if not field.document and field.indexed:
                    if isinstance(value, list):
                        for val in value:
                            self.index.create(searchable_object=self, key=key, value=val)
                    else:
                        self.index.create(searchable_object=self, key=key, value=value)

class SearchableIndex(models.Model):
    searchable_object = models.ForeignKey(SearchableObject, related_name='index')
    key = models.CharField(max_length=32, db_index=True)
    value = models.CharField(max_length=255, db_index=True)

