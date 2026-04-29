"""race-data: 指定したレースの情報を持ったインスタンスを提供します."""

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("race-data")
except (PackageNotFoundError, ImportError):
    __version__ = "unknown"

# 公開するクラス・関数のインポートをここに記述
