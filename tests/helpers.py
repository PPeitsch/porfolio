import datetime

import jwt


def generate_test_token(app):
    """
    Helper function to generate a valid JWT for tests.
    This token can be used to bypass the @token_required decorator.
    """
    payload = {
        "sub": "test_access",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=15),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
