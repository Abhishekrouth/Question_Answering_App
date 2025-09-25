from flask import Flask, request, jsonify
from transformers import pipeline

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

@app.route('/', methods = ['GET'])
def home():
    return "Welcome to Question Answering APP"
    
@app.route('/ask', methods=['POST'])
def ask_questions():
    context = request.form['context']
    question = request.form['question']
    result = qa_pipeline(question=question, context=context)
    return jsonify({"Answer": result['answer'], "confidence_score": result['score']})
    
if __name__ == '__main__':
    app.run(debug=True)





































