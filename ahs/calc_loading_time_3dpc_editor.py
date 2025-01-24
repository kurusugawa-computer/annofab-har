import argparse
import datetime
import json
from pathlib import Path
from typing import Any


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="3次元エディタにアクセスしたときのHARファイルから、全フレームを読み込むまでの時間を算出します。"
        "`index.html`のリクエストから`validate-operation` APIのリクエストまでの時間の差分を、全フレームを読み込むまでの時間とします。"
    )
    parser.add_argument("har_file", type=Path, nargs="+", help="HARファイルのパス。")
    parser.add_argument("-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。")
    return parser


def match_start_request(request: dict[str, Any]) -> bool:
    url = request["url"]
    method = request["method"]
    return method == "GET" and url.startswith("https://d2rljy8mjgrfyd.cloudfront.net/3d-editor-latest/index.html")


def match_end_request(request: dict[str, Any]) -> bool:
    url = request["url"]
    method = request["method"]
    return method == "POST" and url.endswith("validate-operation")


def calc_loading_time(data: dict[str, Any]) -> dict[str, Any]:
    """
    harファイルの内容から、全フレームを読み込むまでの時間を算出します。
    """
    start_request_time = None
    end_request_time = None
    for entry in data["log"]["entries"]:
        request = entry["request"]
        if match_start_request(request):
            start_request_time = entry["startedDateTime"]
            continue

        if match_end_request(request):
            end_request_time = entry["startedDateTime"]
            break

    result = {"start_request.startedDateTime": start_request_time, "end_request.startedDateTime": end_request_time}
    if start_request_time is not None and end_request_time is not None:
        time_seconds = (datetime.datetime.fromisoformat(end_request_time) - datetime.datetime.fromisoformat(start_request_time)).total_seconds()
        result["time_seconds"] = time_seconds
    else:
        result["time_seconds"] = None

    return result


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    result = []
    for har_file in args.har_file:
        input_data = json.loads(har_file.read_text(encoding="utf-8"))
        sub_result = calc_loading_time(input_data)
        sub_result["har_file"] = str(har_file)
        result.append(sub_result)

    output_string = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output is not None:
        output_file: Path = args.output
        output_file.parent.mkdir(exist_ok=True, parents=True)
        output_file.write_text(output_string, encoding="utf-8")
    else:
        print(output_string)  # noqa: T201


if __name__ == "__main__":
    main()
