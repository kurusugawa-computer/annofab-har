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


def create_dataframe2(df: pandas.DataFrame, frame_content_type: str) -> pandas.DataFrame:
    import numpy as np

    # har_file列がない場合（単一ファイル）、ダミー列を追加
    if "har_file" not in df.columns:
        df["har_file"] = "default"

    results = []
    for har_file, group in df.groupby("har_file"):
        # image/pngリクエストのみ抽出
        png_rows = group[group["response.content.mimeType"] == frame_content_type].reset_index(drop=True)
        frame_count = len(png_rows)

        # 合計contentLength
        content_lengths = png_rows["response.headers.contentLength"].dropna().astype(float)
        total_content_length = content_lengths.sum() if not content_lengths.empty else 0

        # timing.receive
        receive_times = png_rows["timings.receive"].dropna().astype(float)

        # 合計通信時間
        if frame_count > 0:
            first_dt = dateutil.parser.isoparse(png_rows.iloc[0]["startedDateTime"])
            last_row = png_rows.iloc[-1]
            last_dt = dateutil.parser.isoparse(last_row["startedDateTime"])
            last_time_sec = last_row["time"] / 1000.0
            last_finish = last_dt.timestamp() + last_time_sec
            first_start = first_dt.timestamp()
            total_time = last_finish - first_start
        else:
            total_time = 0

        # スループット
        throughput = total_content_length / total_time if total_time > 0 else np.nan

        # 失敗リクエスト数
        fail_count = (png_rows["response.status"] != 200).sum() if frame_count > 0 else 0

        # 偏差値計算関数
        def stdscore(series):
            if len(series) == 0 or np.std(series) == 0:
                return np.nan
            return ((series - np.mean(series)) / np.std(series) * 10 + 50).mean()

        result = {
            "har_file": har_file,
            "frame_count": frame_count,
            "throughput": throughput,
            "receive_mean": receive_times.mean() if not receive_times.empty else np.nan,
            "receive_median": receive_times.median() if not receive_times.empty else np.nan,
            "receive_min": receive_times.min() if not receive_times.empty else np.nan,
            "receive_max": receive_times.max() if not receive_times.empty else np.nan,
            "receive_stdscore": stdscore(receive_times) if not receive_times.empty else np.nan,
            "contentLength_mean": content_lengths.mean() if not content_lengths.empty else np.nan,
            "contentLength_min": content_lengths.min() if not content_lengths.empty else np.nan,
            "contentLength_max": content_lengths.max() if not content_lengths.empty else np.nan,
            "contentLength_stdscore": stdscore(content_lengths) if not content_lengths.empty else np.nan,
            "fail_count": fail_count,
            "total_time": total_time,
            "total_contentLength": total_content_length,
        }
        results.append(result)

    return pandas.DataFrame(results)


def create_dataframe(df: pandas.DataFrame, nth_frames: list[int], frame_content_type: str) -> pandas.DataFrame:
    """
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

    df_output = create_dataframe(df_input, nth_frames=args.nth_frame, frame_content_type="image/png")
    df_summary = create_dataframe2(df_input, frame_content_type="image/png")

    if args.output:
        df_output.to_csv(args.output, index=False, encoding="utf-8")
        # サマリは別ファイルとして出力
        summary_path = args.output.parent / (args.output.stem + "_summary.csv")
        df_summary.to_csv(summary_path, index=False, encoding="utf-8")
        print(f"サマリ出力: {summary_path}")
    else:
        print(df_output.to_csv(index=False, encoding="utf-8"), end="")  # noqa: T201
        print("\n--- summary ---")
        print(df_summary.to_csv(index=False, encoding="utf-8"), end="")  # noqa: T201


if __name__ == "__main__":
    main()
