import logging
import random
import requests
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load DialoGPT
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

user_progress = {}
active_exercises = {}
active_quizzes = {}

def grammar_exercise():
    exercises = [
        {"question": "Identify the grammatical error: She don't like apples.", "answer": "doesn't"},
        {"question": "Construct a sentence using 'quickly' as an adverb.", "answer": "He runs quickly."},
        {"question": "Identify the grammatical error: He go to the park.", "answer": "goes"},
        {"question": "Construct a sentence using 'always' as an adverb.", "answer": "She always smiles."},
        {"question": "Identify the grammatical error: They was happy.", "answer": "were"},
    ]
    return random.choice(exercises)

def correct_grammar(sentence):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': sentence,
        'language': 'en-US'
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        matches = response.json().get('matches', [])

        if not matches:
            return "No grammatical errors detected."

        corrections = []
        for match in matches:
            replacements = [rep['value'] for rep in match['replacements']]
            corrections.append(f"Error: {match['message']}. Suggestion: {', '.join(replacements)}")

        logging.debug(f"Corrections for '{sentence}': {corrections}")
        return "\n".join(corrections)
    except requests.RequestException as e:
        logging.error(f"Error communicating with grammar correction API: {e}")
        return "Error communicating with grammar correction API."

def explain_grammar(concept):
    explanations = {
        "noun": "A noun is a person, place, thing, or idea (e.g., 'dog', 'city', 'happiness').",
        "verb": "A verb expresses action or being (e.g., 'run', 'is').",
        "adverb": "An adverb modifies a verb, adjective, or another adverb (e.g., 'quickly', 'very').",
        "adjective": "An adjective describes a noun (e.g., 'blue', 'happy').",
        "pronoun": "A pronoun replaces a noun (e.g., 'he', 'she', 'they')."
    }
    return explanations.get(concept.lower(), "I'm not sure about that concept.")

def identify_intent(user_input):
    user_input = user_input.lower()
    intents = {
        "greeting": ["hello", "hi", "hey"],
        "ask_noun": ["noun"],
        "ask_verb": ["verb"],
        "ask_adverb": ["adverb"],
        "ask_adjective": ["adjective"],
        "ask_pronoun": ["pronoun"],
        "request_exercise": ["exercise"],
        "request_quiz": ["quiz"],
        "difference": ["difference"]
    }
    
    for intent, keywords in intents.items():
        if any(keyword in user_input for keyword in keywords):
            return intent
    return "general_query"

def generate_difference_response(terms):
    if len(terms) == 2:
        return f"The difference between {terms[0]} and {terms[1]} is..."
    return "Please provide exactly two terms to compare."

def generate_quiz():
    quizzes = [
        {"question": "Choose the correct word: She (is/are) going to the market.", "options": ["is", "are"], "answer": "is"},
        {"question": "Fill in the blank: They ____ (play/plays) soccer.", "options": ["play", "plays"], "answer": "play"},
        {"question": "Choose the correct form: He (go/goes) to school every day.", "options": ["go", "goes"], "answer": "goes"},
        {"question": "Identify the error: The cat have eaten its food.", "options": ["have", "has"], "answer": "has"},
        {"question": "Choose the correct word: I (am/is) happy today.", "options": ["am", "is"], "answer": "am"},
        {"question": "Fill in the blank: She ____ (like/likes) to read books.", "options": ["like", "likes"], "answer": "likes"},
        {"question": "Choose the correct form: They (is/are) friends.", "options": ["is", "are"], "answer": "are"},
        {"question": "Identify the error: He don't know the answer.", "options": ["don't", "doesn't"], "answer": "doesn't"}
    ]
    return random.choice(quizzes)

def extract_terms(user_input):
    terms = user_input.split("difference between")[-1].strip().split()
    return terms

def respond(user_input, chat_history_ids=None, user_id=None, current_exercise=None, current_quiz=None):
    try:
        if not user_input:
            return "Please type something so I can assist you.", chat_history_ids

        intent = identify_intent(user_input)

        # Directly check for common grammatical mistakes
        if "she are" in user_input.lower():
            return "That's not correct. The correct sentence is: 'She is a teacher.'", chat_history_ids

        # Check for sentence correction request
        if "correct" in user_input.lower():
            sentence_to_correct = user_input.split("correct the sentence: ")[-1].strip('\'"')
            corrected_sentence = correct_grammar(sentence_to_correct)
            return f"Here are the corrections: {corrected_sentence}", chat_history_ids

        # Handle exercise answers
        if current_exercise:
            if user_input.strip().lower() == current_exercise['answer'].strip().lower():
                return "Correct! Great job.", chat_history_ids
            else:
                return "That's not correct. Try again.", chat_history_ids

        # Handle quiz answers
        if current_quiz:
            if user_input.strip().lower() == current_quiz['answer'].strip().lower():
                return "Correct! Well done.", chat_history_ids
            else:
                return f"That's not correct. The correct answer is: {current_quiz['answer']}", chat_history_ids

        if intent in ["ask_noun", "ask_verb", "ask_adverb", "ask_adjective", "ask_pronoun"]:
            return explain_grammar(intent.split('_')[-1]), chat_history_ids
        
        elif intent == "request_exercise":
            current_exercise = grammar_exercise()
            return f"Here is an exercise: {current_exercise['question']}", chat_history_ids
        
        elif intent == "request_quiz":
            current_quiz = generate_quiz()
            return f"Here is your quiz question: {current_quiz['question']}", chat_history_ids
        
        elif intent == "difference":
            terms = extract_terms(user_input)
            return generate_difference_response(terms), chat_history_ids

        # Using DialoGPT for general responses
        new_user_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if chat_history_ids is not None else new_user_input_ids

        chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

        return response, chat_history_ids
    
    except Exception as e:
        logging.error(f"Error in respond function: {e}")
        return f"Error: {str(e)}", chat_history_ids

if __name__ == "__main__":
    print("Chatbot module loaded successfully!")
