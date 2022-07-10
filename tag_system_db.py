# let's start with database
import functools
import re
from traceback import print_tb
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker
import enum
import os
import tag_system_files as tsf


engine = create_engine('sqlite:///tags.db?check_same_thread=False')  # creating a database file

Base = declarative_base()  # parent class for our Table class


tag_delimiter = '/\\'
tsf.set_up()


class Tags(Base):
    __tablename__ = 'tags'  # name in database
    # primary key means that id will define object (i guess?)
    id = Column(Integer, primary_key=True)
    path = Column(String, default='')
    tags = Column(String, default='')


    def __init__(self, path, tags):
        self.id = id
        self.path = path
        self.tags = tags

    def __repr__(self):
        return f"id: {self.id}; path: {self.path}; tags: {list(self.tags.split(tag_delimiter))}"


Base.metadata.create_all(engine)  # creating database

Session = sessionmaker(bind=engine)  # creating this to work with the database
session = Session()  # to manage database


def get_file_id(file: str):
    # TODO: fix: doesn't work with unix
    return int(tsf.get_file_create_date(file) * 1e9)


def remake(path: str):
    print(path)
    used = set()
    for file in tsf.list_files(path):
        fid = get_file_id(file)
        used.add(fid)
        if not session.query(Tags).filter(Tags.id == fid).first():
            session.add(Tags(id=fid, path=file, tags=''))
        else:
            session.query(Tags).filter(Tags.id == fid).update({Tags.path: file})
    for tag in session.query(Tags).all():
        if tag.id not in used:
            session.delete(tag)
    session.commit()


def have_tag(file: str, tag: str):
    fid = get_file_id(file)
    res = session.query(Tags).filter(Tags.id == fid).first()
    if not res:
        return
    return (tag + tag_delimiter) in res.tags


def add_tag_file(file: str, tag: str):
    fid = get_file_id(file)
    if have_tag(file, tag):
        print("Tag '{}' already exists in {}".format(tag, file))
        return
    if not session.query(Tags).filter(Tags.id == fid).first():
            session.add(Tags(id=fid, path=file, tags=tag + tag_delimiter))
    else:
        session.query(Tags).filter(Tags.id == fid).update({Tags.tags: Tags.tags + tag + tag_delimiter})
    print("Added tag '{}' to {}".format(tag, file))


def remove_tag_file(file: str, tag: str):
    fid = get_file_id(file)
    if not have_tag(file, tag):
        print("Tag '{}' does not exist in {}".format(tag, file))
        return
    res = session.query(Tags).filter(Tags.id == fid).first()
    tags = res.tags
    session.delete(res)
    session.add(Tags(id=fid, path=file, tags=tags.replace(tag + tag_delimiter, '')))
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
    print(">remake <path> - update database in provided directory(needs to be done after moving /renaming some files)(leave empty for directory to be current directory)\n"
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


def compare():
    print("Comparing database with filesystem...")
    files = set(tsf.list_files(os.getcwd()))
    for file in session.query(Tags).all():
        if not (file.path in files):
            print("File {} does not exist in filesystem".format(file.path))
    print("Comparing filesystem with database...")
    missing = []
    for file in files:
        if not session.query(Tags).filter(Tags.path == file).first():
            print("File {} does not exist in database".format(file))
            missing.append(file)
    print("Done")
    for file in missing:
        fid = get_file_id(file)
        print(f"{file}    <->    {session.query(Tags).filter(Tags.id == fid).first().path}")


def main():
    print("Hi! This is a test version of my tag system.\n"
          "Right now you can only interact with it via terminal, but it will evolve with time.\n"
          "Now, here is the list of commands.")
    print_help()
    while True:
        command, *arg = input("---\nEnter command:\n>>> ").split()
        if command == "remake":
            if len(arg) == 0:
                path = os.getcwd()
            else:
                path = arg[0].strip()
            remake(path)
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
            for tag in tags:
                print(tag)
        elif command == "compare":
            compare()
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
