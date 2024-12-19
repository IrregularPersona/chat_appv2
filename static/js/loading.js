function showLoading(message) {
    const overlay = document.getElementById('loadingOverlay');
    const messageElement = document.getElementById('loadingMessage');
    
    messageElement.textContent = message;
    overlay.style.display = 'flex';
    
    return new Promise(resolve => {
        setTimeout(() => {
            overlay.style.display = 'none';
            resolve();
        }, 5000); // Show loading for 2 seconds
    });
}

// Handle flash messages
document.addEventListener('DOMContentLoaded', () => {
    const messages = document.querySelectorAll('.input-feedback');
    if (messages.length > 0) {
        const message = messages[0].textContent.trim();
        messages[0].remove(); // Remove the original flash message
        showLoading(message);
    }
}); 