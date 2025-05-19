# noqa: INP001
import argparse
from pathlib import Path

import dateutil.parser
import pandas


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="foo")
    parser.add_argument(
        "csv_path",
        type=Path,
        help="画像エディタ画面のHARファイルに対して、`to_timing_csv`コマンドで出力したCSVファイルのパス",
    )
    parser.add_argument("-o", "--output", type=Path, help="出力先。未指定ならば標準出力に出力します。")
    parser.add_argument("-n", "--nth_frame", type=int, nargs="+", default=[1], help="N枚目のimage/pngリクエストを指定します（1始まり）")
    return parser


def create_dataframe_frame_request_statistics(df: pandas.DataFrame, frame_content_type: str) -> pandas.DataFrame:
    """
    フレームのリクエスト統計を算出します。
    """
    import numpy as np

    # har_file列がない場合（単一ファイル）、ダミー列を追加
    if "har_file" not in df.columns:
        df["har_file"] = "default"

    # image/pngリクエストのみ抽出
    png_df = df[df["response.content.mimeType"] == frame_content_type].copy()

    # 必要な列をfloat化
    png_df["response.headers.contentLength"] = pandas.to_numeric(png_df["response.headers.contentLength"], errors="coerce")
    png_df["timings.receive"] = pandas.to_numeric(png_df["timings.receive"], errors="coerce")
    png_df["time"] = pandas.to_numeric(png_df["time"], errors="coerce")
    png_df["response.status"] = pandas.to_numeric(png_df["response.status"], errors="coerce")

    # pivot_table/aggで集計
    agg_dict = {
        "timings.receive": ["mean", "median", "min", "max", "std", "sum"],
        "response.headers.contentLength": ["mean", "min", "max", "std", "sum"],
        "response.status": lambda x: (x != 200).sum(),
        "startedDateTime": "count",
    }
    summary = png_df.pivot_table(
        index="har_file",
        values=["timings.receive", "response.headers.contentLength", "response.status", "startedDateTime"],
        aggfunc=agg_dict,
        fill_value=np.nan,
        observed=True,
    )

    # カラム名をフラット化
    summary.columns = ["_".join([col[0], col[1]]) if isinstance(col, tuple) else col for col in summary.columns.to_numpy()]
    summary = summary.rename(
        columns={
            "startedDateTime_count": "frame_count",
            "response.status_<lambda>": "fail_count",
        }
    )

    receive_std_list = []
    contentLength_std_list = []  # noqa: N806

    for _, group in png_df.groupby("har_file"):
        receive_std_list.append(np.std(group["timings.receive"].dropna()))
        contentLength_std_list.append(np.std(group["response.headers.contentLength"].dropna()))

    summary["timings.receive_std"] = receive_std_list
    summary["response.headers.contentLength_std"] = contentLength_std_list

    summary["throughput"] = summary["response.headers.contentLength_sum"] / summary["timings.receive_sum"]

    # 列順を調整
    col_order = [
        "frame_count",
        "throughput",
        "timings.receive_mean",
        "timings.receive_median",
        "timings.receive_min",
        "timings.receive_max",
        "timings.receive_std",
        "response.headers.contentLength_mean",
        "response.headers.contentLength_min",
        "response.headers.contentLength_max",
        "response.headers.contentLength_std",
        "fail_count",
        "response.headers.contentLength_sum",
        "timings.receive_sum",
    ]
    summary = summary[col_order]

    summary = summary.reset_index()
    return summary


def create_dataframe_nth_frames_loading_time(df: pandas.DataFrame, nth_frames: list[int], frame_content_type: str) -> pandas.DataFrame:
    """
    N枚目のフレームの読み込みが完了するまでの時間を算出します。

    Args:
        nth_frames: N枚目のフレームの読み込みが完了するまでの時間を算出します。
        frame_content_type: フレームのContent-Typeを指定します。
    """
    # har_file列がない場合（単一ファイル）、ダミー列を追加
    if "har_file" not in df.columns:
        df["har_file"] = "default"

    results = []
    for har_file, group in df.groupby("har_file"):
        group = group.sort_values("startedDateTime").reset_index(drop=True)  # noqa: PLW2901
        first_row = group.iloc[0]
        first_dt_str = first_row["startedDateTime"]

        first_dt = dateutil.parser.isoparse(first_dt_str)

        sub_result = {"har_file": har_file, "first_startedDateTime": first_dt_str}
        # image/pngリクエスト抽出
        png_rows = group[group["response.content.mimeType"] == frame_content_type].reset_index(drop=True)
        for nth_frame in nth_frames:
            if len(png_rows) >= nth_frame:
                nth_row = png_rows.iloc[nth_frame - 1]
                nth_dt_str = nth_row["startedDateTime"]
                nth_time_sec = nth_row["time"] / 1000.0
                nth_dt = dateutil.parser.isoparse(nth_dt_str)
                elapsed_sec = (nth_dt - first_dt).total_seconds() + nth_time_sec

            else:
                elapsed_sec = None

            sub_result.update(
                {
                    f"{nth_frame}_frame_elapsed_seconds": elapsed_sec,
                }
            )

        results.append(sub_result)

    return pandas.DataFrame(results)


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    df_input = pandas.read_csv(args.csv_path)

    frame_content_type = "image/png"
    df1 = create_dataframe_nth_frames_loading_time(df_input, nth_frames=args.nth_frame, frame_content_type=frame_content_type)
    df2 = create_dataframe_frame_request_statistics(df_input, frame_content_type=frame_content_type)
    df_output = df1.merge(df2, on="har_file", how="left")

    if args.output:
        df_output.to_csv(args.output, index=False, encoding="utf-8")
    else:
        print(df_output.to_csv(index=False, encoding="utf-8"), end="")  # noqa: T201


if __name__ == "__main__":
    main()
