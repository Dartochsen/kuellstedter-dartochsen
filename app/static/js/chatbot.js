// static/js/chatbot.js

document.addEventListener('DOMContentLoaded', function() {
    const chatbotContainer = document.getElementById('chatbot-container');
    const closeChatbotButton = document.getElementById('close-chatbot');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const sendButton = document.getElementById('send-chatbot-message');

    // Funktion zum Schließen des Chatbots
    function closeChatbot() {
        chatbotContainer.classList.add('d-none');
    }

    // Funktion zum Öffnen des Chatbots
    function openChatbot() {
        chatbotContainer.classList.remove('d-none');
    }

    // Funktion zum Umschalten der Sichtbarkeit des Chatbots
    function toggleChatbot() {
        chatbotContainer.classList.toggle('d-none');
    }

    // Funktion zum Senden einer Nachricht
    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (message === "") return;
        
        chatbotInput.value = "";
        
        displayMessage("Sie: " + message);
        
        fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({message: message}),
        })
        .then(response => response.json())
        .then(data => {
            displayMessage("Bot: " + data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage("Bot: Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.");
        });
    }

    // Funktion zum Anzeigen einer Nachricht im Chatfenster
    function displayMessage(message) {
        const messageElement = document.createElement("p");
        messageElement.textContent = message;
        chatbotMessages.appendChild(messageElement);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    // Event Listener hinzufügen
    if (closeChatbotButton) {
        closeChatbotButton.addEventListener('click', closeChatbot);
    }

    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    // Globale Funktionen verfügbar machen
    window.toggleChatbot = toggleChatbot;
    window.sendChatbotMessage = sendMessage;
});
