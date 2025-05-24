import argparse
import sys
import traceback

import ahs
import ahs.editor_loadtime
import ahs.sanitize_har
import ahs.to_timing_csv


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AnnofabのHAR(HTTP Archive)ファイルを扱うコマンドです。")
    parser.add_argument("--version", action="version", version=f"annofab_har {ahs.__version__}")
    parser.set_defaults(command_help=parser.print_help)

    subparsers = parser.add_subparsers(dest="command_name")

    ahs.sanitize_har.add_parser(subparsers)
    ahs.to_timing_csv.add_parser(subparsers)

    # 全部のエディタに対応しておらず未完成なので、一時的にコメントアウト
    # ahs.editor_loadtime.add_parser(subparsers)
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
            traceback.print_exc()
            # エラーで終了するためExit Codeを1にする
            sys.exit(1)

    else:
        # 未知のサブコマンドの場合はヘルプを表示
        args.command_help()


if __name__ == "__main__":
    main()
