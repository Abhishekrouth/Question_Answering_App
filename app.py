from flask import Flask, request, jsonify
from transformers import pipeline
import PyPDF2


model = "deepset/roberta-base-squad2"
qa_pipeline = pipeline("question-answering", model=model)

app = Flask(__name__)

context = """
The Indian cricket team, also known as the “Men in Blue,” is one of the most successful teams in world cricket.
Governed by the Board of Control for Cricket in India (BCCI), the team played its first Test match in 1932 against 
England at Lord’s. India won its first-ever Cricket World Cup in 1983 under the captaincy of Kapil Dev, a historic 
moment that changed the face of Indian cricket. The team repeated this success in 2011, lifting the World Cup again 
under M. S. Dhoni’s leadership. Apart from these victories, India also won the inaugural ICC T20 World Cup in 2007. 
Over the years, legendary players like Sunil Gavaskar, Sachin Tendulkar, Anil Kumble, Rahul Dravid, and Virat Kohli 
have represented India. With a passionate fan base and a rich cricketing legacy, Indian cricket remains a symbol of 
national pride and unity.
"""
questions = [
"What is the nickname of the Indian cricket team?",
"Who governs the Indian cricket team?",
"In which year did India play its first Test match?",
"Who was the captain when India won its first World Cup in 1983?",
"Which World Cup did India win under M. S. Dhoni’s captaincy?",
"When did India win the inaugural ICC T20 World Cup?",
"Name any two legendary Indian cricketers mentioned in the passage.",
"What does Indian cricket symbolize for the nation?"
    ]

for q in questions:
    result = qa_pipeline(question=q, context=context)
    print(f"Q: {q}\nA: {result['answer']}\n")

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
    
def split_text(text, max_length=300):
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

@app.route('/ask_file', methods=['POST'])
def ask_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    question = request.form['question']

    context = extract_text(uploaded_file)
    if context is None:
        return jsonify({"error": "Error"}), 400

    best_answer = ""
    for chunk in split_text(context):
        result = qa_pipeline(question=question, context=chunk)
        if not best_answer or result['score'] > best_answer['score']:
            best_answer = result

    return jsonify({"answer": best_answer['answer'],"confidence_score": best_answer['score'],
        "start": best_answer['start'],"end": best_answer['end']})

if __name__ == '__main__':
    app.run(debug=True)


































