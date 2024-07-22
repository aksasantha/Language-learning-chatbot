const chatbox = document.getElementById("messages");
const userId = "user_" + Date.now();
let currentExercise = null;
let currentQuiz = null;

document.getElementById("sendButton").addEventListener("click", sendMessage);
document.getElementById("exerciseButton").addEventListener("click", getExercise);
document.getElementById("quizButton").addEventListener("click", getQuiz);

function sendMessage() {
    const userInput = document.getElementById("userInput").value;
    if (!userInput) return;

    appendMessage("You: " + userInput);
    document.getElementById("userInput").value = '';

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message: userInput,  // Changed to message to match server expectation
            user: userId         // Changed to user to match server expectation
        }),
    })
    .then(response => response.json())
    .then(data => {
        appendMessage("Bot: " + data.response);
        if (data.progress) {
            displayProgress(data.progress);
        }
    })
    .catch(error => console.error("Error:", error));
}

function getExercise() {
    fetch("/exercise", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ user: userId }),  // Changed to user to match server expectation
    })
    .then(response => response.json())
    .then(data => {
        appendMessage("Exercise: " + data.question); // Updated to match response structure
        currentExercise = data; // Set current exercise
    })
    .catch(error => console.error("Error:", error));
}

function getQuiz() {
    fetch("/quiz", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ user: userId }),  // Changed to user to match server expectation
    })
    .then(response => response.json())
    .then(data => {
        appendMessage("Quiz: " + data.question + " Options: " + data.options.join(", ")); // Updated to match response structure
        currentQuiz = data; // Set current quiz
    })
    .catch(error => console.error("Error:", error));
}

function appendMessage(message) {
    const msgElement = document.createElement("div");
    msgElement.textContent = message;
    chatbox.appendChild(msgElement);
    chatbox.scrollTop = chatbox.scrollHeight; // Auto scroll to the bottom
}

function displayProgress(progress) {
    const progressElement = document.getElementById("progress");
    if (progressElement) {
        progressElement.textContent = `Score: ${progress.score}, Completed Exercises: ${progress.completed_exercises}`;
    }
}
