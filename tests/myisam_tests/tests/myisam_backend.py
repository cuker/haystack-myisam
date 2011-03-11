from datetime import date
from django.test import TestCase
from haystack import indexes, sites, backends
from haystackmyisam.myisam_backend import SearchBackend
from haystackmyisam.models import SearchableObject
from haystack.sites import SearchSite
from core.models import MockModel


class SimpleMockSearchIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='author')
    pub_date = indexes.DateField(model_attr='pub_date')
    foo = indexes.CharField(model_attr='foo')


class SimpleSearchBackendTestCase(TestCase):
    fixtures = ['bulk_data.json']
    
    def setUp(self):
        super(SimpleSearchBackendTestCase, self).setUp()
        
        self.site = SearchSite()
        self.backend = SearchBackend(site=self.site)
        self.index = SimpleMockSearchIndex(MockModel, backend=self.backend)
        self.site.register(MockModel, SimpleMockSearchIndex)
        
        self.sample_objs = MockModel.objects.all()
        self.backend.update(self.index, self.sample_objs)
    
    def test_update(self):
        self.backend.update(self.index, self.sample_objs)
        self.assertEqual(len(self.sample_objs), SearchableObject.objects.count())
    
    def test_remove(self):
        self.backend.remove(self.sample_objs[0])
        self.assertEqual(len(self.sample_objs)-1, SearchableObject.objects.count())
    
    def test_clear(self):
        self.backend.clear()
        self.assertEqual(0, SearchableObject.objects.count())
    
    def test_search(self):
        # No query string should always yield zero results.
        self.assertEqual(self.backend.search(u''), {'hits': 0, 'results': []})
        
        search_results = self.backend.search(u'[]')
        self.assertEqual(search_results['hits'], 23)
        self.assertEqual([result.pk for result in search_results['results']], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
        
        search_results = self.backend.search(u'["daniel"]')
        #print SearchableObject.objects.filter(search_text__icontains='daniel')
        self.assertEqual(search_results['hits'], 23)
        self.assertEqual([result.pk for result in search_results['results']], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
        
        search_results = self.backend.search(u'["should be a string"]')
        self.assertEqual(search_results['hits'], 1)
        self.assertEqual([result.pk for result in search_results['results']], [8])
        # Ensure the results are ``SearchResult`` instances...
        self.assertEqual(search_results['results'][0].score, 0)
        '''
        #Ands are not supported currently
        search_results = self.backend.search(u'[["index", "document"]]', debug=True)
        self.assertEqual(search_results['hits'], 6)
        self.assertEqual([result.pk for result in search_results['results']], [2, 3, 15, 16, 17, 18])
        
        # Regression-ville
        self.assertEqual([result.object.id for result in search_results['results']], [2, 3, 15, 16, 17, 18])
        self.assertEqual(search_results['results'][0].model, MockModel)
        '''
        # No support for spelling suggestions
        self.assertEqual(self.backend.search(u'["Indx"]')['hits'], 0)
        self.assertFalse(self.backend.search(u'["Indx"]').get('spelling_suggestion'))
        
        # No support for facets
        self.assertEqual(self.backend.search(u'', facets=['name']), {'hits': 0, 'results': []})
        self.assertEqual(self.backend.search(u'["daniel"]', facets=['name'])['hits'], 23)
        self.assertEqual(self.backend.search(u'', date_facets={'pub_date': {'start_date': date(2008, 2, 26), 'end_date': date(2008, 2, 26), 'gap': '/MONTH'}}), {'hits': 0, 'results': []})
        self.assertEqual(self.backend.search(u'["daniel"]', date_facets={'pub_date': {'start_date': date(2008, 2, 26), 'end_date': date(2008, 2, 26), 'gap': '/MONTH'}})['hits'], 23)
        self.assertEqual(self.backend.search(u'', query_facets={'name': '[* TO e]'}), {'hits': 0, 'results': []})
        self.assertEqual(self.backend.search(u'["daniel"]', query_facets={'name': '[* TO e]'})['hits'], 23)
        self.assertFalse(self.backend.search(u'').get('facets'))
        self.assertFalse(self.backend.search(u'["daniel"]').get('facets'))
        
        # Contextual fields are lumped in
        self.assertEqual(self.backend.search(u'["2009-06-18"]')['hits'], 2)
        
    def test_more_like_this(self):
        self.assertEqual(self.backend.search(u'[]')['hits'], 23)
        
        # Unsupported by 'dummy'. Should see empty results.
        self.assertEqual(self.backend.more_like_this(self.sample_objs[0])['hits'], 0)
