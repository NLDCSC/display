from flask_restx import fields, Namespace

models = Namespace("Models")

error = models.model(
    "Error",
    {
        "message": fields.String(
            description="Error response message",
            example="Something very descriptive to indicate the error....",
        ),
    },
)
