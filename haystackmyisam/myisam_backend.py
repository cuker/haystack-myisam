"""

"""
from django.utils.datastructures import MultiValueDict
from haystack.backends import BaseSearchBackend, BaseSearchQuery, SearchNode, log_query
from haystack.models import SearchResult


BACKEND_NAME = 'myisam'

from models import SearchableObject

class SearchBackend(BaseSearchBackend):
    def update(self, index, iterable, commit=True):
        for obj in iterable:
            doc = index.full_prepare(obj)
            searchable = SearchableObject.objects.get_or_init(obj)
            searchable_parts = list()
            
            if hasattr(index, 'content_fields'):
                for content_field in index.content_fields:
                    if doc.get(content_field, False):
                        searchable_parts.append(unicode(doc[content_field]))
            else:
                searchable_parts.append(unicode(doc.get(index.get_content_field(), '')))
                
            searchable.search_text = u' | '.join(searchable_parts)
            searchable.document = doc
            searchable.save()
            searchable.populate_index(index)
    
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
        
        #build search criteria
        qs = SearchableObject.objects.all()
        extras = MultiValueDict()
        
        if limit_to_registered_models is not None:
            qs = qs.filter(content_type__in=limit_to_registered_models)
        
        for key, value_list in query_string.iterlists():
            if key == 'content':
                search_params = ' '.join(query_string.getlist('content'))
                qs &= SearchableObject.objects.search(search_params)
            else:
                #TODO support multi value search
                extras.appendlist('where','''
                    (SELECT COUNT(*) FROM haystackmyisam_searchableindex AS searchindex 
                     WHERE searchindex.searchable_object_id="haystackmyisam_searchableobject"."id" 
                       AND searchindex."key"=%s AND searchindex."value"=%s) > 0
                    ''')
                extras.appendlist('params', key)
                extras.appendlist('params', str(value_list[0]))
        
        if extras:
            qs = qs.extra(**extras)
        
        qs = qs.distinct() #may or may not work....
        
        for match in qs: #TODO this part should be lazy
            obj = match.content_object
            result = SearchResult(obj._meta.app_label, obj._meta.module_name, obj.pk, 0, **match.document)
            # For efficiency.
            result._model = obj.__class__
            result._object = obj
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
            return MultiValueDict()
        
        params = self._build_sub_query(self.query_filter)
        return params
    
    def _build_sub_query(self, search_node):
        terms = MultiValueDict()
        
        for child in search_node.children:
            if isinstance(child, SearchNode):
                terms.update(self._build_sub_query(child))
            else:
                terms.appendlist(child[0], child[1])
        
        return terms

