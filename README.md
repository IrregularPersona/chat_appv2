## Running the code

Running the app for the first time is easy. Theres a few step you have to take.

1. Making a venv so that everything is isolated and you can install packages without affecting the rest of your system. You can do this by running 
        
    ``` python -m venv venv ```

2. Activating the venv (on your powershell terminal in VSCode). You can do this by running
    ``` .\venv\Scripts\Activate ```

3. Installing the required packages. You can do this by running
    ``` pip install -r requirements.txt ```

and this should work instantly

### TODO:
- [X] Login/Logout/Register
- [X] Message Timestamp (GMT +7)
- [X] Message Bubbles
- [ ] Message Bubble Formatting
- [X] Messages to DB
- [X] Real-time update of messages
- [X] Auto-Scroll per new message
- [ ] Color change between Self and other user
