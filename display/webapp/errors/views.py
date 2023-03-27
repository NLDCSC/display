from flask import render_template

from . import errors


@errors.route("/50x")
def user_home():
    return (
        render_template(
            "errors/500.html",
            header="Internal Server Error",
            authenticated=False,
            error=True,
        ),
        500,
    )
