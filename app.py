from flask import Flask, request, jsonify
from transformers import pipeline
import PyPDF2
import uuid
import chromadb
from chromadb.utils import embedding_functions
import json
import os
import numpy as np
from numpy import dot
from numpy.linalg import norm

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="docs_collection",
embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
)

model = "deepset/roberta-base-squad2"
qa_pipeline = pipeline("question-answering", model=model)
refine = pipeline("text2text-generation", model="google/flan-t5-base")

app = Flask(__name__)
SESSIONS_FILE = "sessions.json"

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

sessions = load_sessions()

# context = """
# The Indian cricket team, also known as the “Men in Blue,” is one of the most successful teams in world cricket.
# Governed by the Board of Control for Cricket in India (BCCI), the team played its first Test match in 1932 against 
# England at Lord’s. India won its first-ever Cricket World Cup in 1983 under the captaincy of Kapil Dev, a historic 
# moment that changed the face of Indian cricket. The team repeated this success in 2011, lifting the World Cup again 
# under M. S. Dhoni’s leadership. Apart from these victories, India also won the inaugural ICC T20 World Cup in 2007. 
# Over the years, legendary players like Sunil Gavaskar, Sachin Tendulkar, Anil Kumble, Rahul Dravid, and Virat Kohli 
# have represented India. With a passionate fan base and a rich cricketing legacy, Indian cricket remains a symbol of 
# national pride and unity.
# """
# questions = [
# "What is the nickname of the Indian cricket team?",
# "Who governs the Indian cricket team?",
# "In which year did India play its first Test match?",
# "Who was the captain when India won its first World Cup in 1983?",
# "Which World Cup did India win under M. S. Dhoni’s captaincy?",
# "When did India win the inaugural ICC T20 World Cup?",
# "Name any two legendary Indian cricketers mentioned in the passage.",
# "What does Indian cricket symbolize for the nation?"
#     ]

# for q in questions:
#     result = qa_pipeline(question=q, context=context)
#     print(f"Q: {q}\nA: {result['answer']}\n")

def extract_text(uploaded_file):
    if uploaded_file.filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    
    elif uploaded_file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + " "
        return text
    else:
        return None
        
def split_text(text, max_length=500):
    words = text.split()
    for i in range(0, len(words), max_length):
        yield " ".join(words[i:i + max_length])

@app.route('/', methods = ['GET'])
def home():
    return "Welcome to Question Answering APP"
    
@app.route('/ask', methods=['POST'])
def ask_questions():
    context = request.form['context']
    question = request.form['question']
    result = qa_pipeline(question=question, context=context)
    return jsonify({"Answer": result['answer'], "confidence_score": result['score'], "Start": result['start'],"End":result['end']})

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "Session name required"}), 400
    if name not in sessions:
        sessions[name] = {"id": str(uuid.uuid4()), "history": []}
        save_sessions()
    return jsonify({"session_name": name, "session_id": sessions[name]["id"]})

@app.route('/ask_session', methods=['POST'])
def ask_session():
    data = request.get_json()
    if "files" in data:
        uploaded_files = data["files"]
        stored_files = []
        for f in uploaded_files:
            text = f["content"]
            doc_name = f["filename"]
            for chunk in split_text(text):
                collection.add(
                    documents=[chunk],
                    metadatas=[{"source": doc_name}],
                    ids=[str(uuid.uuid4())]
                )
            stored_files.append(doc_name)
        return jsonify({"message": "Files uploaded successfully", "stored_files": stored_files})
    
    name = data.get("name")
    question = data.get("question")

    if not name or name not in sessions:
        return jsonify({"error": "Invalid session name"}), 400

    history = sessions[name]["history"]

    results = collection.query(query_texts=[question], n_results=5)
    answers = []

    for i, context in enumerate(results['documents'][0]):
        qa_result = qa_pipeline(question=question, context=context)
        answers.append({
            "answer": qa_result['answer'],
            "confidence_score": qa_result['score'],
            "source_doc": results['metadatas'][0][i]['source']
        })

    best_answer = max(answers, key=lambda x: x['confidence_score'])

    history.append({
        "question": question,
        "answer": best_answer['answer'],
        "source_doc": best_answer['source_doc']
    })
    save_sessions()

    return jsonify({
        "answer": best_answer['answer'],
        "history": history
    })

@app.route('/list_sessions', methods=['GET'])
def list_sessions():
    return jsonify({"sessions": list(sessions.keys())})

@app.route('/clear_session/<name>', methods=['GET'])
def clear_session(name):
    if name in sessions:
        sessions[name]["history"] = []
        save_sessions()
        return f"Session {name} cleared."
    return "Invalid session name", 400

@app.route('/delete_session/<name>', methods=['GET'])
def delete_session(name):
    if name in sessions:
        del sessions[name]
        save_sessions()
        return f"Session {name} deleted."
    return "Invalid session name", 400

@app.route('/ask_refined', methods = ['POST'])
def refined():
    data = request.get_json()
    question = data.get('question')
    result = collection.query(query_texts=[question], n_results=10)
    all_chunks = sum(result["documents"], []) 
    metadatas = sum(result["metadatas"], [])

    query_embedding = collection._embedding_function([question])[0]
    chunk_embeddings = collection._embedding_function(all_chunks)
    
    def cosine_similarity(a, b):
        return dot(a, b) / (norm(a) * norm(b))

    scores = [cosine_similarity(query_embedding, emb) for emb in chunk_embeddings]

    threshold = 0.75
    selected_chunks = [chunk for chunk, score in zip(all_chunks, scores) if score >= threshold]
    if not selected_chunks:
        selected_chunks = all_chunks[:2] 
    top_contexts = " ".join(selected_chunks)

    raw_result = qa_pipeline(question=question, context=top_contexts)
    raw_answer = raw_result["answer"]
    
    source_docs = [meta["source"] for meta_list in result["metadatas"] for meta in meta_list]

    input = f"""
    Question: {question}
    Raw Answer: {raw_answer}
    Context: {top_contexts}

    Return only a concise factual answer strictly relevant to the question. 
    Do not include extra details or timeline unless the question asks for it.
    Keep the answer relevant to the context of question. Do not include extra details or timeline unless the question asks for it.
    """

    refined = refine(input, max_length=100, do_sample=False)[0]["generated_text"].strip()

    return jsonify({"raw_answer": raw_answer,"refined_answer": refined,"source_docs": source_docs})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    from sklearn.metrics import precision_score, recall_score, f1_score
    from difflib import SequenceMatcher
    from numpy import dot
    from numpy.linalg import norm

    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    test_set = [
        {"question": "Why is Yuvraj Singh considered one of India's greatest all rounders?",
         "expected": "His career remains one of inspiration, marked by resilience, fighting spirit, and unforgettable moments. He continues to inspire millions through his foundation YouWeCan, supporting cancer awareness and treatment."},
        {"question": "What made Yuvraj Singh famous in the 2007 World Cup?",
         "expected": "He hit six sixes in one over bowled by Stuart Broad."},
    ]

    prediction = []

    for item in test_set:
        question = item["question"]
        result = collection.query(query_texts=[question], n_results=10)
        all_chunks = sum(result["documents"], [])
        metadatas = sum(result["metadatas"], [])


        query_embedding = collection._embedding_function([question])[0]
        chunk_embeddings = collection._embedding_function(all_chunks)
        def cosine_similarity(a, b):
            return dot(a, b) / (norm(a) * norm(b))
        scores = [cosine_similarity(query_embedding, emb) for emb in chunk_embeddings]

        threshold = 0.75
        selected_chunks = [chunk for chunk, score in zip(all_chunks, scores) if score >= threshold]
        if not selected_chunks:
            selected_chunks = all_chunks[:2]
        top_contexts = " ".join(selected_chunks)

        raw_result = qa_pipeline(question=question, context=top_contexts)
        raw_answer = raw_result["answer"]
        refine_input = f"""
        Question: {question}
        Raw Answer: {raw_answer}
        Context: {top_contexts}

        Return only a concise factual answer strictly relevant to the question. 
        Do not include extra details or timeline unless the question asks for it.
        Keep the answer relevant to the context of question. Do not include extra details or timeline unless the question asks for it.
        """
        refined_answer = refine(refine_input, max_length=100, do_sample=False)[0]["generated_text"].strip()

        prediction.append(refined_answer)

    y_true = [item["expected"].lower() for item in test_set]
    y_pred = [pred.lower() for pred in prediction]

    y_true_bin = [1] * len(y_true)
    y_pred_bin = [1 if similarity(t, p) > 0.5 else 0 for t, p in zip(y_true, y_pred)]

    precision = precision_score(y_true_bin, y_pred_bin, zero_division=0)
    recall = recall_score(y_true_bin, y_pred_bin, zero_division=0)
    f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
    accuracy = sum(y_pred_bin) / len(y_pred_bin)

    return jsonify({"precision": round(precision, 3),"recall": round(recall, 3),"f1_score": round(f1, 3),"retrieval_accuracy": round(accuracy, 3)})


if __name__ == '__main__':
    app.run(debug=True)


































