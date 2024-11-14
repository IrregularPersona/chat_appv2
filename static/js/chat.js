window.onload = function(){
  
  //Scroll To Bottom
  const lastMessage = document.querySelector(".messages ul li.message:last-child");
  
  if(lastMessage){
    lastMessage.scrollIntoView({behavior: 'smooth'});
  }

  //Highlight Username
  const currentUser = document.querySelector('.chat-container').dataset.username;

  let chatLog = Array.from(document.querySelectorAll('.message'));

  chatLog.forEach((message, index) => {
    if(message.querySelector('.message-header strong').dataset.user === currentUser){
      message.classList.add('right');
    };
  });
};