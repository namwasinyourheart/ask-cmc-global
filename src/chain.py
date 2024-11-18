from langchain.document_loaders import SitemapLoader, RecursiveUrlLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS, Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from langchain.retrievers import BM25Retriever, EnsembleRetriever

from .prompts import qa_prompt, condense_question_prompt
from .db import load_session_history, save_message

def get_llm():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=1000)
    return llm

def get_embeddings():
    embeddings = OpenAIEmbeddings()
    return embeddings

def load_documents(urls):

    loader = WebBaseLoader(urls)

    # docs = sitemap_loader.load()
    docs = loader.load()

    return docs

def get_keyword_retriever(docs):
    
    keyword_retriever = BM25Retriever.from_documents(docs)
    return keyword_retriever

def create_vector_db(collection_name, docs):
    # # Split
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                chunk_overlap=200)
    
    # Split the documents into smaller text chunks
    texts = text_splitter.split_documents(docs)
    persist_directory = "../persist"

    # Create a new Chroma collection from the text chunks
    try:
        vector_db = Chroma.from_documents(
            documents=texts,
            embedding=get_embeddings(),
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
    except Exception as e:
        print(f"Error creating collection: {e}")
        return None

    return vector_db

def load_vector_db(collection_name):
    persist_directory = "../persist"
    # Load the Chroma collection from the specified directory
    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
        collection_name=collection_name,
    )

    return vector_db

def get_vectordb_retriever(vector_db):
    vector_db_retriever = vector_db.as_retriever()

    return vector_db_retriever

def get_rag_chain():
    llm = get_llm()
    urls = [
        'https://cmcglobal.com.vn/',
        'https://cmcglobal.com.vn/vi/ve-chung-toi/',
        'https://cmcglobal.com.vn/vi/cmc-corporation-vi/',
        'https://cmcglobal.com.vn/vi/contact-us-vi/'
        ]
    docs = load_documents(urls)
    
    vector_db = create_vector_db(collection_name="cmcglobal_aboutus", docs=docs)
    keyword_retriever = get_keyword_retriever(docs)
    vectordb_retriever = get_vectordb_retriever(vector_db)

    ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vectordb_retriever], 
                                           weights=[0.5, 0.5])
    
    condense_question_chain = condense_question_prompt | llm | StrOutputParser()
    context_chain = condense_question_chain | ensemble_retriever
    rag_chain = qa_prompt | llm | StrOutputParser()

    parallel_chain = RunnableParallel({
        "context": lambda x: x["context"],
        "question": lambda x: x["question"],
        "chat_history": lambda x: x["chat_history"]
    })

    rag_with_sources_chain = RunnablePassthrough.assign(
        context=context_chain,
        question=condense_question_chain
    ) | parallel_chain.assign(answer=rag_chain)

    return rag_with_sources_chain
    

def get_response(session_id, question):

    chat_history = load_session_history(session_id).messages
    chat_history = chat_history[-6:]  # using last 3 turns of chat
    # print(chat_history)
    
    chain = get_rag_chain()
    input = {"question": question, "chat_history": chat_history}
    # response = chain.invoke(input)
    response = chain.invoke(input)
    

    return response