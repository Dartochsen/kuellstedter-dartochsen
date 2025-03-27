console.log('JavaScript is successfully loaded.');

// CSRF-Token zu allen AJAX-Anfragen hinzufügen
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrf_token');

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
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });

    // Weitere Initialisierungscode hier hinzufügen
});

// Funktion zum Anzeigen von Benachrichtigungen
function showNotification(message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Dartochsen App', { body: message });
    } else if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Dartochsen App', { body: message });
            }
        });
    }
}

// Beispiel für eine asynchrone Funktion zum Laden von Daten
async function loadData(url) {
    try {
        const response = await fetch(url, {
            headers: { 'X-CSRFToken': csrftoken }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Exportieren von Funktionen für die Verwendung in anderen Modulen
export { showNotification, loadData };
