var socket = io();

// Atualizar a tabela de mensagens ao receber um evento 'message_updated' do servidor
socket.on('message_updated', function (data) {
    var message_id = data.message_id;
    var title = data.title;
    var content = data.content;
    var priority = data.priority;
    var author = data.author;
    var datetime = data.datetime;

    var messageRow = document.getElementById('message-' + message_id);
    if (messageRow) {
        messageRow.innerHTML = `
            <td>${title}</td>
            <td>${content}</td>
            <td>${priority}</td>
            <td>${author}</td>
            <td>${datetime}</td>
            <td>
                <a href="/edit_message/${message_id}" class="btn btn-warning btn-sm"><i class="fas fa-edit"></i> Editar</a> 
                <form action="/delete_message/${message_id}" method="post" class="d-inline" onsubmit="return confirmDelete()">
                    <button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-trash-alt"></i> Excluir</button>
                </form>
                ${priority !== 'resolvido' ? `
                <form action="/resolve_message/${message_id}" method="post" class="d-inline">
                    <button type="submit" class="btn btn-success btn-sm"><i class="fas fa-check"></i> Resolver</button>
                </form>` : ''}
            </td>`;
    }
});

// Excluir mensagem da tabela ao receber um evento 'message_deleted' do servidor
socket.on('message_deleted', function (data) {
    var message_id = data.message_id;
    var messageRow = document.getElementById('message-' + message_id);
    if (messageRow) {
        messageRow.remove();
    }
});

// Atualizar a tabela de informações ao receber um evento 'info_updated' do servidor
socket.on('info_updated', function (data) {
    var info_id = data.info_id;
    var title = data.title;
    var content = data.content;
    var datetime = data.datetime;

    var infoRow = document.getElementById('info-' + info_id);
    if (infoRow) {
        infoRow.innerHTML = `
            <td>${title}</td>
            <td>${content}</td>
            <td>${datetime}</td>
            <td>
                <a href="/edit_info/${info_id}" class="btn btn-warning btn-sm"><i class="fas fa-edit"></i> Editar</a>
                <form action="/delete_info/${info_id}" method="post" class="d-inline" onsubmit="return confirmDeleteInfo()">
                    <button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-trash-alt"></i> Excluir</button>
                </form>
            </td>`;
    } else {
        var newRow = document.createElement('tr');
        newRow.id = 'info-' + info_id;
        newRow.innerHTML = `
            <td>${title}</td>
            <td>${content}</td>
            <td>${datetime}</td>
            <td>
                <a href="/edit_info/${info_id}" class="btn btn-warning btn-sm"><i class="fas fa-edit"></i> Editar</a>
                <form action="/delete_info/${info_id}" method="post" class="d-inline" onsubmit="return confirmDeleteInfo()">
                    <button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-trash-alt"></i> Excluir</button>
                </form>
            </td>`;
        document.getElementById('info-messages').appendChild(newRow);
    }
});

// Atualizar a tabela de aniversariantes ao receber um evento 'aniversario_updated' do servidor
socket.on('aniversario_updated', function (data) {
    var nome = data.nome;
    var dataAniversario = data.data;
    // Atualize a exibição dos aniversariantes como desejar
    console.log("Aniversariante Atualizado: ", nome, dataAniversario);
    // Código para atualizar dinamicamente a interface do usuário
});

// Confirmar exclusão de informações
function confirmDeleteInfo() {
    return confirm("Tem certeza de que deseja excluir esta informação?");
}

// Confirmar exclusão de mensagens
function confirmDelete() {
    return confirm("Tem certeza de que deseja excluir esta mensagem?");
}

// Converter o texto do título para maiúsculas
document.getElementById('title').addEventListener('input', function () {
    this.value = this.value.toUpperCase();
});

// Validar o formulário
function validateForm() {
    var title = document.getElementById('title') ? document.getElementById('title').value : '';
    var content = document.getElementById('content') ? document.getElementById('content').value : '';
    var priority = document.getElementById('priority') ? document.getElementById('priority').value : '';
    var autor = document.getElementById('autor') ? document.getElementById('autor').value : '';

    if (title.trim() === '' || content.trim() === '' || priority === '' || autor === '') {
        alert('Por favor, preencha todos os campos.');
        return false; // Impede o envio do formulário
    }

    return true; // Permite o envio do formulário
}

// Alternar a visibilidade dos formulários conforme o tipo de conteúdo
function toggleForm() {
    var contentType = document.getElementById('contentType').value;
    document.getElementById('formAviso').style.display = (contentType === 'aviso') ? 'block' : 'none';
    document.getElementById('formInformacao').style.display = (contentType === 'informacao') ? 'block' : 'none';
    document.getElementById('formAniversario').style.display = (contentType === 'aniversario') ? 'block' : 'none';
}
