"""
A very basic, ORM-based backend for simple search during tests.
"""
from django.conf import settings
from django.db.models import Q
from django.utils import simplejson
from haystack.backends import BaseSearchBackend, BaseSearchQuery, SearchNode, log_query
from haystack.models import SearchResult


BACKEND_NAME = 'myisam'

from models import SearchableObject

class SearchBackend(BaseSearchBackend):
    def update(self, index, iterable, commit=True):
        for obj in iterable:
            doc = index.full_prepare(obj)
            
            searchable = SearchableObject.objects.get_or_init(obj)
            searchable.search_text = u' | '.join([unicode(val) for val in doc.itervalues()])
            searchable.save()
    
    def remove(self, obj, commit=True):
        SearchableObject.objects.filter_by_obj(obj).delete()
    
    def clear(self, models=[], commit=True):
        for model in models:
            SearchableObject.objects.filter_by_model(model).delete()
        if not models:
            SearchableObject.objects.all().delete()
    
    @log_query
    def search(self, query_string, sort_by=None, start_offset=0, end_offset=None,
               fields='', highlight=False, facets=None, date_facets=None, query_facets=None,
               narrow_queries=None, spelling_query=None,
               limit_to_registered_models=None, debug=False, **kwargs):
        hits = 0
        results = list()
        
        if query_string:
            query_params = simplejson.loads(query_string)
            for model in self.site.get_indexed_models():
                base_qs = SearchableObject.objects.filter_by_model(model)
                if query_params:
                    search_params = ' '.join(query_params)
                    sub_qs = base_qs & SearchableObject.objects.search(search_params)
                    """
                    sub_qs = SearchableObject.objects.none()
                    for term in query_params:
                        sub_qs |= base_qs.filter(search_text__icontains=term)
                    """
                else:
                    sub_qs = base_qs
                if debug:
                    print model, query_params, sub_qs
                    print sub_qs.query.as_sql()
                
                for match in sub_qs:
                    result = SearchResult(match._meta.app_label, match._meta.module_name, match.pk, 0, **match.__dict__)
                    # For efficiency.
                    result._model = match.__class__
                    result._object = match
                    results.append(result)
        if debug:
            print len(results)
        
        return {
            'results': results,
            'hits': len(results),
        }
    
    def prep_value(self, db_field, value):
        return value
    
    def more_like_this(self, model_instance, additional_query_string=None,
                       start_offset=0, end_offset=None,
                       limit_to_registered_models=None, **kwargs):
        return {
            'results': [],
            'hits': 0
        }


class SearchQuery(BaseSearchQuery):
    def __init__(self, site=None, backend=None):
        super(SearchQuery, self).__init__(backend=backend)
        
        if backend is not None:
            self.backend = backend
        else:
            self.backend = SearchBackend(site=site)
    
    def build_query(self):
        if not self.query_filter:
            return u'[]'
        
        params = self._build_sub_query(self.query_filter)
        return simplejson.dumps(params)
    
    def _build_sub_query(self, search_node):
        term_list = []
        
        for child in search_node.children:
            if isinstance(child, SearchNode):
                term_list.extend(self._build_sub_query(child))
            else:
                term_list.append(child[1])
        
        return term_list

