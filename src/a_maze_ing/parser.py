import sys
import os
from enum import Enum
try:
    from pydantic import BaseModel, Field, ValidationError
except ImportError:
    print("------>      pip install pydantic")