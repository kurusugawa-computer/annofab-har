from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # `uv run annofab-har --version`では、メタデータからバージョン情報を取得できないため、fallbackしたバージョンを設定する
    __version__ = "0.0.0"
