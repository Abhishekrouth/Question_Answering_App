import streamlit as st
import requests

st.title("Question Answering App")

option = st.radio(
    "Options:",["Text", "File"],
    captions=["Write your own context","Upload a context file"]
)

if option == "Text":
    context = st.text_input("Context")
    question = st.text_input("Question")

    if st.button("Answer"):
        if context and question:
            response = requests.post(
                "http://127.0.0.1:5000/ask",
                data={"context": context, "question": question}
            )
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error("Error: " + response.text)
        else:
            st.warning("Provide both context and question.")


elif option == "File":
    uploaded_file = st.file_uploader("Upload a txt or PDF file", type=["txt", "pdf"])
    question = st.text_input("Question")
    if uploaded_file and question and st.button("Answer"):
        response = requests.post(
            "http://127.0.0.1:5000/ask_file",
            files={"file": (uploaded_file.name, uploaded_file.getvalue())},
            data={"question": question}
        )
        if response.status_code == 200:
            st.json(response.json())
        else:
            st.error("Error: " + response.text)


