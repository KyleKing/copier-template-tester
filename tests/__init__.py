import sys
from os import environ, getenv

DEF_MODE = 'ERROR' if sys.version_info >= (3, 9) else 'WARNING'
environ['RUNTIME_TYPE_CHECKING_MODE'] = getenv('RUNTIME_TYPE_CHECKING_MODE', DEF_MODE)
