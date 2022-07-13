
from tag_system_db import session, Tags
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import tag_system_files as tsf
import time


logging.basicConfig(filename="logs.txt", filemode="a+", level=logging.INFO, format='%(asctime)s - %(message)s')
used = set()
class MyHandler(FileSystemEventHandler):
    def on_moved(self, event):
        for part in tsf.to_ignore_parts:
            if part in event.src_path:
                return
        logging.info("Moving: " + event.src_path + " to " + event.dest_path)
        session.query(Tags).filter(Tags.path == event.src_path).update({Tags.path: event.dest_path})
        session.commit()

    def on_created(self, event):
        for part in tsf.to_ignore_parts:
            if part in event.src_path:
                return
        logging.info("Creating: " + event.src_path)
        if session.query(Tags).filter(Tags.path == event.src_path).first():
            return
        session.add(Tags(event.src_path, ''))
        session.commit()


def create_listener(path: str):
    observer = Observer()
    observer.schedule(MyHandler(), path=path, recursive=True)
    observer.start()


def main():
    while True: 
        with open(tsf.DIRS, "r") as f:
            for line in f:
                if line not in used:
                    create_listener(line)
                    used.add(line)
        time.sleep(3)


if __name__ == "__main__":
    tsf.set_up()
    main()