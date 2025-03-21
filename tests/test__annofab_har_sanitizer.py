from ahs.sanitize_har import sanitize_initiator


def test__sanitize_initiator():
    initiator = {"type": "parser", "url": "https://example.com/foo?X-Amz-Credential=123", "lineNumber": 6}

    actual = sanitize_initiator(initiator)
    assert actual["url"] == "https://example.com/foo?X-Amz-Credential=REDACTED"


def test__sanitize_initiator2():
    initiator = {
        "type": "script",
        "stack": {
            "callFrames": [
                {"functionName": "", "scriptId": "216", "url": "https://example.com/foo?X-Amz-Credential=123", "lineNumber": 25, "columnNumber": 23}
            ]
        },
    }

    actual = sanitize_initiator(initiator)
    assert actual["stack"]["callFrames"][0]["url"] == "https://example.com/foo?X-Amz-Credential=REDACTED"
