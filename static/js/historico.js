$(document).ready(function() {
    // Conectar ao servidor WebSocket
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    // Função para atualizar o conteúdo da mensagem resolvida
    function updateResolvedMessage(data) {
        // Atualizar o conteúdo da mensagem no DOM com base no `message_id`
        const messageElement = $('#resolved-message-' + data.message_id);
        if (messageElement.length > 0) {
            messageElement.find('.message-title').text(data.title);
            messageElement.find('.message-content').text(data.content);
            messageElement.find('.message-priority').text(data.priority);
            messageElement.find('.message-datetime').text(data.datetime);
        } else {
            // Se a mensagem não existe, adicioná-la (útil para novas mensagens resolvidas)
            const newMessageDiv = document.createElement('div');
            newMessageDiv.id = 'resolved-message-' + data.message_id;
            newMessageDiv.className = 'message';
            newMessageDiv.innerHTML = `
                <h3 class="message-title">${data.title}</h3>
                <p class="message-content">${data.content}</p>
                <p class="message-priority">${data.priority}</p>
                <p class="message-datetime">Resolvido dia: ${data.datetime}</p>
            `;
            $('#resolved-messages-container').append(newMessageDiv);
        }
    }

    // Função para remover uma mensagem resolvida
    function removeResolvedMessage(data) {
        // Remover o elemento de mensagem do DOM com base no `message_id`
        const messageElement = $('#resolved-message-' + data.message_id);
        if (messageElement.length > 0) {
            messageElement.remove();
        }
    }

    // Ouvir eventos de atualização de mensagem resolvida
    socket.on('message_updated', function(data) {
        updateResolvedMessage(data);
    });

    // Ouvir eventos de exclusão de mensagem resolvida
    socket.on('message_deleted', function(data) {
        removeResolvedMessage(data);
    });

    // Função para obter mensagens resolvidas (sem filtros)
    async function fetchResolvedMessages() {
        try {
            const response = await fetch('/get_resolved_messages');
            if (!response.ok) throw new Error('Erro na resposta do servidor');

            const messages = await response.json();
            const resolvedMessagesContainer = document.getElementById('resolved-messages-container');
            resolvedMessagesContainer.innerHTML = '';

            if (messages.length === 0) {
                resolvedMessagesContainer.innerHTML = '<p>Nenhuma mensagem resolvida disponível.</p>';
                return;
            }

            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.id = 'resolved-message-' + msg.id;
                messageDiv.className = 'message';
                messageDiv.innerHTML = `
                    <h3 class="message-title">${msg.title}</h3>
                    <p class="message-content">${msg.content}</p>
                    <p class="message-priority ${msg.priority === 'aviso' ? 'priority-green' : ''}">${msg.priority}</p>
                    <p class="message-datetime ${msg.datetime ? 'datetime-highlight' : ''}">Resolvido dia: ${msg.datetime}</p>
                `;
                resolvedMessagesContainer.appendChild(messageDiv);
            });
        } catch (error) {
            console.error('Erro ao obter as mensagens resolvidas:', error);
        }
    }  
    

    // Função para obter mensagens resolvidas filtradas
    async function fetchFilteredResolvedMessages() {
        const dataInicioElement = document.getElementById('filter-start-date');
        const dataFimElement = document.getElementById('filter-end-date');

        const dataInicio = dataInicioElement ? dataInicioElement.value : '';
        const dataFim = dataFimElement ? dataFimElement.value : '';

        // Converter data para o formato dd-mm-yyyy (o formato esperado pelo backend)
        const formatDateString = dateStr => dateStr.split('-').reverse().join('-');

        const params = new URLSearchParams();
        if (dataInicio) params.append('data_inicio', formatDateString(dataInicio));
        if (dataFim) params.append('data_fim', formatDateString(dataFim));

        try {
            const response = await fetch(`/get_filtered_resolved_messages?${params.toString()}`);
            if (!response.ok) throw new Error('Erro na resposta do servidor');

            const messages = await response.json();
            const resolvedMessagesContainer = document.getElementById('resolved-messages-container');
            resolvedMessagesContainer.innerHTML = '';

            if (messages.length === 0) {
                resolvedMessagesContainer.innerHTML = '<p>Nenhuma mensagem encontrada com esses filtros.</p>';
                return;
            }

            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.id = 'resolved-message-' + msg.id;
                messageDiv.className = 'message';
                messageDiv.innerHTML = `
                    <h3 class="message-title">${msg.title}</h3>
                    <p class="message-content">${msg.content}</p>
                    <p class="message-priority ${msg.priority === 'aviso' ? 'priority-green' : ''}">${msg.priority}</p>
                    <p class="message-datetime ${msg.datetime ? 'datetime-highlight' : ''}">Resolvido dia: ${msg.datetime}</p>
                `;
                resolvedMessagesContainer.appendChild(messageDiv);
            });
        } catch (error) {
            console.error('Erro ao obter as mensagens resolvidas filtradas:', error);
        }
    }

    // Chama a função para buscar as mensagens resolvidas no carregamento da página
    fetchResolvedMessages();

    // Adiciona event listeners ao botão de filtro
    const filterButton = document.getElementById('filter-button');
    if (filterButton) {
        filterButton.addEventListener('click', fetchFilteredResolvedMessages);
    }

    // Adiciona event listener para detectar a tecla Enter nos inputs de data
    const dateInputs = ['filter-start-date', 'filter-end-date'];
    dateInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('keypress', event => {
                if (event.key === 'Enter') {
                    fetchFilteredResolvedMessages();
                }
            });
        }
    });
});