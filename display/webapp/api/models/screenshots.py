from flask_restx import fields, Namespace

models = Namespace("Screenshot Models")

screenshot_url = models.model(
    "screenshot_url",
    {
        "URL": fields.String(
            description="Requested URL", example="https://av.baf.27.berylia.org"
        )
    },
)

screenshot_data = models.inherit(
    "screenshot_data",
    screenshot_url,
    {
        "DATA": fields.String(
            description="Base64 encoded byte string representing the requested screenshot/evidence shot",
            example="iVBORw0KGgoAAAANSUhEUgAABAAAAAMACAYAAAC6uhUNAADtVklEQVR4nOzdd5wcd33....",
        )
    },
)

screenshot_create_data = models.inherit(
    "screenshot_create_data",
    screenshot_url,
    {
        "DATA": fields.String(
            description="Response message after submitting a request for a new screenshot",
            example="Create new screenshot submitted",
        )
    },
)

screenshot_request = models.model(
    "screenshot_request",
    {
        "display-url": fields.String(
            description="Requested URL", example="https://av.baf.27.berylia.org"
        ),
    },
)
