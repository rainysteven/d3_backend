import base64


def base64_decode(origin_str):
    origin_str += "=" * (3 - len(origin_str) % 3)
    origin_str = bytes(origin_str, encoding='utf8')
    res = base64.b64decode(origin_str).decode()
    return res
