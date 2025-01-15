# **Material Science Data Extraction**

A Langchain-based RAG to extract details from research papers and present them in the required format.

## **Overview**

This project uses Retrieval-Augmented Generation (RAG) to efficiently process research papers and extract relevant information. By leveraging **LangChain**, **Ollama**, and **ChromaDB**, the system allows users to index PDFs, query specific keywords or topics, and refine results using LLMs.

## Features

- Extract and process research papers in PDF format.
- Index content using embeddings and store it in a vector database.
- Query the indexed documents for specific topics or keywords.
- Refine results into structured JSON format.
- Consolidate results into CSV or JSON files for analysis.
- Detailed Logs of every step to help while debugging issues.

## Installation and Setup
### Basics

> Clone the project into your device/environment. `git clone <https://github.com/taugroup/Material-Science-Data-Extraction.git>`

> Install the required packages using: `pip install -r requirements.txt`

> Install **Ollama** from [here](https://ollama.com/download) and make sure to run the application. The local instance will run in the background.

> Run `ollama pull nomic-embed-text` and `ollama pull <llm model name>` in a terminal to set up the embedding and llm models on your device.

> Research papers are stored in a directory named **papers**.

## Folder Structure
```bash
.
├── chromadb/
├── Studies/
│    ├── Case1
│    └── Case2/
│         ├── Outputs/
│         │    └── output1.json
│         ├── Papers/
│         │    ├── Paper 1.pdf
│         │    └── paper 2.pdf
│         └── Summary/
│              ├── processed_data.json
│              └── summary.txt
├── ui_functions/
│   ├── dashboard.py
│   ├── query_results.py
│   ├── upload_n_process.py
│   └── view_results.py
│
├── config.py
├── db_connection.py
├── index_files.py
├── LLM.py
├── query_db.py
├── store_data.py
├── unit_tests.py
├── logger.py
└── GUI.py
```

1. The **chromadb** folder is the database folder where the PDFs from **Studies/Case/Papers/** are embedded and stored in a vector database.
2. The Data Loading Unit is separated into a group of folders called **Studies**. There are multiple **Case** folders inside **Studies**, each **w**ith its own **Outputs** and **Papers** folders.
3. The **Papers** folder will contain research paper PDFs relevant to that **Case**. So you will be able to query relevant papers based on the configurations you set in the **config.py** file.
4. The **Summary** folder will contain a **summary.txt** file and a **processed_data.json** file which contain information needed to display in the dashboard which is run by the **dashboard.py**.
5. The **db_connection.py** file contains a Singleton design pattern-based code to connect to the vector database to help retrieve text embeds.
6. The **index_files.py** file is used to index and store the research papers in our database.
7. The **LLM.py** file contains code relevant to connecting and querying an LLM to generate answers to our queries.
8. The **query_db.py** file contains code that is used to query the database, use them to talk to an LLM and generate structured answers, parse them properly, and store them in the **Outputs** folder of that **Case**.
9. The **store_data.py** includes code to parse the output generated from an LLM and store them in JSON format.
10. The **unit_tests.py** file can be executed while development changes, to test whether individual functions are doing as expected or not.
11. The **logger.py** file contains code that helps with logging every step of the process. This will help to backtrack an error while debugging.
12. The **GUI.py** helps by providing a smooth user interface to handle the process without having to enter commands in the terminal.

## Configuration

All configurations and Static variables are stored in the **config.py** file. Feel free to modify them based on your considerations.

## Usage Guide

### User Interface

Run the below command in the terminal, in the root directory of the project, to generate a user interface that helps run processes without writing commands or code.

`streamlit run GUI.py`

### Indexing Documents

Run the below command in the terminal, in the **root directory** of the project:

`python index_files.py`

 This breaks the documents in the papers folder into chunks and stores them in the database. These chunks will later be retrieved while querying

### Querying

Run the below code in the terminal, in the **root directory** of the project:

`python query_db.py --query <input_your_query_or_keyword(s)_here>`

This command will help you get results for your query. It will store the results in JSON format in the **Outputs** folder once the LLM is done refining the answer.

## Project Walkthrough

Info about the flow of the code and what each important function does.

## Troubleshooting

The **unit_tests.py** file has the necessary tests to run for different functions individually. Please follow the below instructions:

- For _Query testing_: `python unit_tests.py query --query "yield strength"`

- For _Indexing testing_: `python unit_tests.py indexing --folder "./papers_test"`

- For _Data Storage to JSON testing_: `python unit_tests.py store`

## Future Enhancements

Info here
