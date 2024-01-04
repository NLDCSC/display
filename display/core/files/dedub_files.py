import hashlib
import logging
import os
from collections import defaultdict
from multiprocessing.pool import ThreadPool

from display.helpers.logger_class import HelperLogger
from display.webapp.config import Config

logging.setLoggerClass(HelperLogger)


class DeduplicateFilesInFolder(object):
    def __init__(self, top_level_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config = Config()

        self.top_level_path = top_level_path

        if self.top_level_path is None:
            self.dir_workload = [
                f"{os.path.join(self.config.TIMELINE_LOCATION, x)}"
                for x in next(os.walk(self.config.TIMELINE_LOCATION))[1]
            ]
        else:
            self.dir_workload = [
                f"{os.path.join(self.top_level_path, x)}"
                for x in next(os.walk(self.top_level_path))[1]
            ]

    def execute(self):
        with ThreadPool(5) as pool:
            for each_path in pool.map(
                self.check_for_duplicates, self.dir_workload, chunksize=10
            ):
                self.logger.debug(f"Checked duplicates on path: {each_path}")

    def chunk_reader(self, fobj, chunk_size=1024):
        """Generator that reads a file in chunks of bytes"""
        while True:
            chunk = fobj.read(chunk_size)
            if not chunk:
                return
            yield chunk

    def get_hash(self, filename, first_chunk_only=False, hash_algo=hashlib.md5):
        hashobj = hash_algo()
        with open(filename, "rb") as f:
            if first_chunk_only:
                hashobj.update(f.read(1024))
            else:
                for chunk in self.chunk_reader(f):
                    hashobj.update(chunk)
        return hashobj.hexdigest()

    def check_for_duplicates(self, path):
        files_by_mtime = defaultdict(list)
        files_by_small_hash = defaultdict(list)

        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    # if the target is a symlink (soft one), this will
                    # dereference it - change the value to the actual target file
                    # Group files based on mtime
                    full_path = os.path.realpath(full_path)
                    file_mtime = int(os.path.getmtime(full_path))
                except OSError:
                    # not accessible (permissions, etc) - pass on
                    continue
                files_by_mtime[file_mtime].append(full_path)

        # For all files with the same mtime, get their hash on the first 1024 bytes
        for file_mtime, files in files_by_mtime.items():
            if len(files) < 2:
                continue  # this file mtime is unique, no need to spend cpu cycles on it

            for filename in files:
                try:
                    small_hash = self.get_hash(filename, first_chunk_only=True)
                except OSError:
                    # the file access might've changed till the exec point got here
                    continue
                files_by_small_hash[(file_mtime, small_hash)].append(filename)

        # For all files with the hash on the first 1024 bytes, get their hash on the full
        # file - collisions will be duplicates
        for files in files_by_small_hash.values():
            files_by_full_hash = dict()
            if len(files) < 2:
                # the hash of the first 1k bytes is unique -> skip this file
                continue

            for filename in files:
                try:
                    full_hash = self.get_hash(filename, first_chunk_only=False)
                except OSError:
                    # the file access might've changed till the exec point got here
                    continue

                if full_hash in files_by_full_hash:
                    duplicate = files_by_full_hash[full_hash]

                    # duplicate; remove the file....
                    os.remove(duplicate)

                    self.logger.info(f"Duplicate found: [{filename} -> {duplicate}]")

                else:
                    files_by_full_hash[full_hash] = filename

        return path

    def __repr__(self):
        return f"<< DedubFilesInFolder >>"
