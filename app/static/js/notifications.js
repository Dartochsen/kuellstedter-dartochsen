// Firebase-Konfiguration
const firebaseConfig = {
  apiKey: "AIzaSyAsB571e3zF-VU8_x99JKd0-jlRUCMyYvs",
  authDomain: "dartochsenapp.firebaseapp.com",
  projectId: "dartochsenapp",
  storageBucket: "dartochsenapp.firebasestorage.app",
  messagingSenderId: "234549860324",
  appId: "1:234549860324:web:a78e01b6df5326db75d9f1"
};

// Firebase initialisieren
firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// Funktion zum Anfordern der Benachrichtigungsberechtigung
function requestNotificationPermission() {
  Notification.requestPermission().then((permission) => {
    if (permission === 'granted') {
      console.log('Benachrichtigungsberechtigung erteilt.');
      getMessagingToken();
    } else {
      console.log('Keine Berechtigung für Benachrichtigungen erhalten.');
    }
  });
}

// Funktion zum Abrufen des Messaging-Tokens
function getMessagingToken() {
  messaging.getToken().then((currentToken) => {
    if (currentToken) {
      console.log('Token:', currentToken);
      sendTokenToServer(currentToken);
    } else {
      console.log('Kein Instanz-ID-Token verfügbar. Berechtigung zum Generieren anfordern.');
    }
  }).catch((err) => {
    console.log('Fehler beim Abrufen des Tokens: ', err);
  });
}

// Funktion zum Senden des Tokens an den Server
function sendTokenToServer(token) {
  fetch('/register-token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({token: token}),
  })
  .then(response => response.json())
  .then(data => console.log('Token registriert:', data))
  .catch((error) => console.error('Fehler:', error));
}

// Funktion zum Empfangen von Benachrichtigungen
messaging.onMessage((payload) => {
  console.log('Nachricht empfangen:', payload);
  // Hier können Sie die empfangene Nachricht verarbeiten und anzeigen
});

// Benachrichtigungsberechtigung beim Laden der Seite anfordern
document.addEventListener('DOMContentLoaded', (event) => {
  requestNotificationPermission();
});
