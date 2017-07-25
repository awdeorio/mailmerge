"""
Mail merge module importable API.

Andrew DeOrio <awdeorio@umich.edu>
"""

from .api import main
from .api import TEMPLATE_FILENAME_DEFAULT
from .api import DATABASE_FILENAME_DEFAULT
from .api import CONFIG_FILENAME_DEFAULT
from .smtp_dummy import SMTP_dummy
