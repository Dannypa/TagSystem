from tag_system_db import session, Tags
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import config
import tag_system_files as tsf
import time

logging.basicConfig(filename=config.logs_dir, filemode="a+", level=logging.INFO, format='%(asctime)s - %(message)s')


class MyHandler(FileSystemEventHandler):
    def on_moved(self, event):
        for part in tsf.to_ignore_parts:  # if file does not need to be in database
            if part in event.src_path:
                return
        logging.info("Moving: " + event.src_path + " to " + event.dest_path)
        session.query(Tags).filter(Tags.path == event.src_path).update(
            {Tags.path: event.dest_path})  # updating path in db
        session.commit()

    def on_created(self, event):
        for part in tsf.to_ignore_parts:  # if file does not need to be in database
            if part in event.src_path:
                return
        logging.info("Creating: " + event.src_path)
        if session.query(Tags).filter(
                Tags.path == event.src_path).first():  # if something with the same filename is already in db
            return  # we don't want to spam data to database
        session.add(Tags(event.src_path, ''))
        session.commit()

    def on_modified(self, event):
        if event.src_path.endswith('.tagignoreparts') or event.src_path.endswith(
                '.tagignoredirs'):  # if we need to have new restrictions
            tsf.set_up()


listeners = dict()  # directory path -> observer


def create_listener(path: str):
    observer = Observer()
    observer.schedule(MyHandler(), path=path, recursive=True)
    observer.start()
    listeners[path] = observer


# TODO: may be delete directory from tsf.DIRS if dir1 is parent for dir2, but this may not be useful

def main():
    # remake listeners every 3 seconds
    while True:
        with open(config.DIRS, "r") as f:
            current = set()  # set for all files that are currently need to be observed
            for line in f:
                if line not in listeners:  # if the file is not yet observed
                    try:
                        create_listener(line.strip())
                    except Exception as e:
                        logging.error(line.strip())
                        logging.error(e)
                current.add(line)
            # deleting unnecessary observers
            to_pop = set()
            for file in listeners:
                if not (file in current):  # if we are observing file which does not need observation
                    listeners[file].stop()
                    to_pop.add(file)
            for file in to_pop:
                listeners.pop(file)
        time.sleep(3)


if __name__ == "__main__":
    try:
        tsf.set_up()
    except Exception as eo:
        logging.error(eo)
    main()
