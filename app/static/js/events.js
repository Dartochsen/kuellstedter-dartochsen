function registerForEvent(eventId) {
    fetch('/api/register-event', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ eventId: eventId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Anmeldung für Event ' + eventId + ' war erfolgreich!');
        } else {
            alert('Anmeldung fehlgeschlagen: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Fehler bei der Anmeldung:', error);
        alert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    });
}
