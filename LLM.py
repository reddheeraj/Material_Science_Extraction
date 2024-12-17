from langchain_ollama import ChatOllama, OllamaEmbeddings
from config import prompt_template_A, LLM_MODEL, EMBEDDING_MODEL

def get_llm():
    llm = ChatOllama(model=LLM_MODEL)
    return llm

def query_llama(prompt):
    llm = get_llm()
    res = llm.invoke(prompt)
    return res.content

def get_embeddings():
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return embeddings

def refine_with_llm(chunks):
    properties = []
    for chunk in chunks:
        prompt = prompt_template_A(chunk)
        response = query_llama(prompt)
        # print("response => ", response)
        properties.append(response)
    return properties
