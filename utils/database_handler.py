from sqlite3 import connect, Connection, Cursor
from os.path import abspath, isdir
from traceback import format_exc
from threading import Lock, Event
from datetime import datetime
from github import Github
from random import choice
from os import mkdir
import json


class JsonRecordHandler(object):
    """
    This class manages the record IDs of scraped repositories and handles JSON file operations.

    Args:
        - thread_lock (Lock): A thread lock for synchronization.
        - json_file_name (str): The name of the JSON file for storing record IDs.

    Methods:
        - dump_json(): Writes the record IDs to the JSON file.
        - create_git_instance(): Creates a new instance of the GitHub class with the next token.
        - _load_json(): Loads record IDs from the JSON file.
        - insertion_in_record_ids(new_id): Inserts a new record ID into the set.
    """

    def __init__(self, total_tokens: list, thread_lock=Lock(), json_file_name: str = "ids.json") -> None:
        """Initialize the instance of JsonRecordHandler class"""

        self._thread_lock = thread_lock
        self._json_file_name: str = json_file_name
        if not total_tokens:
            print("Github token is not provided")
            exit()
        self._total_tokens: list = total_tokens
        self.total_values = len(self._total_tokens)
        self.current_token: int = 1
        self._old_time = datetime.now()
        self._wait_token_reset: float = 80.0

        self.current_git_instance = Github(self._total_tokens[0])
        self.next_token: Event = Event()

        self.id_record = set()
        self._load_json()

    def dump_json(self) -> None:
        """
        Writes the record IDs to the JSON file.
        """

        with self._thread_lock:
            with open(self._json_file_name, 'w') as file:
                json.dump(list(self.id_record), file)

    def _load_json(self) -> None:
        """
        Loads record IDs from the JSON file.
        """

        try:
            with open(self._json_file_name, 'r') as file:
                data = json.load(file)
                self.id_record = set(data)
        except FileNotFoundError:
            with self._thread_lock:
                self.id_record = set()

    def insertion_in_record_ids(self, new_id: int) -> None:
        """
        Inserts a new record ID into the set.
        Args:
            new_id (int): The new record ID to be inserted.
        """

        with self._thread_lock:
            self.id_record.add(new_id)


class DataBaseHandler(object):
    """
    This class manages the SQLite database for storing Python code snippets with docstrings.

    Args:
        - thread_lock (Lock): A thread lock for synchronization.
        - data_base_path (str): The path where the database file will be stored.
        - data_base_file_name (str): The name of the SQLite database file.

    Methods:
        - create_connection(): Creates a connection to the SQLite database and returns a connection and cursor.
        - _create_database(): Initializes the database schema.
        - insert_data(functions_data, classes_data, source): Inserts Python code snippets with docstrings into the
                                                             database.
    """

    def __init__(self,
                 thread_lock=Lock(),
                 data_base_path: str = "./database",
                 data_base_file_name: str = "python_code_snippets.db",
                 ) -> None:
        """Initialize the instance of DataBaseHandler class"""

        self._data_base_path = abspath(data_base_path)
        self._data_file_name = data_base_file_name
        self._thread_lock = thread_lock
        self._doc_string_texts = [
            "write a docstring for this ",
            "can you generate documentation for this code ",
            "provide documentation for this ",
            "please write a docstring explaining this code ",
            "generate comments for this Python code ",
            "create documentation for this code snippet ",
            "add descriptive comments to this code ",
            "explain the purpose of this code with a docstring ",
            "generate documentation comments for this ",
            "help me understand this code with a docstring ",
            "write me some comments for this code ",
            "provide details about this code with a docstring ",
            "add explanations to this Python script ",
            "can you describe this code with a docstring ",
            "write a helpful docstring for this function ",
            "generate documentation for this Python file ",
            "add comments to clarify this code ",
            "create a docstring for this Python function ",
            "explain the functionality of this code with a docstring ",
            "write me documentation for this Python class ",
            "help me document this piece of code ",
            "provide details about this Python module ",
            "generate a docstring for this Python method ",
            "add comments to make this code more understandable ",
            "create a docstring explaining the logic of this code ",
            "write me a description for this Python code ",
            "generate comments to document this script ",
            "add a docstring to explain this code ",
            "help me with the documentation of this code ",
            "write a docstring to describe this function ",
            "generate documentation to explain this code ",
            "provide insights into this Python code with a docstring ",
            "add comments for better understanding of this code ",
            "create a docstring for this Python class method ",
            "write me some comments to annotate this code ",
            "generate documentation comments for this Python file ",
            "add descriptive comments to clarify this code ",
            "help me understand the purpose of this code with a docstring ",
            "write a docstring to detail the functionality of this code ",
            "generate comments to document the logic of this code ",
            "add explanations to this Python script with a docstring ",
            "create documentation for this Python function ",
            "explain the behavior of this code with a docstring ",
            "write me documentation comments for this Python module ",
            "provide details about this Python function with a docstring ",
            "generate documentation for this Python class ",
            "add comments to explain the flow of this code ",
            "help me document this Python class ",
            "write a docstring to describe the purpose of this code ",
            "generate documentation to explain the functionality of this code ",
            "add comments for better understanding of this Python script ",
            "create a docstring for this Python module ",
            "write me some comments to annotate this Python code ",
            "generate documentation comments for this Python method ",
            "add descriptive comments to clarify this Python code ",
            "help me understand the logic of this code with a docstring ",
            "write a docstring to detail the behavior of this Python code ",
            "generate comments to document the purpose of this code ",
            "add explanations to this Python function with a docstring ",
            "create documentation for this Python class method ",
            "explain the structure of this code with a docstring ",
            "write me documentation comments for this Python file ",
            "provide details about this Python script with a docstring ",
            "generate documentation for this Python function ",
            "add comments to explain the functionality of this code ",
            "help me document this Python module ",
            "write a docstring to describe the logic of this Python code ",
            "generate documentation to explain the purpose of this code ",
            "add comments for better understanding of this Python function ",
            "create a docstring for this Python class ",
            "write me some comments to annotate this Python script ",
            "generate documentation comments for this Python class method ",
            "add descriptive comments to clarify this Python function ",
            "help me understand the behavior of this code with a docstring ",
            "write a docstring to detail the structure of this Python code ",
            "generate comments to document the behavior of this Python code ",
            "add explanations to this Python module with a docstring ",
            "create documentation for this Python class ",
            "explain the functionality of this code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python class with a docstring ",
            "generate documentation for this Python script ",
            "add comments to explain the purpose of this Python code ",
            "help me document this Python class method ",
            "write a docstring to describe the flow of this Python code ",
            "generate documentation to explain the logic of this Python code ",
            "add comments for better understanding of this Python module ",
            "create a docstring for this Python function ",
            "write me some comments to annotate this Python class ",
            "generate documentation comments for this Python file ",
            "add descriptive comments to clarify this Python module ",
            "help me understand the purpose of this Python function with a docstring ",
            "write a docstring to detail the functionality of this Python class ",
            "generate comments to document the structure of this Python code ",
            "add explanations to this Python code with a docstring ",
            "create documentation for this Python module ",
            "explain the behavior of this Python code with a docstring ",
            "write me documentation comments for this Python script ",
            "provide details about this Python module with a docstring ",
            "generate documentation for this Python class method ",
            "add comments to explain the flow of this Python code ",
            "help me document this Python function ",
            "write a docstring to describe the purpose of this Python module ",
            "generate documentation to explain the functionality of this Python class ",
            "add comments for better understanding of this Python class method ",
            "create a docstring for this Python script ",
            "write me some comments to annotate this Python function ",
            "generate documentation comments for this Python class ",
            "add descriptive comments to clarify this Python class method ",
            "help me understand the logic of this Python code with a docstring ",
            "write a docstring to detail the behavior of this Python function ",
            "generate comments to document the purpose of this Python module ",
            "add explanations to this Python script with a docstring ",
            "create documentation for this Python class ",
            "explain the structure of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python script with a docstring ",
            "generate documentation for this Python module ",
            "add comments to explain the functionality of this Python class ",
            "help me document this Python class ",
            "write a docstring to describe the logic of this Python class method ",
            "generate documentation to explain the purpose of this Python function ",
            "add comments for better understanding of this Python script ",
            "create a docstring for this Python class ",
            "write me some comments to annotate this Python module ",
            "generate documentation comments for this Python class method ",
            "add descriptive comments to clarify this Python function ",
            "help me understand the behavior of this Python code with a docstring ",
            "write a docstring to detail the structure of this Python class ",
            "generate comments to document the behavior of this Python class method ",
            "add explanations to this Python module with a docstring ",
            "create documentation for this Python class ",
            "explain the functionality of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python class with a docstring ",
            "generate documentation for this Python script ",
            "add comments to explain the purpose of this Python code ",
            "help me document this Python class method ",
            "write a docstring to describe the flow of this Python class ",
            "generate documentation to explain the logic of this Python class method ",
            "add comments for better understanding of this Python module ",
            "create a docstring for this Python function ",
            "write me some comments to annotate this Python class method ",
            "generate documentation comments for this Python file ",
            "add descriptive comments to clarify this Python module ",
            "help me understand the purpose of this Python function with a docstring ",
            "write a docstring to detail the functionality of this Python class ",
            "generate comments to document the structure of this Python code ",
            "add explanations to this Python code with a docstring ",
            "create documentation for this Python module ",
            "explain the behavior of this Python code with a docstring ",
            "write me documentation comments for this Python script ",
            "provide details about this Python module with a docstring ",
            "generate documentation for this Python class method ",
            "add comments to explain the flow of this Python code ",
            "help me document this Python function ",
            "write a docstring to describe the purpose of this Python module ",
            "generate documentation to explain the functionality of this Python class ",
            "add comments for better understanding of this Python class method ",
            "create a docstring for this Python script ",
            "write me some comments to annotate this Python function ",
            "generate documentation comments for this Python class ",
            "add descriptive comments to clarify this Python class method ",
            "help me understand the logic of this Python code with a docstring ",
            "write a docstring to detail the behavior of this Python function ",
            "generate comments to document the purpose of this Python module ",
            "add explanations to this Python script with a docstring ",
            "create documentation for this Python class ",
            "explain the structure of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python script with a docstring ",
            "generate documentation for this Python module ",
            "add comments to explain the functionality of this Python class ",
            "help me document this Python class ",
            "write a docstring to describe the logic of this Python class method ",
            "generate documentation to explain the purpose of this Python function ",
            "add comments for better understanding of this Python script ",
            "create a docstring for this Python class ",
            "write me some comments to annotate this Python module ",
            "generate documentation comments for this Python class method ",
            "add descriptive comments to clarify this Python function ",
            "help me understand the behavior of this Python code with a docstring ",
            "write a docstring to detail the structure of this Python class ",
            "generate comments to document the behavior of this Python class method ",
            "add explanations to this Python module with a docstring ",
            "create documentation for this Python class ",
            "explain the functionality of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python class with a docstring ",
            "generate documentation for this Python script ",
            "add comments to explain the purpose of this Python code ",
            "help me document this Python class method ",
            "write a docstring to describe the flow of this Python class ",
            "generate documentation to explain the logic of this Python class method ",
            "add comments for better understanding of this Python module ",
            "create a docstring for this Python function ",
            "write me some comments to annotate this Python class method ",
            "generate documentation comments for this Python file ",
            "add descriptive comments to clarify this Python module ",
            "help me understand the purpose of this Python function with a docstring ",
            "write a docstring to detail the functionality of this Python class ",
            "generate comments to document the structure of this Python code ",
            "add explanations to this Python code with a docstring ",
            "create documentation for this Python module ",
            "explain the behavior of this Python code with a docstring ",
            "write me documentation comments for this Python script ",
            "provide details about this Python module with a docstring ",
            "generate documentation for this Python class method ",
            "add comments to explain the flow of this Python code ",
            "help me document this Python function ",
            "write a docstring to describe the purpose of this Python module ",
            "generate documentation to explain the functionality of this Python class ",
            "add comments for better understanding of this Python class method ",
            "create a docstring for this Python script ",
            "write me some comments to annotate this Python function ",
            "generate documentation comments for this Python class ",
            "add descriptive comments to clarify this Python class method ",
            "help me understand the logic of this Python code with a docstring ",
            "write a docstring to detail the behavior of this Python function ",
            "generate comments to document the purpose of this Python module ",
            "add explanations to this Python script with a docstring ",
            "create documentation for this Python class ",
            "explain the structure of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python script with a docstring ",
            "generate documentation for this Python module ",
            "add comments to explain the functionality of this Python class ",
            "help me document this Python class ",
            "write a docstring to describe the logic of this Python class method ",
            "generate documentation to explain the purpose of this Python function ",
            "add comments for better understanding of this Python script ",
            "create a docstring for this Python class ",
            "write me some comments to annotate this Python module ",
            "generate documentation comments for this Python class method ",
            "add descriptive comments to clarify this Python function ",
            "help me understand the behavior of this Python code with a docstring ",
            "write a docstring to detail the structure of this Python class ",
            "generate comments to document the behavior of this Python class method ",
            "add explanations to this Python module with a docstring ",
            "create documentation for this Python class ",
            "explain the functionality of this Python code with a docstring ",
            "write me documentation comments for this Python function ",
            "provide details about this Python class with a docstring ",
            "generate documentation for this Python script ",
            "add comments to explain the purpose of this Python code ",
            "help me document this Python class method ",
            "write a docstring to describe the flow of this Python class ",
            "generate documentation to explain the logic of this Python class method ",
            "add comments for better understanding of this Python module ",
            "create a docstring for this Python function ",
            "write me some comments to annotate this Python class method ",
            "generate documentation comments for this Python file ",
            "add descriptive comments to clarify this Python module "]
        if not isdir(self._data_base_path):
            mkdir(self._data_base_path)

        self._create_database()

    def create_connection(self) -> tuple[Connection, Cursor]:
        """
        Creates a connection to the SQLite database and returns a connection and cursor.

        Returns:
            tuple[Connection, Cursor]: A tuple containing the database connection and cursor.
        """

        with self._thread_lock:
            database_connection = connect(f"{self._data_base_path}/{self._data_file_name}")
            cursor = database_connection.cursor()
            return database_connection, cursor

    def _create_database(self) -> None:
        """
        Initializes the database schema.
        """

        database_connection, cursor = self.create_connection()
        cursor.execute('''CREATE TABLE IF NOT EXISTS snippets (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           title TEXT,
                           code TEXT,
                           source TEXT
                           )
                   ''')
        database_connection.commit()
        database_connection.close()

    def insert_data(self, functions_data: list, classes_data: list, source: str, file_content: str) -> bool:
        """
        Inserts Python code snippets with docstrings into the database.

        Args:
            functions_data (list): List of tuples containing docstrings, function definitions, and function
                                   without docstring.
            classes_data (list): List of tuples containing docstrings, class definitions, and class without docstring.
            source (str): The source of the code snippets.
            file_content (str): The content of the entire file.
        Returns:
            bool: True if the insertion is successful, False otherwise.
        """
        database_connection, cursor = self.create_connection()
        try:
            for doc_func in functions_data:
                docstring = doc_func[0].strip()  # doc string
                if not docstring:
                    continue
                function_content = f"<code>\n{doc_func[1].strip()}\n</code>"  # with doc string
                function_content_without_doc_sting = doc_func[2].strip()  # without doc string
                # For title code generation system
                with self._thread_lock:
                    cursor.execute("INSERT INTO snippets (title, code, source) VALUES (?, ?, ?)",
                                   (docstring, f"<code>\n{function_content_without_doc_sting}\n</code>", source))

                    # For writing doc strings
                    cursor.execute("INSERT INTO snippets (title, code, source) VALUES (?, ?, ?)",
                                   (f"{choice(self._doc_string_texts)}\n{function_content_without_doc_sting}",
                                    function_content, source))

            classes_docs: str = ""
            for doc_func in classes_data:
                docstring = doc_func[0].strip()  # doc string
                if not docstring:
                    continue
                classes_docs += f"{docstring}\n"
                function_content = f"<code>\n{doc_func[1].strip()}\n</code>"  # with doc string
                function_content_without_doc_sting = doc_func[2].strip()  # without doc string
                # For title code generation system of class-based code
                with self._thread_lock:
                    cursor.execute("INSERT INTO snippets (title, code, source) VALUES (?, ?, ?)",
                                   (docstring,  f"<code>\n{function_content_without_doc_sting}\n</code>", source))

                    # For writing doc strings
                    cursor.execute("INSERT INTO snippets (title, code, source) VALUES (?, ?, ?)",
                                   (f"{choice(self._doc_string_texts)}\n{function_content_without_doc_sting}",
                                    function_content, source))

            classes_docs = classes_docs.strip()
            if classes_docs:
                # For complete file name with classes docs as a title
                with self._thread_lock:
                    cursor.execute("INSERT INTO snippets (title, code, source) VALUES (?, ?, ?)",
                                   (classes_docs, f"<code>\n{file_content}\n</code>", source))

        except Exception as e:
            traceback_str = format_exc()
            print(traceback_str + "\n" + str(e))
            return False
        with self._thread_lock:
            database_connection.commit()
            database_connection.close()
        return True
