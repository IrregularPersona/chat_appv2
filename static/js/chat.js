window.onload = function(){
  
  //Scroll To Bottom
  const lastMessage = document.querySelector(".messages ul li:last-child");
  console.log(lastMessage);
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

function scrollToBottom() {
  const messageList = document.getElementById('message-list');
  const lastMessage = messageList ? messageList.lastElementChild : null;
  
  if (lastMessage) {
      lastMessage.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
      });
  }
}

function convertToGMTPlus7(utcDateString) {
  const date = new Date(utcDateString);
  const gmtPlus7Offset = 7 * 60 * 60 * 1000;
  const gmtPlus7Date = new Date(date.getTime() + gmtPlus7Offset);
  return gmtPlus7Date.toLocaleTimeString(); 
}