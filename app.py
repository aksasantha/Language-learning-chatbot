from flask import Flask, request, jsonify, render_template
from chatbot import respond, grammar_exercise, generate_quiz
import uuid

app = Flask(__name__)

user_progress = {}
active_exercises = {}
active_quizzes = {}
user_chat_history = {}

def update_progress(user_id, score):
    if user_id not in user_progress:
        user_progress[user_id] = {"score": 0, "completed_exercises": 0}
    
    user_progress[user_id]["score"] += score
    user_progress[user_id]["completed_exercises"] += 1
    
    return user_progress[user_id]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    user_id = request.json.get("user")

    if not user_id:
        user_id = str(uuid.uuid4())

    current_exercise = active_exercises.get(user_id)
    current_quiz = active_quizzes.get(user_id)
    chat_history_ids = user_chat_history.get(user_id, None)

    feedback = ""
    score = 0
    correct = False
    progress = None

    # Handle exercises
    if current_exercise:
        feedback, chat_history_ids = respond(user_input, chat_history_ids=chat_history_ids, user_id=user_id, current_exercise=current_exercise)
        if feedback.startswith("Correct"):
            active_exercises.pop(user_id)
            correct = True
    # Handle quizzes
    elif current_quiz:
        feedback, chat_history_ids = respond(user_input, chat_history_ids=chat_history_ids, user_id=user_id, current_quiz=current_quiz)
        if feedback.startswith("Correct"):
            active_quizzes.pop(user_id)
            correct = True
    # General response
    else:
        feedback, chat_history_ids = respond(user_input, chat_history_ids=chat_history_ids, user_id=user_id)

    score = 1 if correct else 0

    if user_id:
        progress = update_progress(user_id, score)

    user_chat_history[user_id] = chat_history_ids  # Store updated chat history IDs

    return jsonify({"response": feedback, "progress": progress})

@app.route("/exercise", methods=["POST"])
def exercise():
    user_id = request.json.get("user")
    if not user_id:
        user_id = str(uuid.uuid4())
    exercise = grammar_exercise()
    active_exercises[user_id] = exercise
    return jsonify({"question": exercise["question"], "answer": exercise["answer"]})

@app.route("/quiz", methods=["POST"])
def quiz():
    user_id = request.json.get("user")
    if not user_id:
        user_id = str(uuid.uuid4())
    quiz = generate_quiz()
    active_quizzes[user_id] = quiz
    return jsonify({"question": quiz["question"], "options": quiz["options"], "answer": quiz["answer"]})

if __name__ == "__main__":
    app.run(debug=True)
