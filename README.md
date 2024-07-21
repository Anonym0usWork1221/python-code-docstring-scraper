# GitHub Python Code Scraper

This project is a GitHub scraper designed to collect Python code from repositories, focusing on code that includes docstrings in functions and classes. The collected data is used to create an extensive dataset for the **JaraConverse** LLM model created by **Abdul Moez**.

 *  Date   : 2024/07/22
 *  Author : **__Abdul Moez__** & **__Hammad Hussain__**
 *  Version : 0.1
 *  Used For: JaraConverse Coding dataset creation


 MIT License  
 Copyright (c) 2024 AbdulMoez

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Ethical Considerations](#ethical-considerations)
- [Contributing](#contributing)
- [License](#license)

## Overview

The GitHub Python Code Scraper automates the process of searching for and scraping Python repositories from GitHub. It focuses on extracting code snippets that contain docstrings, ensuring that the dataset includes well-documented code. The scraper supports multithreading and handles GitHub API rate limits.

## Features

- **Multi-threaded Scraping**: Utilizes multiple threads to speed up the scraping process.
- **Rate Limit Handling**: Automatically switches GitHub tokens when rate limits are reached.
- **Customizable Search Queries**: Allows specifying custom GitHub search queries.
- **Database Storage**: Stores the scraped data in an SQLite database.
- **Verbose Logging**: Provides detailed status messages during the scraping process.

## Installation

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage

To start the scraper, run the following command:

```bash
python scraper.py
```

### Example

```python
from scraper import Scraper

# Initialize the Scraper object
scraper = Scraper(
    search_query="language:python pushed:<2023-01-01",
    git_tokens=["your_github_token1", "your_github_token2"],
    number_of_threads=4
)

# Start the scraping process
scraper.start_scraper()
```

## Configuration

You can customize the scraper's behavior using the following parameters:

- `search_query`: GitHub search query used to filter repositories.
- `git_tokens`: List of GitHub personal access tokens for authentication.
- `id_record_file`: File name for storing scraped repository IDs.
- `db_commit_index`: Number of records after which the database is committed.
- `width_for_wrap`: Width used for wrapping docstrings.
- `verbose`: Whether to print verbose status messages.
- `use_threads`: Whether to use multiple threads for scraping.
- `number_of_threads`: The number of threads to use for scraping.
- `data_base_path`: Path where the SQLite database will be stored.
- `data_base_file_name`: Name of the SQLite database file.

## Ethical Considerations

When using this scraper, it is essential to adhere to GitHub's terms of service and respect the rights of repository owners. Follow these guidelines to ensure ethical use:

1. **Obtain Permission**: Ensure you have permission to scrape and use the data from public repositories.
2. **Respect Rate Limits**: Be mindful of GitHub's rate limits and avoid excessive requests that could impact the service for others.
3. **Respect Licensing**: Check the licenses of the repositories you scrape and comply with their terms.
4. **Data Privacy**: Avoid scraping personal data or sensitive information from repositories.

# Contributors

<a href = "https://github.com/Anonym0usWork1221/python-code-docstring-scraper/graphs/contributors">
  <img src = "https://contrib.rocks/image?repo=Anonym0usWork1221/python-code-docstring-scraper"/>
</a>

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
