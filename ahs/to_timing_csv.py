import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas

from ahs.sanitize_har import sanitize_url


def _minimize_request(request: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key in ("method", "url"):
        result[key] = request[key]
    return result


def get_content_length(headers: list[dict[str, Any]]) -> int | None:
    for header in headers:
        if header["name"].lower() == "content-length":
            return int(header["value"])
    return None


def _minimize_response(response: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key in ("status",):
        result[key] = response[key]

    content = response["content"]
    result["content"] = {
        "size": content["size"],
        "mimeType": content["mimeType"],
    }
    result["headers"] = {"contentLength": get_content_length(response["headers"])}
    return result


def minimize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    CSVに出力するための最小の情報に変換します。
    """
    result = {}
    result["startedDateTime"] = entry["startedDateTime"]
    result["time"] = entry["time"]
    result["timings"] = entry["timings"]
    result["request"] = _minimize_request(entry["request"])
    result["response"] = _minimize_response(entry["response"])
    return result


def match_entry(entry: dict[str, Any], is_s3_path: bool) -> bool:
    if is_s3_path:
        url = entry["request"]["url"]
        return re.search("https://.*amazonaws\\.com/", url) is not None
    return True


def create_dataframe_from_har_object(data: dict[str, Any], *, is_s3_path: bool) -> pandas.DataFrame:
    """
    harファイルの内容をpandas.DataFrameに変換します。
    """
    tmp_list = [minimize_entry(entry) for entry in data["log"]["entries"] if match_entry(entry, is_s3_path)]
    df_har = pandas.json_normalize(tmp_list)

    columns = [
        "startedDateTime",
        "request.method",
        "request.url",
        "response.status",
        "response.content.size",
        "response.content.mimeType",
        "response.headers.contentLength",
        "time",
        "timings.blocked",
        "timings.dns",
        "timings.connect",
        "timings.send",
        "timings.wait",
        "timings.receive",
        "timings.ssl",
    ]
    return df_har[columns]


def main(args: argparse.Namespace) -> None:
    if len(args.har_file) == 1:
        har_file: Path = args.har_file[0]
        input_data = json.loads(har_file.read_text(encoding="utf-8"))
        df_har = create_dataframe_from_har_object(input_data, is_s3_path=args.only_s3_path)
    else:
        df_har_list = []
        for har_file in args.har_file:
            input_data = json.loads(har_file.read_text(encoding="utf-8"))
            df_sub_har = create_dataframe_from_har_object(input_data, is_s3_path=args.only_s3_path)
            df_sub_har["har_file"] = str(har_file)
            df_har_list.append(df_sub_har)
        df_har = pandas.concat(df_har_list, ignore_index=True)

    if args.sanitize_url:
        df_har["request.url"] = df_har["request.url"].apply(sanitize_url)

    if args.output is not None:
        output_file: Path = args.output
        output_file.parent.mkdir(exist_ok=True, parents=True)
        df_har.to_csv(output_file, index=False, encoding="utf-8")
    else:
        df_har.to_csv(sys.stdout, index=False, encoding="utf-8")


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    subcommand_name = "to_timing_csv"
    subcommand_help = "HARファイルからtimingに関する情報をCSVとして出力します。"

    parser = subparsers.add_parser(subcommand_name, description=subcommand_help, help=subcommand_help)
    parser.set_defaults(func=main)

    parser.add_argument("har_file", type=Path, nargs="+", help="HARファイルのパス。")
    parser.add_argument("-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。")
    parser.add_argument("--only_s3_path", action="store_true", help="AWS S3へアクセスしているリクエストのみを抽出します。")
    parser.add_argument("--sanitize_url", action="store_true", help="URLのQuery Stringに含まれるセンシティブな値をマスクします。")

    return parser
