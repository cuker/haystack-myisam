import os
from settings import *

INSTALLED_APPS += [
    'myisam_tests',
    'haystackmyisam',
]

HAYSTACK_SEARCH_ENGINE = 'haystackmyisam.myisam'

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'haystack_test'
DATABASE_USER = 'root'
