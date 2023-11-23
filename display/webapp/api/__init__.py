from flask import Blueprint
from flask_restx import Api

from set_version import VERSION
from .models.general import models as gen_models
from .models.screenshots import models as scr_models
from .screenshots import api as screenshots_api

namespaces = [screenshots_api]

models = [gen_models, scr_models]

api_bp = Blueprint("api", __name__)

authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "Access-Token"}}

api = Api(
    api_bp,
    version=VERSION,
    title="Display",
    description="API documentation for Display server",
    authorizations=authorizations,
    security="apikey",
)

for each in namespaces:
    api.add_namespace(each)

for each in models:
    api.add_namespace(each)
