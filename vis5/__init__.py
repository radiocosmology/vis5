# your_library/__init__.py
import dunamai as _dunamai

__version__ = _dunamai.get_version(
    "vis5", third_choice=_dunamai.Version.from_any_vcs
)
