import streamlit as st
import requests
import PyPDF2

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
     opt = st.radio("Choose an option:", ["Start/Resume Session","List Sessions","Upload Documents", "Ask Question", "Clear Sessions", "Delete Sessions"])
     if opt == "Upload Documents":
        uploaded_files = st.file_uploader("Upload txt/PDF files", type=["txt", "pdf"], accept_multiple_files=True)
        if uploaded_files and st.button("Upload"):
                file_data = []
                for f in uploaded_files:
                    
                    if f.name.endswith(".txt"):
                        content = f.getvalue().decode("utf-8")
                    elif f.name.endswith(".pdf"):
                        reader = PyPDF2.PdfReader(f)
                        content = ""
                        for page in reader.pages:
                            content += page.extract_text() + " "
                    else:
                        continue

                    file_data.append({"filename": f.name, "content": content})

                r = requests.post(
                    "http://127.0.0.1:5000/ask_session",
                    json={"name": "session1", "files": file_data}
                )

                if r.status_code == 200:
                    st.json(r.json())
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
        
     elif opt == "Start/Resume Session":
        session_name = st.text_input("Enter a session name")
        if session_name and st.button("Start/Resume"):
                    r = requests.post("http://127.0.0.1:5000/start_session", json={"name": session_name})
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state["session_name"] = data["session_name"]
                        st.success(f"Using session: {data['session_name']}")
                    else:
                        st.error(r.text)

     elif opt == "Ask Question":
            if "session_name" not in st.session_state:
                st.warning("Start or resume a session first.")
            else:
                question = st.text_input("Enter your question")
                if question and st.button("Ask"):
                    r = requests.post("http://127.0.0.1:5000/ask_session", json={"name": st.session_state['session_name'], "question": question})
                    if r.status_code == 200:
                        data = r.json()
                        st.write(f"**Answer:** {data['answer']}")
                        st.markdown("### Conversation History")
                        for i, h in enumerate(data["history"], 1):
                            st.write(f"Question {i}: {h['question']}")
                            st.write(f"Answer {i}: {h['answer']}")
                            st.write(f"Source: {h['source_doc']}")
                    else:
                        st.error(r.text)

     elif opt == "List Sessions":
        r = requests.get("http://127.0.0.1:5000/list_sessions")
        if r.status_code == 200:
                st.json(r.json())
        else:
                st.error(r.text)

     elif opt == "Clear Sessions":
      if "session_name" not in st.session_state:
        st.warning("Start a session first.")
      else:
        if st.button("Clear Current Session"):
            r = requests.get(f"http://127.0.0.1:5000/clear_session/{st.session_state['session_name']}")
            st.write(r.text)

     elif opt == "Delete Sessions":
         session_name = st.text_input("Enter session name to delete")
         if session_name and st.button("Delete"):
             r = requests.get(f"http://127.0.0.1:5000/delete_session/{session_name}")
             st.write(r.text)



