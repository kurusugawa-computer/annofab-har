import json
import argparse
from pathlib import Path

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Any
from collections.abc import Collection

STR_REDACTED = "REDACTED"
"""編集済を表す文字列"""


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AnnofabからエクスポートしたHAR(Http Archive)ファイルから個人情報をマスクします。"
    )

    parser.add_argument("har_file", type=Path)
    parser.add_argument(
        "-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。"
    )
    return parser


def mask_query_string(url: str, masked_keys: Collection[str]) -> str:
    """
    URLのQuery Stringに含まれるセンシティブな値をマスクする

    """
    # Parse the URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Mask the sensitive keys
    for key in masked_keys:
        if key in query_params:
            query_params[key] = [STR_REDACTED] * len(query_params[key])

    # Reconstruct the query string and URL
    masked_query = urlencode(query_params, doseq=True)
    masked_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            masked_query,
            parsed_url.fragment,
        )
    )
    return masked_url


def sanitize_response(response: dict[str, Any]) -> dict[str, Any]:
    response["content"]["text"] = STR_REDACTED
    response["cookies"] = []
    return response


def sanitize_request(request: dict[str, Any]) -> dict[str, Any]:
    if "postData" in request:
        request["postData"]["text"] = STR_REDACTED
    request["cookies"] = []
    headers = request["headers"]

    for header in headers:
        if header["name"] == "Authorization":
            header["value"] = STR_REDACTED

    sensitive_keys = {"X-Amz-Credential", "X-Amz-Signature", "X-Amz-Security-Token"}
    query_string_list = request["queryString"]
    for qs in query_string_list:
        if qs["name"] in sensitive_keys:
            qs["value"] = STR_REDACTED

    url = request["url"]
    request["url"] = mask_query_string(url, sensitive_keys)
    return request


def sanitize_har_object(data: dict[str, Any]) -> dict[str, Any]:
    for entry in data["log"]["entries"]:
        entry["request"] = sanitize_request(entry["request"])
        entry["response"] = sanitize_response(entry["response"])
    return data


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    input_data = json.loads(args.har_file.read_text())
    output_data = sanitize_har_object(input_data)

    if args.output is not None:
        output_file:Path = args.output
        output_file.parent.mkdir(exist_ok=True, parents=True)
        output_file.write_text(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()
