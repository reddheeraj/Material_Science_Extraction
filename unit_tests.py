import click
from query_db import query_relevant_chunks
from store_data import consolidate_to_json
from LLM import refine_with_llm
from index_files import main_function
from multiprocessing import Queue


# Test query_relevant_chunks
@click.command("query")
@click.option("--query", default="test query", help="Query to search for.")
def test_query_relevant_chunks(query):
    click.echo("Testing query_relevant_chunks...")
    click.echo(f"Query: {query}")
    documents, metadatas = query_relevant_chunks(query)
    click.echo(f"Documents: {documents}")
    click.echo(f"Metadatas: {metadatas}")


# Test consolidate_to_json
@click.command("store")
def test_consolidate_to_json():
    click.echo("Testing consolidate_to_json...")
    results = [
        {
            "source": "source1",
            "chunk_id": 1,
            "properties": "{\"Alloy\": \"Al\", \"Properties\": {\"some key\": \"some value\"}}"
        }
    ]
    output_file = "tests/output.json"
    consolidate_to_json(results, output_file)
    click.echo(f"Data written to {output_file}")


# # Test refine_with_llm
# @click.command("llm")
# def test_refine_with_llm():
#     click.echo("Testing refine_with_llm...")
#     chunks = ["chunk1", "chunk2"]
#     results = refine_with_llm(chunks)
#     click.echo(f"Refined Results: {results}")


# Test pdf_file_processor
@click.command("indexing")
@click.option("--folder", default="./papers_test", help="Path to the folder containing PDF files.")
def test_data_indexing(folder):
    """
    Make sure to edit the DB_PATH in config.py to point to the correct database file,
    and the COLLECTION_NAME to the desired collection name for testing.
    """
    click.echo("Testing index_files.py...")
    main_function(folder, 2, Queue())



# Group commands
@click.group()
def cli():
    """CLI for testing individual functions."""
    pass


cli.add_command(test_query_relevant_chunks)
cli.add_command(test_consolidate_to_json)
# cli.add_command(test_refine_with_llm)
cli.add_command(test_data_indexing)

if __name__ == "__main__":
    cli()
