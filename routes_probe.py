import os, hashlib, base64, json
from flask import current_app as app, Blueprint, request, session, redirect, url_for, make_response, jsonify
from werkzeug.exceptions import HTTPException

probe = Blueprint("probe", __name__)

def _fp(key):
    return base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest()).decode()[:16]

@probe.get("/diag/env")
def diag_env():
    cfg = app.config
    return jsonify({
        "host": request.host,
        "scheme_hdr": request.headers.get("X-Forwarded-Proto"),
        "url_root": request.url_root,
        "secret_fp": _fp(cfg["SECRET_KEY"]),
        "cookie_cfg": {
            "name": cfg.get("SESSION_COOKIE_NAME"),
            "secure": cfg.get("SESSION_COOKIE_SECURE"),
            "samesite": cfg.get("SESSION_COOKIE_SAMESITE"),
            "domain": cfg.get("SESSION_COOKIE_DOMAIN"),
        },
        "iframe_preview_warning": "If this app is in an iframe, SameSite must be 'None' + Secure=True."
    })

@probe.route("/diag/cookie-write")
def diag_cookie_write():
    resp = make_response(jsonify({
        "set_cookie": True,
        "received_cookie": request.cookies.get("cookie_diag"),
        "host": request.host
    }))
    # Auto-detect secure setting based on request scheme
    is_https = request.headers.get("X-Forwarded-Proto") == "https" or request.scheme == "https"
    resp.set_cookie("cookie_diag", "hello", httponly=True, secure=is_https, samesite="Lax")
    return resp

@probe.route("/diag/cookie-read")
def diag_cookie_read():
    return jsonify({"cookie_diag": request.cookies.get("cookie_diag")})

@probe.route("/diag/login-post-echo", methods=["POST"])
def diag_login_post_echo():
    # Do NOT return the password in logs; return metadata only.
    form_keys = list(request.form.keys())
    return jsonify({
        "method": request.method,
        "action_url": request.url,
        "referrer": request.referrer,
        "form_keys": form_keys,
        "has_csrf": "csrf_token" in form_keys or "csrfmiddlewaretoken" in form_keys
    })

@probe.get("/diag/whoami-verbose")
def diag_whoami_verbose():
    return jsonify({
        "is_authenticated": session.get('user_id') is not None,
        "user_id": session.get('user_id'),
        "session_keys": list(session.keys()),
        "headers": {
            "Host": request.host,
            "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto"),
            "Cookie": "present" if request.headers.get("Cookie") else "missing"
        }
    })

# Last resort: force a server-side session to bypass cookie-size and client-session issues
@probe.get("/diag/force-server-side-session")
def diag_force_server_side():
    enabled = bool(app.config.get("SESSION_TYPE"))
    return jsonify({"server_side_session_enabled": enabled})

# Production deployment readiness check
@probe.get("/diag/deployment-check")
def deployment_check():
    is_https = request.headers.get("X-Forwarded-Proto") == "https" or request.scheme == "https"
    is_replit_domain = ".replit.app" in request.host or "replit.dev" in request.host
    
    return jsonify({
        "request_scheme": request.scheme,
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "host": request.host,
        "is_https": is_https,
        "is_replit_domain": is_replit_domain,
        "should_use_secure_cookies": is_https and is_replit_domain,
        "current_cookie_secure": app.config.get("SESSION_COOKIE_SECURE"),
        "ready_for_production": is_https and is_replit_domain
    })