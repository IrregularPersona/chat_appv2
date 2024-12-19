document.addEventListener('DOMContentLoaded', () => {
    const usernameInput = document.querySelector('input[name="username"]');
    if (!usernameInput) return;

    let timeout = null;
    
    usernameInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        
        timeout = setTimeout(() => {
            const username = e.target.value;
            if (username.length < 3) return;
            
            fetch('/check_username', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username }),
            })
            .then(response => response.json())
            .then(data => {
                const feedback = document.createElement('div');
                feedback.className = `input-feedback ${data.exists ? 'error' : 'success'}-feedback`;
                feedback.textContent = data.exists ? 
                    'Username already taken' : 
                    'Username available';
                
                // Remove any existing feedback
                const existingFeedback = usernameInput.parentNode.querySelector('.input-feedback');
                if (existingFeedback) {
                    existingFeedback.remove();
                }
                
                usernameInput.parentNode.appendChild(feedback);
            });
        }, 500);
    });
}); 