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

    # Verificar se as colunas 'likes', 'autor' e 'category' já existem
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
def insert_message(title, content, priority, autor, categoria=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("INSERT INTO messages (title, content, priority, datetime, autor, category) VALUES (?, ?, ?, ?, ?, ?)", 
                   (title, content, priority, datetime_now, autor, categoria))
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

def get_resolved_messages(data_inicio=None, data_fim=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, title, content, priority, datetime, category FROM messages WHERE priority='resolvido'"
    params = []
    
    if data_inicio:
        data_inicio = datetime.datetime.strptime(data_inicio, '%d-%m-%Y').strftime('%d-%m-%Y 00:00:00')
        query += " AND datetime >= ?"
        params.append(data_inicio)
    if data_fim:
        data_fim = datetime.datetime.strptime(data_fim, '%d-%m-%Y').strftime('%d-%m-%Y 23:59:59')
        query += " AND datetime <= ?"
        params.append(data_fim)
    
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

 
    def update_info(info_id, new_title, new_content):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM information WHERE id=?", (info_id,))
        old_title, old_content = cursor.fetchone()
        
        cursor.execute("UPDATE information SET title=?, content=?, datetime=? WHERE id=?", 
                    (new_title or old_title, new_content or old_content, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), info_id))
        conn.commit()
        conn.close()
        
        # Emitir evento via WebSocket
        socketio.emit('info_updated', {'info_id': info_id, 'title': new_title or old_title, 'content': new_content or old_content})

    def get_info_by_id(info_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM information WHERE id=?", (info_id,))
        info = cursor.fetchone()
        conn.close()
        return info



    def delete_info(info_id):
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM information WHERE id=?", (info_id,))
        conn.commit()
        conn.close()


def setup_routes(app):
    @app.route('/check_message_edit/<int:message_id>')
    def check_message_edit(message_id):
        try:
            # Obter a mensagem antes da edição
            messages_before = get_messages(autor=None, categoria=None, data_inicio=None, data_fim=None)
            old_message = next((msg for msg in messages_before if msg[0] == message_id), None)
            if not old_message:
                return jsonify({"error": "Mensagem não encontrada"}), 404
            
            # Supondo que a edição tenha ocorrido e você quer comparar com o novo estado
            # Aqui você precisa obter o novo estado da mensagem, por exemplo:
            messages_after = get_messages(autor=None, categoria=None, data_inicio=None, data_fim=None)
            new_message = next((msg for msg in messages_after if msg[0] == message_id), None)
            if not new_message:
                return jsonify({"error": "Mensagem não encontrada"}), 404

            old_priority, old_datetime = old_message[3], old_message[4]  # Ajuste conforme o índice correto
            new_priority, new_datetime = new_message[3], new_message[4]  # Ajuste conforme o índice correto
            
            edited = (old_priority != new_priority or old_datetime != new_datetime)
            return jsonify({"edited": edited, "newDatetime": new_datetime})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Função para excluir uma mensagem do banco de dados
def delete_message(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE id=?", (message_id,))
    message = cursor.fetchone()
    if message:
        datetime_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cursor.execute("INSERT INTO message_history (message_id, action, datetime) VALUES (?, ?, ?)", 
                       (message_id, 'exclusão', datetime_now))
        conn.commit()
        cursor.execute("DELETE FROM messages WHERE id=?", (message_id,))
        conn.commit()
        socketio.emit('message_deleted', {'message_id': message_id})
    conn.close()

