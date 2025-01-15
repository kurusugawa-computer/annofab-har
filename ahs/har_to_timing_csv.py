import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HARファイルからtimingに関する情報をCSVとして出力します。")
    parser.add_argument("har_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。")
    return parser


def _minimize_request(request: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key in ("method", "url"):
        result[key] = request[key]
    return result


def _minimize_response(response: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key in ("status",):
        result[key] = response[key]

    content = response["content"]
    result["content"] = {
        "size": content["size"],
        "mimeType": content["mimeType"],
    }

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


def create_dataframe_from_har_object(data: dict[str, Any]) -> pandas.DataFrame:
    """
    harファイルの内容をpandas.DataFrameに変換します。
    """
    tmp_list = [minimize_entry(entry) for entry in data["log"]["entries"]]
    df_har = pandas.json_normalize(tmp_list)

    columns = [
        "startedDateTime",
        "request.method",
        "request.url",
        "response.status",
        "response.content.size",
        "response.content.mimeType",
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


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    input_data = json.loads(args.har_file.read_text(encoding="utf-8"))
    df_har = create_dataframe_from_har_object(input_data)
    if args.output is not None:
        output_file: Path = args.output
        output_file.parent.mkdir(exist_ok=True, parents=True)
        df_har.to_csv(output_file, index=False, encoding="utf-8")
    else:
        df_har.to_csv(sys.stdout, index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
