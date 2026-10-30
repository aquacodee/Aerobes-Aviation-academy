from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import AdminUser
from ..extensions import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    email = (d.get("email") or "").lower().strip()
    user = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not user or not bcrypt.check_password_hash(
        user.password_hash, d.get("password", "")
    ):
        return (
            jsonify(
                {
                    "error": {
                        "code": "invalid_credentials",
                        "message": "Email or password is incorrect.",
                    }
                }
            ),
            401,
        )
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.full_name},
    )
    return jsonify(
        {
            "data": {
                "access_token": token,
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                },
            }
        }
    )


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # Stateless access tokens expire; client must discard its token.
    return jsonify({"message": "Logged out. Discard the access token on this device."})


@auth_bp.get("/me")
@jwt_required()
def me():
    from flask_jwt_extended import get_jwt

    u = AdminUser.query.get(int(get_jwt_identity()))
    if not u:
        return jsonify({"error": {"message": "Account not found"}}), 404
    return jsonify(
        {
            "data": {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
            }
        }
    )
