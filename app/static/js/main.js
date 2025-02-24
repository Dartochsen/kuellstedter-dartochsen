console.log('JavaScript is successfully loaded.');

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/service-worker.js')
        .then(registration => {
            console.log('Service Worker registered with scope:', registration.scope);
        })
        .catch(error => {
            console.error('Service Worker registration failed:', error);
        });
    });
}

// Hervorheben des aktuellen Menüpunkts
const menuItems = document.querySelectorAll('nav ul li a');
menuItems.forEach(item => {
    item.addEventListener('click', () => {
        menuItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
    });
});

// Funktion zum Anzeigen von Benachrichtigungen
function showNotification(message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Dartochsen App', { body: message });
    }
}

// Beispiel für eine asynchrone Funktion zum Laden von Daten
async function loadData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Event Listener für das DOMContentLoaded Event
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    // Hier können Sie Initialisierungscode hinzufügen, der ausgeführt wird, wenn das DOM geladen ist
});

// Exportieren von Funktionen für die Verwendung in anderen Modulen
export { showNotification, loadData };
