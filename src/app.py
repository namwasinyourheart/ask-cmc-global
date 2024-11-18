import streamlit as st

import time
from datetime import datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from dotenv import load_dotenv
load_dotenv()


from chain import *
# from rag_history_chain import *


# def get_response():
#     time.sleep(3)
#     return "This is resonse of AI"
    # pass
    # return response
st.set_page_config(page_title="Ask CMC") 
st.title("Ask CMC")


# Function to generate initial message
def generate_initial_message():
    current_time = datetime.now().time()
    if 5 <= current_time.hour < 12:
        greeting = "Good morning"
    elif 12 <= current_time.hour < 18:
        greeting = "Good afternoon"
    elif 18 <= current_time.hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Hello"
    initial_prompt = f"{greeting}! How can I assist you?"
    return initial_prompt


# Function to generate assistant's response message
def generate_response_message(response):
    full_response = ""
    response_words = response.split()
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        for word in response_words:
            full_response += word + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.05)
        message_placeholder.markdown(full_response)

    return full_response



def main():
    import uuid

    context = None
    question = None

    # Generate a unique session_id for each user if not already set
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    session_id = st.session_state.session_id

    with st.sidebar:
        st.title("Chat Info")
        st.write(f"Session ID: {session_id}")

        # st.subheader("Source")

        # from utils import documents_to_dataframe
        # # st.subheader("Chat history")
        # # chat_history = load_session_history(session_id).messages
        # # # chat_history = response['chat_history']
        # # st.write(chat_history)

        # st.subheader("Source")
        
        # st.write(question)
        # # context = response['context']
        # context_df = documents_to_dataframe(context)
        # st.write(context_df)

    # col1, col2 = st.columns(2)
    # with col1:
        # session_id = "abcd"
    chat_history = None

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": generate_initial_message()
            })
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])


    # User input prompt
    user_input = st.chat_input("Enter your message:")
    # if st.session_state.messages[-1]["role"] != "assistant":
    # Process user input
    if user_input:

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            time.sleep(0.5)

        with st.spinner(""):
            # response = get_response(user_input)['answer']
            response = get_response(session_id, user_input)
        context = response['context']
        question = response['question']
        save_message(session_id, "human", user_input)
        save_message(session_id, "ai", response['answer'])

        # full_response = generate_response_message(response['answer'])
        st.write(response['answer'])
        # st.write(response)
        full_response = response['answer']
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        with st.sidebar:
            st.subheader("Source")
            from utils import documents_to_dataframe
            # st.subheader("Chat history")
            # chat_history = load_session_history(session_id).messages
            # # chat_history = response['chat_history']
            # st.write(chat_history)  
            st.write(question)
            # context = response['context']
            context_df = documents_to_dataframe(context)
            st.write(context_df)

    # with col2:
    #     from utils import documents_to_dataframe
    #     # st.subheader("Chat history")
    #     # chat_history = load_session_history(session_id).messages
    #     # # chat_history = response['chat_history']
    #     # st.write(chat_history)

    #     st.subheader("Source")
        
    #     st.write(question)
    #     # context = response['context']
    #     context_df = documents_to_dataframe(context)
    #     st.write(context_df)



if  __name__ == "__main__":
    main()

