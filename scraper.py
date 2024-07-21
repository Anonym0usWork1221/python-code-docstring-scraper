from utils.database_handler import JsonRecordHandler
from github import RateLimitExceededException
from utils.git_scraper import GitScraper
from utils.pprints import PPrints
from threading import Thread, Lock
from os import path
import subprocess
import signal
import time
import sys

TEMP_EXE = """
from {file_name} import Scraper
obj = Scraper(number_of_threads={num_of_threads}, git_tokens={tokens_list})
obj.start_scraper()
"""


class Scraper(object):
    """
    This class orchestrates the entire scraping process and manages multiple GitScraper instances.

    Args:
        search_query (str): The GitHub search query used to filter repositories.
        git_tokens (str): The GitHub personal access token for authentication.
        id_record_file (str): The file name for storing scraped repository IDs.
        db_commit_index (int): The number of records after which the database is committed.
        width_for_wrap (int): The width used for wrapping docstrings.
        verbose (bool): Whether to print verbose status messages.
        use_threads (bool): Whether to use multiple threads for scraping.
        number_of_threads (int): The number of threads to use for scraping.
        data_base_path (str): The path where the SQLite database will be stored.
        data_base_file_name (str): The name of the SQLite database file.

    Methods:
        _create_instance(): Creates and returns a GitScraper instance.
        start_scraper(): Initiates the scraping process with or without multiple threads.
    """

    def __init__(self,
                 search_query: str = "language:python pushed:<2023-01-01",
                 git_tokens: list = None,
                 id_record_file: str = "ids.json",
                 db_commit_index: int = 1500,
                 width_for_wrap: int = 70,
                 verbose: bool = True,
                 use_threads: bool = True,
                 number_of_threads: int = 2,
                 data_base_path: str = "./database",
                 data_base_file_name: str = "python_code_snippets.db",
                 ) -> None:

        """
        Initialize the Scraper object with various configuration options.

        Args:
            search_query (str): GitHub search query used to filter repositories.
            git_tokens (list): GitHub personal access token for authentication.
            id_record_file (str): File name for storing scraped repository IDs.
            db_commit_index (int): Number of records after which the database is committed.
            width_for_wrap (int): Width used for wrapping docstrings.
            verbose (bool): Whether to print verbose status messages.
            use_threads (bool): Whether to use multiple threads for scraping.
            number_of_threads (int): The number of threads to use for scraping.
            data_base_path (str): The path where the SQLite database will be stored.
            data_base_file_name (str): The name of the SQLite database file.

        Returns:
            None
        """

        # User customizable
        if git_tokens is None:
            git_tokens = []
        self._search_query: str = search_query
        self._git_token: list = git_tokens
        if not self._git_token:
            self.re_execute_main_program()
        self._id_records_file: str = id_record_file
        self._db_commit_index: int = db_commit_index
        self._wrap_width: int = width_for_wrap
        self._verbose: bool = verbose
        self._use_thread: bool = use_threads
        self._no_of_threads: int = number_of_threads
        self._data_base_path: str = data_base_path
        self._data_base_file_name: str = data_base_file_name

        # Script auto customizing
        self._threads_object_instances: list = []
        self._running_threads: list[Thread] = []
        self._thread_lock = Lock()
        self._json_handler = JsonRecordHandler(total_tokens=self._git_token, thread_lock=self._thread_lock)
        self._pprints = PPrints(print_lock=self._thread_lock)

    def _create_instance(self) -> GitScraper:
        """
        Create and return a GitScraper instance for scraping GitHub repositories.

        Returns:
            GitScraper: An instance of the GitScraper class.
        """

        inst = GitScraper(json_handler=self._json_handler, thread_lock=self._thread_lock,
                          search_query=self._search_query,
                          id_record_file=self._id_records_file, db_commit_index=self._db_commit_index,
                          width_for_wrap=self._wrap_width, data_base_path=self._data_base_path,
                          data_base_file_name=self._data_base_file_name,
                          pprints=self._pprints, verbose=self._verbose)

        self._threads_object_instances.append(inst)
        return inst

    @staticmethod
    def _handle_threads(scraper_instance):
        try:
            scraper_instance.search_loop()
        except RateLimitExceededException:
            sys.exit()

    @staticmethod
    def re_execute_main_program():
        command = [sys.executable, path.join(path.dirname(__file__), "scraper.py")]
        subprocess.run(command)
        sys.exit()

    def start_scraper(self) -> None:
        """
        Initiates the scraping process with or without multiple threads.

        If multiple threads are used, a signal handler is set up to handle KeyboardInterrupt
        (Ctrl+C) for graceful termination.

        Returns:
            None
        """

        if self._use_thread:
            try:
                for thread_index in range(self._no_of_threads):
                    scraper_instance = self._create_instance()
                    thread_creator = Thread(target=self._handle_threads, args=(scraper_instance,), daemon=True)
                    thread_creator.start()
                    self._running_threads.append(thread_creator)

                def signal_handler(_, __):
                    print("[**] Ctrl+C pressed. Closing threads...")
                    for thread_instance in self._threads_object_instances:
                        thread_instance.break_thread.set()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)

                while True:
                    time.sleep(.1)
                    if not self._running_threads:
                        print('[**] Rate limit exceed changing token')
                        new_file_content = TEMP_EXE.format(
                            file_name=f"{path.basename(__file__).replace('.py', '')}",
                            num_of_threads=self._no_of_threads,
                            tokens_list=self._git_token[1:]
                        )
                        with open(file="temp.py", mode='w') as file:
                            file.write(new_file_content)

                        command = [sys.executable, path.join(path.dirname(__file__), "temp.py")]
                        if self._git_token[1:]:
                            subprocess.run(command)
                            sys.exit()
                        else:
                            self.re_execute_main_program()

                    for running_thread in self._running_threads:
                        if not running_thread.is_alive():
                            self._running_threads.remove(running_thread)

            except Exception as e:
                print(f"An error occurred: {str(e)}")

        else:
            try:
                scraper_instance = self._create_instance()
                scraper_instance.search_loop()
            except KeyboardInterrupt:
                print("[**] Closing Program")


if __name__ == "__main__":
    obj = Scraper(number_of_threads=4, git_tokens=["token_1"])  # Provide list of github tokens or a single token
    obj.start_scraper()
