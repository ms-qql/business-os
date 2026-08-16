from app import security


def test_password_hash_and_verify():
    h = security.hash_password("geheim-12345")
    assert security.verify_password("geheim-12345", h)
    assert not security.verify_password("falsch", h)
    assert not security.verify_password("x", None)


def test_jwt_roundtrip_business():
    tok = security.make_token("sess-1", "business", {"role": "Inhaber"})
    claims = security.decode_token(tok, "business")
    assert claims["sub"] == "sess-1"
    assert claims["aud"] == "business"


def test_jwt_audience_mismatch_rejected():
    tok = security.make_token("sess-1", "business")
    import jwt
    try:
        security.decode_token(tok, "operator")
    except jwt.exceptions.InvalidAudienceError:
        return
    raise AssertionError("erwartete InvalidAudienceError")
