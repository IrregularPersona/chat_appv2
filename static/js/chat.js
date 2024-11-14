window.onload = function(){
  
  //Scroll To Bottom
  const lastMessage = document.querySelector(".messages ul li.message:last-child");
  
  if(lastMessage){
    lastMessage.scrollIntoView({behavior: 'smooth'});
  }

  //Highlight Username (Progress)
  const messagesContainer = document.querySelector('.messages');
   
  const currentUser = document.querySelector('.chat-container').dataset.username;
  
  socket.on('new_message', (data) => {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-bubble');
    
    if (data.username === currentUser) {
    messageContainer.classList.add('self');
  }
  
    const messageHeader = document.createElement('div');
    messageHeader.classList.add('message-header');
    messageHeader.innerHTML = `<strong>${data.username}</strong> [${data.timestamp}]`;
    
    const messageText = document.createElement('p');
    messageText.textContent = data.text;
  
    messageContainer.appendChild(messageHeader);
    messageContainer.appendChild(messageText);
  
    document.querySelector('.messages').appendChild(messageContainer);
  });
};