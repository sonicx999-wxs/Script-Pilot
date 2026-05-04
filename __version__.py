# ======================================================================
# 版本控制文件 (Version Control File)
# ======================================================================

# __version__.py
"""
Semantic Versioning (语义化版本控制)
格式: MAJOR.MINOR.PATCH[-PRERELEASE]
"""

__title__ = "Script-Pilot"
__description__ = "Python 瘦壳启动器生成引擎 (Thin-Shell Launcher Generator)"
__version__ = "0.2.0"
__author__ = "The Commander & Genesis Architect"
__license__ = "MIT"

def get_version_info():
    return f"{__title__} v{__version__}"
