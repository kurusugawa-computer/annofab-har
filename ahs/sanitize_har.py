import argparse
import json
from argparse import Namespace
from collections.abc import Collection
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

STR_REDACTED = "REDACTED"
"""編集済を表す文字列"""

SENSITIVE_QUERY_STRING_KEYS = {"X-Amz-Credential", "X-Amz-Signature", "X-Amz-Security-Token"}

SENSITIVE_REQUEST_HEADER_KEYS = {"authorization", "cookie"}
"""
マスク対象のリクエストヘッダのキー

Notes:
    小文字で比較するため、小文字で定義すること。
"""


SENSITIVE_RESPONSE_HEADER_KEYS = {"set-cookie"}
"""
マスク対象のリクエストヘッダのキー

Notes:
    小文字で比較するため、小文字で定義すること。
"""


def mask_query_string_in_url(url: str, masked_keys: Collection[str]) -> str:
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

    headers = response["headers"]
    for header in headers:
        if header["name"].lower() in SENSITIVE_RESPONSE_HEADER_KEYS:
            header["value"] = STR_REDACTED

    return response


def sanitize_initiator(initiator: dict[str, Any]) -> dict[str, Any]:
    """
    キー`url`に対応する値をマスクする。
    "_initiator"は標準仕様にはないので、再帰的にアクセスして処理する。

    """
    for key, value in initiator.items():
        if isinstance(value, dict):
            initiator[key] = sanitize_initiator(value)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    value[index] = sanitize_initiator(item)
        elif isinstance(value, str):
            if key == "url":
                initiator[key] = mask_query_string_in_url(initiator["url"], SENSITIVE_QUERY_STRING_KEYS)

    return initiator


def sanitize_url(url: str) -> str:
    """
    URLのQuery Stringに含まれるセンシティブな値をマスクする
    """
    return mask_query_string_in_url(url, SENSITIVE_QUERY_STRING_KEYS)


def sanitize_request(request: dict[str, Any]) -> dict[str, Any]:
    if "postData" in request:
        request["postData"]["text"] = STR_REDACTED
    request["cookies"] = []
    headers = request["headers"]

    for header in headers:
        if header["name"].lower() in SENSITIVE_REQUEST_HEADER_KEYS:
            header["value"] = STR_REDACTED

    query_string_list = request["queryString"]
    for qs in query_string_list:
        if qs["name"] in SENSITIVE_QUERY_STRING_KEYS:
            qs["value"] = STR_REDACTED

    request["url"] = sanitize_url(request["url"])
    return request


def sanitize_har_object(data: dict[str, Any]) -> dict[str, Any]:
    for entry in data["log"]["entries"]:
        if "_initiator" in entry:
            entry["_initiator"] = sanitize_initiator(entry["_initiator"])
        entry["request"] = sanitize_request(entry["request"])
        entry["response"] = sanitize_response(entry["response"])
    return data


def main(args: Namespace) -> None:
    input_data = json.loads(args.har_file.read_text(encoding="utf-8"))
    output_data = sanitize_har_object(input_data)
    output_string = json.dumps(output_data, ensure_ascii=False)
    if args.output is not None:
        output_file: Path = args.output
        output_file.parent.mkdir(exist_ok=True, parents=True)
        output_file.write_text(output_string, encoding="utf-8")
    else:
        print(output_string)  # noqa: T201


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    subcommand_name = "sanitize"
    subcommand_help = "AnnofabのHARファイルから機密情報をマスクします。"

    parser = subparsers.add_parser(subcommand_name, description=subcommand_help, help=subcommand_help)
    parser.set_defaults(func=main)

    parser.add_argument("har_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。")

    return parser
