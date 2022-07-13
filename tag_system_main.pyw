# let's start with database
import functools
import enum
import os
import tag_system_files as tsf
from tag_system_files import tag_delimiter
from pathlib import Path
import tag_system_db as db
from tag_system_db import Tags
import background as bg


tsf.set_up()
session = db.Session()


def init(path: str):
    path = os.path.abspath(path)
    print(path)
    for file in tsf.list_files(path):
        if not session.query(Tags).filter(Tags.path == file).first():
            session.add(Tags(path=file, tags=''))
    session.commit() 
    bg.create_listener(path)
    with open(tsf.DIRS, 'r') as f:
        for line in f.readlines():
            if line.strip() == path:
                return
    with open(tsf.DIRS, 'a+') as f:
        f.write(os.path.abspath(path) + '\n')



def have_tag(file: str, tag: str):
    res = session.query(Tags).filter(Tags.path == file).first()
    if not res:
        return
    return (tag + tag_delimiter) in res.tags


def add_tag_file(file: str, tag: str):
    if have_tag(file, tag):
        print("Tag '{}' already exists in {}".format(tag, file))
        return
    if not session.query(Tags).filter(Tags.path == file).first():
            session.add(Tags(path=file, tags=tag + tag_delimiter))
    else:
        session.query(Tags).filter(Tags.path == file).update({Tags.tags: Tags.tags + tag + tag_delimiter})
    print("Added tag '{}' to {}".format(tag, file))


def remove_tag_file(file: str, tag: str):
    if not have_tag(file, tag):
        print("Tag '{}' does not exist in {}".format(tag, file))
        return
    res = session.query(Tags).filter(Tags.path == file).first()
    tags = res.tags
    session.delete(res)
    session.add(Tags(path=file, tags=tags.replace(tag + tag_delimiter, '')))
    print("Removed tag '{}' from {}".format(tag, file))


def remove_tag(path: str, tag: str):
    path = os.path.abspath(path)
    if os.path.isfile(path):
        remove_tag_file(path, tag)
    else:
        for file in tsf.list_files(path):
            remove_tag_file(file, tag)
    session.commit()


def add_tag(path: str, tag: str):
    path = os.path.abspath(path)
    if os.path.isfile(path):
        add_tag_file(path, tag)
    else:
        for file in tsf.list_files(path):
            add_tag_file(file, tag)
    session.commit()


class Commands(enum.Enum):
    remake = 0
    add_tag = 1
    print_help = 2
    current = 3
    exit = 4


def print_help():
    # TODO: rewrite 
    print(">init <path> - initializes tags for all files in <path>"
          ">add_tag <path> <tag> - add tag to all files satisfying the given path\n"
          ">print_help - print this help\n"
          ">current - print current state of database\n"
          ">remove_tag <path> <tag> - remove tag from all files satisfying the given path\n"
          ">exit - exit program\n\n"
          "little help about the add_tag command:\n"
          "please provide tags in single quotes, e.g. to add tag 'segment tree' to file './Round/solution.cpp', you should enter:\n"
          ">add_tag ./Round/solution.cpp 'segment tree'\n"
          "and to add tag 'segment tree' to all files in directory './Round' and its subdirectories, you should enter:\n"
          ">add_tag ./Round 'segment tree'\n")


def extract_tag(s:str):
    n = len(s)
    i = 0
    while i < n and s[i] != '\'':
        i += 1
    if i == n:
        return ''
    i += 1
    tag = []
    while i < n and s[i] != '\'':
        tag.append(s[i])
        i += 1
    return ''.join(tag)


def cmp(a: Tags, b: Tags):
    if a.path < b.path:
        return -1
    else:
        return 1


def main():
    print("Hi! This is a test version of my tag system.\n"
          "Right now you can only interact with it via terminal, but it will evolve with time.\n"
          "Now, here is the list of commands.")
    print_help()
    while True:
        command, *arg = input("---\nEnter command:\n>>> ").split()
        session = db.Session()
        if command == "init":
            if len(arg) == 0:
                path = Path(os.getcwd()).parent.absolute()
            else:
                path = arg[0]
            init(path)
        elif command.endswith("tag"):
            tag = extract_tag(''.join(arg[1:]))
            if tag == '':
                print("Invalid arguement (tag should not be empty)")
                continue
            if command == "add_tag":
                add_tag(arg[0].strip(), tag)
            elif command == "remove_tag":
                remove_tag(arg[0].strip(), tag)
            else:
                print("Invalid command")
        elif command == "print_help":
            print_help()
        elif command == "current":
            tags = list(session.query(Tags).all())
            tags.sort(key=functools.cmp_to_key(cmp))
            if len(arg):
                for tag in tags:
                    print(tag)
            else:
                for tag in tags[:10]:
                    print(tag)
                if len(tags) > 10:
                    print("...")
            print(f"In total {len(tags)} files in the system.")
        elif command == "exit":
            break
        else:
            print("Unknown command. Try again.")


if __name__ == "__main__":
    main()
    # session.commit()  # committing changes to database
    # session.close()  # closing session with database
    # engine.dispose()  # closing engine with database
    print("Bye!")
    exit(0)  # exiting programm
