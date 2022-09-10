import functools
import os
from typing import Callable, Collection, List
import tag_system_files as tsf
import config
from pathlib import Path
import tag_system_db as db
import logging
from tag_system_db import Tags

tsf.set_up()
session = db.Session()
logging.basicConfig(level=logging.INFO)


def init(path: str):
    """Add all files satisfying path to database"""
    path = os.path.abspath(path)
    for file in tsf.list_files(path):
        if not session.query(Tags).filter(
                Tags.path == file).first():  # if the file is already in the db, there is no need to add it
            session.add(Tags(path=file, tags=''))
    session.commit()
    with open(config.DIRS, 'r') as f:  # add the directory as a directory to watch for background.pyw
        for line in f.readlines():
            if line.strip() == path:
                return
    with open(config.DIRS, 'a+') as f:
        f.write(os.path.abspath(path) + '\n')


def have_tag(file: str, tag: str):
    """Check if the given file have the given tag"""
    res = session.query(Tags).filter(Tags.path == file).first()
    if not res:
        return
    return (tag + config.tag_delimiter) in res.tags


def add_tag_file(file: str, tag: str):
    """Adds tag to a file; if there is no such file, creates it; if the file already has the tag, gives a warning"""
    if have_tag(file, tag):
        logging.warning(f"Tag '{tag}' already exists in {file}")
        return
    if not session.query(Tags).filter(Tags.path == file).first():
        session.add(Tags(path=file, tags=tag + config.tag_delimiter))
    else:
        session.query(Tags).filter(Tags.path == file).update({Tags.tags: Tags.tags + tag + config.tag_delimiter})
    logging.info(f"Added tag '{tag}' to {file}")


def remove_tag_file(file: str, tag: str):
    if not have_tag(file, tag):
        logging.warning(f"Tag '{tag}' does not exist in {file}")
        return
    if not session.query(Tags).filter(Tags.path == file).first():
        logging.warning(f"The file '{file}' is not in the database")
    else:
        session.query(Tags).filter(Tags.path == file).update(
            {Tags.tags: Tags.tags.replace(tag + config.tag_delimiter, '')})
        logging.info(f"Removed tag '{tag}' from {file}")


def remove_tag(path: str, tag: str):
    """Remove the given tag from all files satisfying the path"""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        remove_tag_file(path, tag)
    else:
        for file in tsf.list_files(path):
            remove_tag_file(file, tag)
    session.commit()


def add_tag(path: str, tag: str):
    """Add tbe given tag to all files satisfying the given path"""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        add_tag_file(path, tag)
    else:
        for file in tsf.list_files(path):
            add_tag_file(file, tag)
    session.commit()


def print_help():
    print(">init '<path>' - initializes tags for all files in <path>\n"
          ">add_tag '<path>' '<tag>' - add tag to all files satisfying the given path\n"
          ">help - print this help\n"
          ">current - print current state of database; optional arguement '-o' to print all files in database\n"
          ">remove_tag '<path>' '<tag>' - remove tag from all files satisfying the given path\n"
          ">choose 'path' '<tag1>, <tag2>, ...' - "
          "print all files that have all of the listed tags and satisfy the given path;"
          "if path is empty, searches throughout all database\n"
          ">cls - clear screen\n"
          ">remake - remake database (can be used if there are some new folders to ignore)\n"
          ">exit - exit program\n\n"
          "little help about the add_tag command:\n"
          "please provide tags in single quotes, e.g. to add tag 'segment tree' to file './Round/solution.cpp',"
          " you should enter:\n"
          ">add_tag './Round/solution.cpp' 'segment tree'\n"
          "and to add tag 'segment tree' to all files in directory './Round' and its subdirectories, you should enter:"
          "\n"
          ">add_tag './Round' 'segment tree'\n")


def parse(s: str, start: int, delimiters: List[str]):
    """Get value from the string, where it is embraced by delimiters
    :param s: input string
    :param start: start of the range in which value is searched
    :param delimiters: delimiters
    :return: value and end of its вхождение in string
    """
    n = len(s)
    i = start
    while i < n and not (s[i] in delimiters):
        i += 1
    if i == n:
        return '', -1
    i += 1
    tag = []
    while i < n and not (s[i] in delimiters):
        tag.append(s[i])
        i += 1
    i += 1
    return ''.join(tag), i


def print_long(data: Collection, butch=10, f: Callable = lambda x: x):
    """Print data from iterable by butches"""
    if butch == 0:
        raise ValueError("Butch shouldn't be empty")
    print(f"In total {len(data)} elements.")
    counter = 0
    for el in data:
        print(f(el))
        counter += 1
        if (counter + 1) % butch == 0:
            c = input("Continue? (y/n)>> ").lower()
            if c == 'n':
                print("...")
                break


def current(arg):
    """Print current state of the database; if arg is '-o', print all elements, otherwise print in butches"""
    tags = list(session.query(Tags).all())
    tags.sort(key=functools.cmp_to_key(cmp))
    if arg == '-o':
        for tag in tags:
            print(tag)
    else:
        print_long(tags, f=lambda x: x.path)


def cmp(a: Tags, b: Tags):
    """Comparator to sort files by path"""
    if a.path < b.path:
        return -1
    else:
        return 1


def get_by_tags(path: str, tags: List[str]) -> List[str]:
    """Get files from the given path which have ALL of the given tags"""
    # TODO: rewrite for & and ||
    res = []
    if path == '':  # check all files in db
        for file in session.query(Tags).all():
            flag = True
            for tag in tags:
                if not (tag in file.tags):
                    flag = False
                    break
            if flag:
                res.append(file.path)
    else:
        for file in tsf.list_files(path):  # check all files in db satisfying path
            el = session.query(Tags).filter(Tags.path == file).first()
            if el:
                flag = True
                for tag in tags:
                    if not (tag in el.tags):
                        flag = False
                        break
                if flag:
                    res.append(el.path)
    return sorted(res)


def choose(path, tags):
    """Print files from given path which has ALL of the given tags"""
    files = get_by_tags(path, tags)
    print_long(files)


def remake():
    """Recreate database"""
    used = set()
    with open(config.DIRS, 'r') as f:
        for directory in f.readlines():
            init(directory.strip())
            for file in tsf.list_files(directory.strip()):
                used.add(file)
    for file in session.query(Tags).all():
        if file.path not in used:
            session.delete(file)
    session.commit()


def main():
    """User interaction"""
    print("Hi! This is a test version of my tag system.\n"
          "Right now you can only interact with it via terminal, but it will evolve with time.\n"
          "Now, here is the list of commands.")
    print_help()
    delimiters = ["'", '"']
    while True:
        inp = input("---\nEnter command:\n>>> ").split()
        if len(inp) == 0:
            continue
        command, *arg = inp
        arg = ' '.join(arg).strip()
        if command == "init":
            if len(arg) == 0:
                path = ''
            else:
                path = parse(arg, 0, delimiters)[0]
            if path == '':
                print("Invalid path. Did you provide it in upper commas(??)?")
                continue
            init(path)
        elif command.endswith("tag"):
            path, i = parse(arg, 0, delimiters)
            tag = parse(arg, i, delimiters)[0]
            if path == '':
                c = input(
                    f"Are you sure you want to add tag '{tag}' to all files in the current directory? (y/n)>> ").lower()
                if c == 'n':
                    continue
                else:
                    path = Path(os.getcwd()).parent.absolute()
            if tag == '':
                print("Invalid arguement (tag and path should not be empty)")
                continue
            if command == "add_tag":
                add_tag(path.strip(), tag)
            elif command == "remove_tag":
                remove_tag(path.strip(), tag)
            else:
                print("Invalid command")
        elif command == "help":
            print_help()
        elif command == "current":
            current(arg)
        elif command == "choose":
            path, i = parse(arg, 0, delimiters)
            path = path.strip()
            tags = parse(arg, i, delimiters)[0].split(',')
            tags = list(map(lambda x: x.strip(), tags))
            tags = list(filter(lambda x: x != '', tags))
            choose(path, tags)
        elif command == 'remake':
            remake()
        elif command == "cls":
            os.system('cls' if os.name == 'nt' else 'clear')
        elif command == "exit":
            break
        else:
            print("Unknown command. Try again.")


if __name__ == "__main__":
    main()
    print("Bye!")
    exit(0)
