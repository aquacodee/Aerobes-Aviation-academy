from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify


def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "forbidden",
                                "message": "Insufficient permissions",
                            }
                        }
                    ),
                    403,
                )
            return fn(*args, **kwargs)

        return wrapper

    return deco
