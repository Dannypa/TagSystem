import os
import config


def get_file_create_time(filename: str) -> float:
    """
    Get the creation time of a file.
    :param filename: The filename.
    :return: The creation time.
    """
    return os.path.getctime(filename)


def is_parent(parent_path: str, child_path: str) -> bool:
    """
    :param parent_path: The parent path.
    :param child_path: The child path.
    :return: True if the child path is a child of the parent path.
    """
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)
    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])


to_ignore_dirs = []
to_ignore_parts = []


def list_files(path: str) -> list:
    """
    List files in a directory excluding files in to_ignore_dirs and files with parts in to_ignore_parts.
    :param path: The path to list files from.
    """
    # banned paths are already absolute
    for directory, dirs, files in os.walk(path):
        to_skip = False
        directory = os.path.abspath(directory)
        directory += config.delimiter
        for banned in to_ignore_dirs:
            if is_parent(banned, directory):
                to_skip = True
                break
        if to_skip:
            continue
        for part in to_ignore_parts:
            if part in directory:
                to_skip = True
                break
        if to_skip:
            continue
        for file in files:
            yield os.path.join(directory, file)


def set_up():
    global to_ignore_dirs, to_ignore_parts
    to_ignore_dirs = []
    to_ignore_parts = []
    with open(config.ignore_dirs, 'r') as f:
        for line in f:
            to_ignore_dirs.append(os.path.abspath(line.strip()))
    with open(config.ignore_parts, 'r') as f:
        for line in f:
            part = line.strip()
            if not part.startswith(config.delimiter):
                part = config.delimiter + part
            if not part.endswith(config.delimiter):
                part = part + config.delimiter
            to_ignore_parts.append(part)
    to_ignore_parts.append(config.delimiter + f"{config.TABLENAME}.db-journal")


if __name__ == "__main__":
    set_up()
