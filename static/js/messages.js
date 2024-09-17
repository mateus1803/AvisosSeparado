var socket = io();

// Função para verificar se o usuário já votou nesta mensagem
function hasUserVoted(messageId) {
    var votedMessages = JSON.parse(localStorage.getItem('votedMessages')) || [];
    return votedMessages.includes(messageId.toString());
}

// Função para armazenar o ID da mensagem em que o usuário votou
function recordVote(messageId) {
    var votedMessages = JSON.parse(localStorage.getItem('votedMessages')) || [];
    votedMessages.push(messageId.toString());
    localStorage.setItem('votedMessages', JSON.stringify(votedMessages));
}

// Função para remover o like de uma mensagem
function removeLike(messageId) {
    if (hasUserVoted(messageId)) {
        var likeCountElement = document.querySelector('.message[data-id="' + messageId + '"] .like-count');
        var currentLikes = parseInt(likeCountElement.textContent) || 0; // Use 0 como fallback
        likeCountElement.textContent = Math.max(currentLikes - 1, 0);

        var votedMessages = JSON.parse(localStorage.getItem('votedMessages')) || [];
        var index = votedMessages.indexOf(messageId.toString());
        if (index !== -1) {
            votedMessages.splice(index, 1);
            localStorage.setItem('votedMessages', JSON.stringify(votedMessages));
        }

        // Emite um evento para o servidor
        socket.emit('unlike_message', { message_id: messageId });
    } else {
        console.log('Você ainda não curtiu esta mensagem.');
    }
}

// Função para lidar com o clique no botão de "like"
function handleLikeClick(messageId) {
    var likeCountElement = document.querySelector('.message[data-id="' + messageId + '"] .like-count');
    if (!hasUserVoted(messageId)) {
        console.log('O usuário curtiu a mensagem com o ID:', messageId);

        var currentLikes = parseInt(likeCountElement.textContent) || 0; // Use 0 como fallback
        likeCountElement.textContent = currentLikes + 1;

        recordVote(messageId);

        socket.emit('like_message', { message_id: messageId });
    } else {
        removeLike(messageId);
    }
}



/////////////////////////////////////////////////////////atualizaçõess/////////////////////////////
$(document).ready(function() {
    $('#toggle-info').click(function() {
        $('#info-container .info-content').toggle();
    });
    $('#toggle-birthday').click(function() {
        $('#birthday-container .birthday-content').toggle();
    });

    // Configuração do Socket.IO
    const socket = io();

    // Escuta eventos de novos conteúdos
    socket.on('new_info', function(data) {
        const newInfoHtml = `<p><strong>${data.title}:</strong> ${data.content}</p>`;
        $('#info-messages').append(newInfoHtml);
    });

    socket.on('new_birthday', function(data) {
        const newBirthdayHtml = `<p>${data.name} - ${data.date}</p>`;
        $('#birthday-messages').append(newBirthdayHtml);
    });
});
///////////////////////////////////////////////////////////////////////////

// Função para renderizar mensagens no DOM
function renderMessages(messages) {
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.innerHTML = '';

    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.dataset.id = message.id;
        messageDiv.innerHTML = `
            <h3>${message.title}</h3>
            <p id="priority" class="priority-text" style="color: ${getColorByPriority(message.priority)};">Situação: ${message.priority}</p>
            <p>${message.content}</p>
            <p class="date-time centered-text">Atualizado dia: ${message.datetime}</p>
            <p>Responsável: ${message.autor}</p>
            <div class="like-container">
                <button class="like-button" onclick="handleLikeClick(${message.id})">👍</button>
                <span class="like-count">${message.likes || 0}</span>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
    });
}



// Escuta a atualização de uma mensagem
socket.on('update_message', function(message) {
    var messageDiv = document.querySelector('.message[data-id="' + message.id + '"]');
    if (messageDiv) {
        var likeCountElement = messageDiv.querySelector('.like-count');
        likeCountElement.textContent = message.likes || 0; // Use 0 como fallback
    }
});

// Função para exibir notificação com conteúdo atualizado
function showNotificationWithUpdatedContent(messageContent) {
    if (typeof lastMessageContent === 'undefined') {
        window.lastMessageContent = '';
    }

    if (messageContent !== lastMessageContent) {
        if (Notification.permission !== 'granted') {
            Notification.requestPermission();
        } else {
            var notification = new Notification('Mensagens', {
                body: 'Conteúdo atualizado: ' + messageContent,
            });
            lastMessageContent = messageContent;
        }
    }
}

// Exibir notificação quando a página for carregada
window.onload = function () {
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    } else {
        var notification = new Notification('Mensagens', {
            body: 'A tela foi atualizada.',
        });
    }

    fetch('/get_messages')
        .then(response => response.json())
        .then(messages => renderMessages(messages))
        .catch(error => console.error('Erro ao obter as mensagens:', error));
};

// Função para retornar a cor com base na prioridade
function getColorByPriority(priority) {
    switch (priority) {
        case 'com problema':
            return '#ff3300'; // Vermelho
        case 'manutenção':
            return '#fffb00'; // Azul
        case 'resolvido':
            return '#00cc00'; // Verde
        default:
            return '#000'; // Cor padrão
    }
}
