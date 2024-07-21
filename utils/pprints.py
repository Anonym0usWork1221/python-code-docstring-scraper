from platform import system as system_platform
from threading import active_count, Lock
from psutil import Process
from os.path import isfile
from os import system


class PPrints:
    """
    This class handles pretty-printing status messages and provides terminal-related functionalities.

    Args:
    - print_lock (Lock): A thread lock for printing synchronization.

    Attributes:
    - HEADER, BLUE, CYAN, GREEN, WARNING, RED, RESET: ANSI escape codes for text formatting.
    - _process: A Process instance for accessing memory information.
    - _print_lock: A lock for printing synchronization.
    - _log_file: The name of the log file for storing status messages.

    Methods:
    - clean_terminal(): Clears the terminal screen based on the platform.
    - pretty_print(current_repo, status, current_repo_id, logs): Prints formatted status messages.
    """

    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

    def __init__(self, print_lock: Lock = Lock()) -> None:
        """
        Initializes a new instance of the PPrints class.

        Args:
            print_lock (Lock, optional): A thread lock for printing synchronization. Defaults to Lock().
        """

        self._process = Process()
        self._print_lock = print_lock
        self._log_file = "logs.txt"

    @staticmethod
    def clean_terminal() -> str:
        """
        Clears the terminal screen based on the platform.
        Returns:
            str: The platform name.
        """

        if system_platform() == "Windows":
            system("cls")
        else:
            system("clear")
        return system_platform()

    def pretty_print(self, current_repo: str, status: str,
                     current_repo_id: str = "Calculating .....",
                     current_token: str = "Calculating...",
                     logs: bool = False) -> None:
        """
        Prints formatted status messages.
        Args:
            current_repo (str): The name of the current repository.
            status (str): The status message to be printed.
            current_repo_id (str, optional): The ID of the current repository. Defaults to "Calculating ...".
            current_token (str, optional): The current token. Defaults to "Calculating...".
            logs (bool, optional): Whether to include detailed logs. Defaults to False.
        """

        with self._print_lock:
            memory_info = self._process.memory_info()
            current_memory_usage = memory_info.rss / 1024 / 1024  # Convert bytes to megabytes
            non_log_msg = f"Current Repo: {current_repo}\n" \
                          f"Status: {status}\n" \
                          f"Current Repo: {current_repo}\n" \
                          f"Token: {current_token}\n" \
                          f"Current Repo ID: {current_repo_id}\n"

            log_msg = f"{self.GREEN}Platform: {self.clean_terminal()}\n" \
                      f"{self.CYAN}Developer: AbdulMoez\n" \
                      f"{self.GREEN}Scraper Version: 0.1\n" \
                      f"{self.WARNING}GitHub: github.com/Anonym0usWork1221\n" \
                      f"{self.BLUE}Current Repo: {current_repo}\n" \
                      f"{self.CYAN}Current Repo ID: {current_repo_id}\n" \
                      f"{self.GREEN}Token: {current_token}\n" \
                      f"{self.WARNING}Status: {status}\n" \
                      f"{self.GREEN}Output File: Sqlite3\n" \
                      f"{self.BLUE}Launched Multi Threads: {active_count() - 1}\n" \
                      f"{self.WARNING}MemoryUsageByScript: {current_memory_usage: .2f}MB\n" \
                      f"{self.RED}Warning: Don't open the output file while script is running\n{self.RESET}"
            print(log_msg)
            if logs:
                if isfile(self._log_file):
                    file_obj = open(self._log_file, "a")
                    file_obj.write(non_log_msg)
                    file_obj.close()
                else:
                    file_obj = open(self._log_file, "w")
                    file_obj.write(non_log_msg)
                    file_obj.close()


