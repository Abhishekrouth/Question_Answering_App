# Question Answering App: Flask + Hugging Face + Streamlit (RAG)

This is a Context based question answering app built with Flask and hugging face.
It uses [deepset/roberta-base-squad2 model](https://huggingface.co/deepset/roberta-base-squad2) 
to extract answer from a given context. It also has a feature to upload multiples .pdf or .txt and
extract answer from them.

## Features

* By default app has a context about journey of Indian cricket team and answers the predefined questions
such as: 
Who was the captain when India won its first World Cup in 1983?
When did India win the inaugural ICC T20 World Cup?

* GET  / : Response with a welcome message
* POST /ask:  accepts a context and question and returns the answer and it's confidence score
* POST /ask_file: to upload multiple(.txt/.pdf) for context
* POST /ask_docs: to retrieve answers from the uploaded docs
* Returns:
  1. Answer: Based context
  2. Confidence score: Confidence of model in extracting the 
     answer from the context
  3. Start:The index of the character in the context that corresponds 
     to the start of the extracted answer.
  4. End:The index of the character in the context that corresponds 
     to the end of the extracted answer.
* Used Streamlit for UI
* Chromadb to save the uploaded files
> Using Hugging Face's pipeline: 'question-answering'

## Technologies Used:

* Python
* Flask
* Hugging face
* Streamlit
* Chromadb

## Installation:

1. Clone the repository:
<pre> git clone https://github.com/yourusername/Question_Answering_App.git 
 cd Question_Answering_App </pre>

2. Set up the environment
<pre> python -m venv venv
 venv\Scripts\Activate</pre>

3. Install dependecies
<pre>pip install -r requirements.txt</pre>

4. Run the application
<pre>python app.py</pre>
<pre>streamlit run streamlit.py</pre>

![alt text](home.png)

### 'Text' option:

![alt text](Text.png)

### 'File' option

1. Upload & Save Documents: We can upload multiples files(.txt/.pdf)

![alt text](upload_file.png)


2. Ask a question from the saved file
   > Correct answer was Rohit Sharma (mentioned in the Sachin.pdf)

![alt text](Question.png)
