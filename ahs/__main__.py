import argparse
import sys

import ahs
import ahs.sanitize_har
import ahs.to_timing_csv
import ahs.editor_loadtime


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AnnofabのHAR(HTTP Archive)ファイルを扱うコマンドです。")
    parser.set_defaults(command_help=parser.print_help)

    subparsers = parser.add_subparsers(dest="command_name")

    ahs.sanitize_har.add_parser(subparsers)
    ahs.to_timing_csv.add_parser(subparsers)
    ahs.editor_loadtime.add_parser(subparsers)
    return parser


def main(arguments: list[str] | None = None) -> None:
    """ """
    parser = create_parser()

    if arguments is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arguments)

    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception:
            # エラーで終了するためExit Codeを1にする
            sys.exit(1)

    else:
        # 未知のサブコマンドの場合はヘルプを表示
        args.command_help()


if __name__ == "__main__":
    main()
