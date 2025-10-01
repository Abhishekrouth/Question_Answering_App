# @app.route('/ask_session', methods=['POST'])
# def ask_session():
#     data = request.json
#     name = data.get("name")
#     question = data.get("question")

#     if name not in sessions:
#         return jsonify({"error": "Invalid session name"}), 400

#     history = sessions[name]["history"]

#     results = collection.query(query_texts=[question], n_results=5)
#     answers = []

#     for i, context in enumerate(results['documents'][0]):
#         qa_result = qa_pipeline(question=question, context=context)
#         answers.append({
#         "answer": qa_result['answer'],
#         "confidence_score": qa_result['score'],
#         "source_doc": results['metadatas'][0][i]['source']
#     })

#     best_answer = max(answers, key=lambda x: x['confidence_score'])

#     history.append({
#         "question": question,
#         "answer": best_answer['answer'],
#         "source_doc": best_answer['source_doc']
#     })
#     save_sessions()

#     return jsonify({
#             "answer": best_answer['answer'],
#             "history": history
#         })