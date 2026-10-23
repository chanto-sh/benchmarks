from app import _build_info


def version_string():
    return f"orders@{_build_info.COMMIT} ({_build_info.BUILD})"
