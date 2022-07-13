import os


delimiter = '\\' if os.name == 'nt' else '/'
tag_delimiter = '/\\'
TABLENAME = 'tags'
DIRS = "directories.txt"


def get_file_create_time(filename:str) -> float:
    """
    Get the creation time of a file.
    :param filename: The filename.
    :return: The creation time.
    """
    return os.path.getctime(filename)


def is_parent(parent_path:str, child_path:str) -> bool:
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
def list_files(path:str) -> list:
    """
    List files in a directory excluding files in to_ignore_dirs and files with parts in to_ignore_parts.
    :param path: The path to list files from.
    :param to_ignore_dirs: The directories to ignore.
    """
    # banned paths are already absolute
    for dir, dirs, files in os.walk(path):
        to_skip = False
        dir = os.path.abspath(dir)
        dir += delimiter
        for banned in to_ignore_dirs:
            if is_parent(banned, dir):
                to_skip = True
                break
        if to_skip:
            continue
        for part in to_ignore_parts:
            if part in dir:
                to_skip = True
                break
        if to_skip:
            continue
        for file in files:
            yield os.path.join(dir, file)
        

def set_up():
    global to_ignore_dirs, to_ignore_parts
    if len(to_ignore_dirs) == 0 and len(to_ignore_parts) == 0:
        return
    with open(".tagignoredirs", 'r') as f:
        for line in f:
            to_ignore_dirs.append(os.path.abspath(line.strip()))
    with open(".tagignoreparts", 'r') as f:
        for line in f:
            part = line.strip()
            if not part.startswith(delimiter):
                part = delimiter + part
            if not part.endswith(delimiter):
                part = part + delimiter
            to_ignore_parts.append(part)
    to_ignore_parts.append(delimiter + f"{TABLENAME}.db-journal")


if __name__ == "__main__":
    set_up()
    cnt = 0
    print(os.getcwd())
    for file in list_files(os.getcwd()):
        print(file)
        cnt += 1
    print(cnt)
   
    