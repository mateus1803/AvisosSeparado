from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
socketio = SocketIO(app)

# Configuração do banco de dados

DB_NAME = 'messages.db'


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Criação da tabela messages com a coluna 'likes'
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  priority TEXT NOT NULL,
                  datetime TEXT NOT NULL,
                  category TEXT,
                  autor TEXT,
                  likes INTEGER DEFAULT 0)''')  # Incluindo a coluna 'likes'

    # Verificar se a coluna 'likes' já existe
    cursor.execute("PRAGMA table_info(messages)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'likes' not in column_names:
        cursor.execute("ALTER TABLE messages ADD COLUMN likes INTEGER DEFAULT 0")
    
    if 'autor' not in column_names:
        cursor.execute("ALTER TABLE messages ADD COLUMN autor TEXT")

    if 'category' not in column_names:
        cursor.execute("ALTER TABLE messages ADD COLUMN category TEXT")

    # Criação da tabela message_history
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_history (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message_id INTEGER NOT NULL,
                  action TEXT NOT NULL,
                  datetime TEXT NOT NULL,
                  FOREIGN KEY(message_id) REFERENCES messages(id))''')
    
    # Criação da tabela information
    cursor.execute('''CREATE TABLE IF NOT EXISTS information (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  datetime TEXT NOT NULL)''')

    # Criação da tabela birthdays
    cursor.execute('''CREATE TABLE IF NOT EXISTS birthdays (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  birth_date TEXT NOT NULL,
                  added_on TEXT NOT NULL)''')
    
    conn.commit()
    conn.close()

# Função para inserir uma mensagem no banco de dados
def insert_message(title, content, priority, autor):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO messages (title, content, priority, datetime, autor) VALUES (?, ?, ?, ?, ?)", 
                   (title, content, priority, datetime_now, autor))  # Incluindo 'autor'
    conn.commit()
    conn.close()

# Função para obter todas as mensagens do banco de dados
def get_messages(categoria=None, autor=None, data_inicio=None, data_fim=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, title, content, priority, datetime, category, autor, likes FROM messages WHERE priority != 'resolvido'"
    params = []

    if categoria:
        query += " AND category = ?"
        params.append(categoria)
    if autor:
        query += " AND autor = ?"
        params.append(autor)
    if data_inicio:
        query += " AND datetime >= ?"
        params.append(data_inicio)
    if data_fim:
        query += " AND datetime <= ?"
        params.append(data_fim)
    
    # Ordenar por prioridade 'aviso' primeiro (datas mais recentes no topo) e depois por data descendentemente
    query += " ORDER BY CASE WHEN priority='aviso' THEN 0 ELSE 1 END, datetime DESC"

    cursor.execute(query, params)
    messages = cursor.fetchall()
    conn.close()
    return messages

def increment_likes(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Incrementar o número de curtidas
    cursor.execute("UPDATE messages SET likes = likes + 1 WHERE id = ?", (message_id,))
    conn.commit()

    # Obter o número atualizado de curtidas
    cursor.execute("SELECT likes FROM messages WHERE id = ?", (message_id,))
    likes = cursor.fetchone()[0]
    
    conn.close()

    # Emitir evento para atualizar as curtidas no frontend
    socketio.emit('update_likes', {'message_id': message_id, 'likes': likes})

# Função para obter as mensagens resolvidas do banco de dados
def get_resolved_messages(data_inicio=None, data_fim=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Base query para selecionar mensagens resolvidas
    query = "SELECT id, title, content, priority, datetime, category FROM messages WHERE priority='resolvido'"
    params = []
    
    # Adicionando filtros de data se disponíveis
    if data_inicio:
        # Ajuste o formato da data de entrada para corresponder ao formato no banco de dados
        data_inicio = datetime.datetime.strptime(data_inicio, '%d-%m-%Y').strftime('%d-%m-%Y 00:00:00')
        query += " AND datetime >= ?"
        params.append(data_inicio)
    if data_fim:
        data_fim = datetime.datetime.strptime(data_fim, '%d-%m-%Y').strftime('%d-%m-%Y 23:59:59')
        query += " AND datetime <= ?"
        params.append(data_fim)
    
    # Ordenar por data em ordem decrescente
    query += " ORDER BY datetime DESC"
    
    cursor.execute(query, params)
    resolved_messages = cursor.fetchall()
    conn.close()
    return resolved_messages

@socketio.on('like_message')
def handle_like_message(data):
    message_id = data['message_id']
    increment_likes(message_id)

    # Função para adicionar uma informação ao banco de dados
def add_info(title, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO information (title, content, datetime) VALUES (?, ?, ?)", 
                   (title, content, datetime_now))
    conn.commit()
    conn.close()

# Função para adicionar um aniversariante ao banco de dados
def add_birthday(name, birth_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO birthdays (name, birth_date, added_on) VALUES (?, ?, ?)", 
                   (name, birth_date, datetime_now))
    conn.commit()
    conn.close()

# Função para obter todas as informações do banco de dados
def get_information():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, datetime FROM information ORDER BY datetime DESC")
    info = cursor.fetchall()
    conn.close()
    return info

# Função para obter todos os aniversariantes do banco de dados
def get_birthdays():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, birth_date FROM birthdays ORDER BY birth_date")
    birthdays = cursor.fetchall()
    conn.close()
    return birthdays
  
# Função para editar uma mensagem no banco de dados
def update_message(message_id, new_title, new_content, new_priority):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, priority FROM messages WHERE id=?", (message_id,))
    old_title, old_content, old_priority = cursor.fetchone()
    
    cursor.execute("UPDATE messages SET title=?, content=?, priority=?, datetime=? WHERE id=?", 
                   (new_title or old_title, new_content or old_content, new_priority or old_priority, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), message_id))
    conn.commit()
    conn.close()

    # Emitir evento via WebSocket
    socketio.emit('message_updated', {'message_id': message_id, 'title': new_title or old_title, 'content': new_content or old_content, 'priority': new_priority or old_priority})

    if old_priority != 'resolvido' and new_priority == 'resolvido':
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO message_history (message_id, action, datetime) VALUES (?, ?, ?)", 
                       (message_id, 'resolvido', datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
        conn.commit()
        conn.close()
        

# Função para excluir uma mensagem do banco de dados
def delete_message(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE id=?", (message_id,))
    message = cursor.fetchone()
    if message:
        # Registra a exclusão no histórico antes de excluir a mensagem
        datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cursor.execute("INSERT INTO message_history (message_id, action, datetime) VALUES (?, ?, ?)", 
                       (message_id, 'exclusão', datetime_now))
        conn.commit()
        cursor.execute("DELETE FROM messages WHERE id=?", (message_id,))
        conn.commit()
        socketio.emit('message_deleted', {'message_id': message_id})  # Emite o evento de exclusão via WebSocket
    conn.close()

# Rota para verificar se a mensagem foi editada e obter o novo horário
@app.route('/check_message_edit/<int:message_id>')
def check_message_edit(message_id):
    old_priority, old_datetime = update_message(message_id, "", "", "")  # Chame a função de atualização sem fazer alterações
    new_priority, new_datetime = get_message_info(message_id)  # Obtenha as informações atualizadas da mensagem
    edited = (old_priority != new_priority or old_datetime != new_datetime)
    return jsonify({"edited": edited, "newDatetime": new_datetime})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        priority = request.form['priority']  # Campo de prioridade
        autor = request.form['autor']  # Capturando o autor do formulário
        
        insert_message(title, content, priority, autor)  # Incluindo o autor na inserção
        flash('Mensagem enviada com sucesso', 'success')
        return redirect(url_for('admin'))

    messages = get_messages()
    resolved_messages = get_resolved_messages()
    return render_template('admin.html', messages=messages, resolved_messages=resolved_messages)

@app.route('/messages')
def view_messages():
    messages = get_messages()
    return render_template('messages.html', messages=messages)


#######################################################################
# Rota para adicionar informações
@app.route('/admin/add_info', methods=['GET', 'POST'])
def add_info():
    if request.method == 'POST':
        title = request.form['infoTitle']
        content = request.form['infoContent']
        datetime_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        conn.execute('INSERT INTO informacoes (title, content, datetime) VALUES (?, ?, ?)',
                     (title, content, datetime_info))
        conn.commit()
        conn.close()

        flash('Informação adicionada com sucesso!', 'success')

        # Envia uma mensagem de atualização para os clientes conectados
        socketio.emit('info_updated', {
            'title': title,
            'content': content,
            'datetime': datetime_info
        })

        return redirect(url_for('add_info'))

    return render_template('add_info.html')

# Rota para adicionar aniversariantes

@app.route('/admin/add_aniversario', methods=['GET', 'POST'])
def add_aniversario():
    if request.method == 'POST':
        nome = request.form['nomeAniversariante']
        data = request.form['dataAniversario']

        conn = get_db_connection()
        conn.execute('INSERT INTO aniversarios (nome, data) VALUES (?, ?)', (nome, data))
        conn.commit()
        conn.close()

        flash('Aniversariante adicionado com sucesso!', 'success')

        # Envia uma mensagem de atualização para os clientes conectados
        socketio.emit('aniversario_updated', {
            'nome': nome,
            'data': data
        })

        return redirect(url_for('add_aniversario'))

    return render_template('add_aniversario.html')  # Mantido fora do bloco `if`

#########################################################

@app.route('/get_messages')
def get_messages_json():
    categoria = request.args.get('categoria')
    autor = request.args.get('autor')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    messages = get_messages(categoria=categoria, autor=autor, data_inicio=data_inicio, data_fim=data_fim)
    formatted_messages = [{'id': msg[0], 'title': msg[1], 'content': msg[2], 'priority': msg[3], 'datetime': msg[4], 'autor': msg[6], 'likes': msg[7]} for msg in messages]
    
    return jsonify(formatted_messages)


@app.route('/get_resolved_messages')
def get_resolved_messages_json():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Recuperar as mensagens resolvidas com os filtros de data
    resolved_messages = get_resolved_messages(data_inicio, data_fim)
    formatted_resolved_messages = [{'id': msg[0], 'title': msg[1], 'content': msg[2], 'priority': msg[3], 'datetime': msg[4], 'category': msg[5]} for msg in resolved_messages]
    
    return jsonify(formatted_resolved_messages)

@app.route('/edit_message/<int:message_id>', methods=['GET', 'POST'])
def edit_message_route(message_id):
    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        new_priority = request.form['priority']
        # Atualizar a mensagem no banco de dados
        update_message(message_id, new_title, new_content, new_priority)
        flash('Mensagem editada com sucesso', 'success')
        return redirect(url_for('admin'))

    # Recuperar a mensagem do banco de dados para edição
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, priority, datetime FROM messages WHERE id=?", (message_id,))
    message = cursor.fetchone()
    conn.close()

    if message:
        # message[4] contém a última data e hora atualizada da mensagem
        last_updated = message[4]
        return render_template('edit_message.html', message=message, last_updated=last_updated)
    else:
        flash('Mensagem não encontrada.', 'error')
        return redirect(url_for('admin'))

@app.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message_route(message_id):
    try:
        delete_message(message_id)
        flash('Mensagem excluída com sucesso.', 'success')
        return redirect(url_for('admin'))  # Redireciona de volta para a página de administração
    except Exception as e:
        print(f"Erro ao excluir a mensagem: {e}")
        flash('Erro ao excluir a mensagem.', 'error')
        return redirect(url_for('admin'))

@app.route('/get_filtered_resolved_messages')
def get_filtered_resolved_messages():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    # Recuperar as mensagens resolvidas com os filtros de data
    resolved_messages = get_resolved_messages(data_inicio, data_fim)

    # Formatar as mensagens para o formato JSON desejado
    formatted_resolved_messages = [
        {
            'id': msg[0],
            'title': msg[1],
            'content': msg[2],
            'priority': msg[3],
            'datetime': msg[4],
            'category': msg[5]  # Remover 'autor' já que não estamos mais filtrando por ele
        }
        for msg in resolved_messages
    ]
    
    return jsonify(formatted_resolved_messages)

@app.route('/message_history')
def view_message_history_page():
    # Obter todas as mensagens do banco de dados
    messages = get_messages()
    return render_template('message_history.html', messages=messages)

@app.route('/resolve_message/<int:message_id>', methods=['POST'])
def resolve_message_route(message_id):
    update_message(message_id, "", "", "resolvido")  # Marcar a mensagem como resolvida
    flash('Mensagem marcada como resolvida', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    create_tables()
    socketio.run(app, debug=True, host='192.168.1.58')
