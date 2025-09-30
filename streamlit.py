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

    options = st.radio("Choose an option:", ["Upload Documents", "Ask Question"])
    if options == "Upload Documents":
        uploaded_files = st.file_uploader("Upload txt/PDF files", type=["txt", "pdf"], accept_multiple_files=True)
        if uploaded_files and st.button("Upload"):
            files = [("files", (f.name, f.getvalue())) for f in uploaded_files]
            response = requests.post("http://127.0.0.1:5000/ask_file", files=files)
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error("Error: " + response.text) 

    elif options == "Ask Question":
        question = st.text_input("Enter your question")
        if question and st.button("Ask form Doc"):
            response = requests.post("http://127.0.0.1:5000/ask_docs", json={"question": question})
            if response.status_code == 200:
                data = response.json()
                if "answers" in data and len(data["answers"]) > 0:
                    for i, ans in enumerate(data["answers"], start=1):
                        st.write(f"**Answer {i}:** {ans['answer']}")
                        st.write(f"Confidence: {ans['confidence_score']:.4f}")
                        st.write(f"Source: {ans['source_doc']}")
                else:
                    st.warning("No relevant answers found.")
            else:
                    st.error("Error: " + response.text)