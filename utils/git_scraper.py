from github.Repository import Repository

from utils.database_handler import DataBaseHandler, JsonRecordHandler
from github.GithubException import RateLimitExceededException
from github import PaginatedList
from requests.exceptions import Timeout
from traceback import format_exc
from pprint import pprint
from threading import Lock, Event
from utils.pprints import PPrints
from textwrap import fill
import time
import sys
import ast
import re


class GitScraper(object):
    """
    This class is responsible for scraping Python code snippets with docstrings from GitHub repositories.

    Args:
        - git_instance (Github): A GitHub instance for authentication.
        - json_handler (JsonRecordHandler): An instance of JsonRecordHandler for managing record IDs.
        - thread_lock (Lock): A thread lock to handle synchronization between threads.
        - search_query (str): The GitHub search query used to filter repositories.
        - id_record_file (str): The file name for storing scraped repository IDs.
        - db_commit_index (int): The number of records after which the database is committed.
        - width_for_wrap (int): The width used for wrapping docstrings.
        - pprints (PPrints): An instance of PPrints for pretty-printing status messages.
        - verbose (bool): Whether to print verbose status messages.
        - data_base_path (str): The path where the SQLite database will be stored.
        - data_base_file_name (str): The name of the SQLite database file.

    Attributes:
        - break_thread (Event): An event to signal thread termination.

    Methods:
        - py_class_parser(file_content): Parses Python class definitions and their docstrings.
        - py_function_parser(file_content): Parses Python function definitions and their docstrings.
        - get_repos(): Retrieves a list of repositories based on the search query.
        - get_single_repo(repo_name): Retrieves a single repository by name or ID.
        - get_sub_dirs(raw_contents, repo, branch): Retrieves subdirectories within a repository.
        - get_python_content_files(raw_contents, repo, branch, sub_dirs): Retrieves Python content files within a repository.
        - get_file_content(file): Retrieves the content of a file.
        - search_loop(): Initiates the repository scraping process in a loop.
        - single_loop(): Initiates the scraping process for a single repository.
        - _pprint_override(status, info_type, logs): Prints formatted status messages.
    """

    _SUB_DOC_PATTERN = r'\"\"\"[\s\S]*?\"\"\"'
    _info_types: dict = {
        1: "INFO",
        2: "WARNING",
        3: "ERROR"
    }

    def __init__(self,
                 json_handler: JsonRecordHandler,
                 thread_lock: Lock = Lock(),
                 search_query: str = "language:python",
                 id_record_file: str = "ids.json",
                 db_commit_index: int = 1500,
                 width_for_wrap: int = 70,
                 pprints: PPrints = PPrints(),
                 verbose: bool = True,
                 data_base_path: str = "./database",
                 data_base_file_name: str = "python_code_snippets.db",
                 ) -> None:
        """
        Initializes a new instance of the GitScraper class.

        Args:
            json_handler (JsonRecordHandler): An instance of JsonRecordHandler for managing record IDs.
            thread_lock (Lock, optional): A thread lock to handle synchronization between threads. Defaults to Lock().
            search_query (str, optional): The GitHub search query used to filter repositories.
                                          Defaults to "language:python".
            id_record_file (str, optional): The file name for storing scraped repository IDs. Defaults to "ids.json".
            db_commit_index (int, optional): The number of records after which the database is committed.
                                             Defaults to 1500.
            width_for_wrap (int, optional): The width used for wrapping docstrings. Defaults to 70.
            pprints (PPrints, optional): An instance of PPrints for pretty-printing status messages.
                                         Defaults to PPrints().
            verbose (bool, optional): Whether to print verbose status messages. Defaults to True.
            data_base_path (str, optional): The path where the SQLite database will be stored.
                                            Defaults to "./database".
            data_base_file_name (str, optional): The name of the SQLite database file.
                                                 Defaults to "python_code_snippets.db".
        """

        # Customizable variables
        self._search_query: str = search_query
        self._id_records_file: str = id_record_file
        self._thread_lock = thread_lock
        self._db_commit_index: int = db_commit_index
        self._json_handler: JsonRecordHandler = json_handler
        self._wrap_width: int = width_for_wrap
        self._pprints = pprints
        self._verbose = verbose
        self.break_thread = Event()

        # Script Customizable variables
        self._current_repo = "Calculating ....."
        self._current_repo_id = "Calculating ....."
        self._database_handler = DataBaseHandler(thread_lock=self._thread_lock, data_base_path=data_base_path,
                                                 data_base_file_name=data_base_file_name)

    def _pprint_override(self, status, info_type: int = 1, logs: bool = False) -> None:
        """
        Prints formatted status messages.

        Args:
            status (str): The status message to be printed.
            info_type (int, optional): The type of information (INFO, WARNING, ERROR). Defaults to 1.
            logs (bool, optional): Whether to include detailed logs. Defaults to False.
        """

        if self._verbose:
            self._pprints.pretty_print(current_repo=self._current_repo,
                                       status=f"{self._info_types[info_type]}: {status}",
                                       current_repo_id=str(self._current_repo_id),
                                       current_token=f"Current: {self._json_handler.current_token}, "
                                                     f"ToTal: {self._json_handler.total_values}",
                                       logs=logs)

    def py_class_parser(self, file_content: str) -> list:
        """
        Parses Python class definitions and their docstrings.
        Args:
            file_content (str): The content of the Python file.
        Returns:
            list: A list of tuples containing formatted docstrings, class definition, and class without docstring.
        """

        classes_with_docstrings = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        class_docstring = ast.unparse(node.body[0])
                        class_without_docstring = re.sub(self._SUB_DOC_PATTERN, '', ast.unparse(node))
                        replace_sting_to_correct_intent = [line.strip() for line in class_docstring.split("\n")]
                        extensive_docs_strings = "\n".join(replace_sting_to_correct_intent).strip('"').strip("'")
                        formatted_doc_string = fill(extensive_docs_strings, width=self._wrap_width, initial_indent='',
                                                    subsequent_indent=' ' * 8).strip()
                        classes_with_docstrings.append((formatted_doc_string,
                                                        ast.unparse(node), class_without_docstring))
        except SyntaxError:
            # Raise due to python-2 version code
            ...
        return classes_with_docstrings

    def py_function_parser(self, file_content: str) -> list:
        """
        Parses Python function definitions and their docstrings.

        Args:
            file_content (str): The content of the Python file.

        Returns:
            list: A list of tuples containing formatted docstrings, function definition, and function without docstring.
        """

        functions_with_docstrings = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        function_doc_string = ast.unparse(node.body[0])
                        function_without_docstring = re.sub(self._SUB_DOC_PATTERN, '', ast.unparse(node))
                        replace_sting_to_correct_intent = [line.strip() for line in function_doc_string.split("\n")]
                        extensive_docs_strings = "\n".join(replace_sting_to_correct_intent).strip('"').strip("'")
                        formatted_doc_string = fill(extensive_docs_strings, width=self._wrap_width, initial_indent='',
                                                    subsequent_indent=' ' * 8).strip()
                        functions_with_docstrings.append(
                            (formatted_doc_string, ast.unparse(node), function_without_docstring)
                        )
        except SyntaxError:
            # Raise due to python-2 version code
            ...
        return functions_with_docstrings

    def get_repos(self) -> list[Repository]:
        """
        Retrieves a list of repositories based on the search query.
        Returns:
            list[Repository]: A Repository list of repositories.
        """

        try:
            # start_page: int = int((len(self._json_handler.id_record) / 30) + 1)
            search_repos = self._json_handler.current_git_instance.search_repositories(
                self._search_query
            )
            # search_repos = search_repos.get_page(start_page)
        except Timeout:
            traceback_text = format_exc()
            self._pprint_override(status=f"Look Like no internet connection Error: {traceback_text}", logs=True,
                                  info_type=3)
            sys.exit()
        except RateLimitExceededException:
            sys.exit()
        return search_repos

    def get_single_repo(self, repo_name) -> PaginatedList:
        """
        Retrieves a single repository by name or ID.
        Args:
            repo_name: The name or ID of the repository.
        Returns:
            PaginatedList: A paginated list containing the specified repository.
        """

        try:
            repo = self._json_handler.current_git_instance.get_repo(full_name_or_id=repo_name)
        except Timeout:
            traceback_text = format_exc()
            self._pprint_override(status=f"Look Like no internet connection Error: {traceback_text}", logs=True,
                                  info_type=3)
            sys.exit()
        except RateLimitExceededException:
            sys.exit()
        return repo

    def get_sub_dirs(self, raw_contents, repo, branch) -> list:
        """
        Retrieves subdirectories within a repository.

        Args:
            raw_contents: The raw contents of the repository.
            repo: The GitHub repository.
            branch: The default branch of the repository.

        Returns:
            list: A list of subdirectories within the repository.
        """

        sub_dirs = []
        queue = raw_contents.copy()
        while queue:
            current_directory = queue.pop(0)
            if current_directory.type == "dir" and not current_directory.path.startswith("."):
                sub_dirs.append(current_directory)
                try:
                    new_contents = repo.get_contents(path=current_directory.path, ref=branch)
                except Timeout:
                    traceback_text = format_exc()
                    self._pprint_override(status=f"Look Like no internet connection Error: {traceback_text}", logs=True,
                                          info_type=3)
                    sys.exit()
                except RateLimitExceededException:
                    sys.exit()
                queue.extend(new_contents)
        return sub_dirs

    def get_python_content_files(self, raw_contents, repo, branch, sub_dirs) -> list:
        """
        Retrieves Python content files within a repository.
        Args:
            raw_contents: The raw contents of the repository.
            repo: The GitHub repository.
            branch: The default branch of the repository.
            sub_dirs: A list of subdirectories within the repository.
        Returns:
            list: A list of Python content files within the repository.
        """

        contents = []
        # Getting Content for raw_contents
        for content in raw_contents:
            if content.path.endswith(".py") and not content.path.startswith("setup"):
                contents.append(content)

        # Loop through all the sub_dirs for their content
        for directory in sub_dirs:
            try:
                directory_contents = repo.get_contents(path=directory.path, ref=branch)
            except Timeout:
                traceback_text = format_exc()
                self._pprint_override(status=f"Look Like no internet connection Error: {traceback_text}", logs=True,
                                      info_type=3)
                sys.exit()
            except RateLimitExceededException:
                sys.exit()

            for content in directory_contents:
                if content.path.endswith(".py") and not content.path.startswith("setup"):
                    contents.append(content)
        return contents

    def get_file_content(self, file) -> str:
        """
        Retrieves the content of a file.
        Args:
            file: The file object.
        Returns:
            str: The content of the file.
        """
        try:
            file_content = file.decoded_content.decode("utf-8")
        except Timeout:
            traceback_text = format_exc()
            self._pprint_override(status=f"Look Like no internet connection Error: {traceback_text}", logs=True,
                                  info_type=3)
            sys.exit()
        except RateLimitExceededException:
            sys.exit()

        return file_content

    def search_loop(self) -> None:
        """
        Initiates the repository scraping process in a loop.
        """

        self._pprint_override(status="Getting REPOS")
        repos: list[Repository] = self.get_repos()
        # current_db_commit_index = 0
        for repo in repos:
            if self.break_thread.is_set():
                break
            if repo.id in self._json_handler.id_record:
                time.sleep(1)
                continue
            self._json_handler.insertion_in_record_ids(new_id=repo.id)

            source = repo.html_url
            branch = repo.default_branch
            self._current_repo = repo.name
            self._current_repo_id = repo.id
            self._pprint_override(status="Getting raw_contents")
            try:
                with self._thread_lock:
                    raw_contents = repo.get_contents(ref=branch, path="")
            except RateLimitExceededException:
                sys.exit()

            self._pprint_override(status="Getting sub_dirs")
            sub_dirs = self.get_sub_dirs(raw_contents, repo, branch)
            self._pprint_override(status="Getting content_files")
            contents_files = self.get_python_content_files(raw_contents, repo, branch, sub_dirs)
            self._pprint_override(status="Getting files data and storing in database")
            for content_file in contents_files:
                if self.break_thread.is_set():
                    break
                file_content = self.get_file_content(content_file)
                doc_functions = self.py_function_parser(file_content)
                doc_classes = self.py_class_parser(file_content)
                if doc_functions or doc_classes:
                    self._database_handler.insert_data(functions_data=doc_functions,
                                                       classes_data=doc_classes,
                                                       source=source,
                                                       file_content=file_content)
            self._json_handler.dump_json()
            # current_db_commit_index += 1

    def single_loop(self) -> None:
        """
        Initiates the scraping process for a single repository.
        """
        self._pprint_override(status="Getting REPO")
        repo = self.get_single_repo("Anonym0usWork1221/android-memorytool")
        branch = repo.default_branch
        source = repo.html_url
        self._current_repo = repo.name
        self._current_repo_id = repo.id
        self._pprint_override(status="Getting raw_contents")
        raw_contents = repo.get_contents(ref=branch, path="")
        self._pprint_override(status="Getting sub_dirs")
        sub_dirs = self.get_sub_dirs(raw_contents, repo, branch)
        self._pprint_override(status="Getting content_files")
        contents_files = self.get_python_content_files(raw_contents, repo, branch, sub_dirs)
        self._pprint_override(status="Getting files data and storing in database")
        for content_file in contents_files:
            if self.break_thread.is_set():
                break
            file_content = self.get_file_content(content_file)
            doc_functions = self.py_function_parser(file_content)
            doc_classes = self.py_class_parser(file_content)
            if doc_functions or doc_classes:
                self._database_handler.insert_data(functions_data=doc_functions,
                                                   classes_data=doc_classes, source=source,
                                                   file_content=file_content)

