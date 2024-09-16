from flask import request, render_template, redirect, url_for, flash, jsonify
from db_utils import (
    insert_message, 
    get_messages, 
    get_information, 
    get_birthdays, 
    update_message, 
    delete_message, 
    add_info, 
    add_birthday, 
    get_resolved_messages  # Adicione aqui a função que estava faltando
)
from flask_socketio import SocketIO
import sqlite3
import datetime

socketio = SocketIO()

def setup_routes(app):
    @app.route('/check_message_edit/<int:message_id>')
    def check_message_edit(message_id):
        old_priority, old_datetime = update_message(message_id, "", "", "")
        new_priority, new_datetime = get_message_info(message_id)
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
            priority = request.form['priority']
            autor = request.form['autor']

            insert_message(title, content, priority, autor)
            flash('Mensagem enviada com sucesso', 'success')
            return redirect(url_for('admin'))

        messages = get_messages()
        resolved_messages = get_resolved_messages()
        return render_template('admin.html', messages=messages, resolved_messages=resolved_messages)

    @app.route('/messages')
    def view_messages():
        messages = get_messages()
        return render_template('messages.html', messages=messages)
    
    @app.route('/admin/add_info', methods=['GET', 'POST'])
    def add_info_route():
        if request.method == 'POST':
            title = request.form['infoTitle']
            content = request.form['infoContent']
            datetime_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Adicionando a informação ao banco de dados
            add_info(title, content)

            # Emitindo evento via SocketIO
            socketio.emit('info_updated', {
                'title': title,
                'content': content,
                'datetime': datetime_info
            })

            flash('Informação adicionada com sucesso!', 'success')
            return redirect(url_for('add_info_route'))

        return render_template('add_info.html')

    @app.route('/admin/add_aniversario', methods=['GET', 'POST'])
    def add_aniversario():
        if request.method == 'POST':
            nome = request.form['nomeAniversariante']
            data = request.form['dataAniversario']

            add_birthday(nome, data)
            flash('Aniversariante adicionado com sucesso!', 'success')

            socketio.emit('aniversario_updated', {
                'nome': nome,
                'data': data
            })

            return redirect(url_for('add_aniversario'))

        return render_template('add_aniversario.html')

    @app.route('/get_messages')
    def get_messages_json():
        categoria = request.args.get('categoria')
        autor = request.args.get('autor')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        messages = get_messages(categoria=categoria, autor=autor, data_inicio=data_inicio, data_fim=data_fim)
        formatted_messages = [
            {
                'id': msg[0],
                'title': msg[1],
                'content': msg[2],
                'priority': msg[3],
                'datetime': msg[4],
                'autor': msg[6],
                'likes': msg[7]
            }
            for msg in messages
        ]
        
        return jsonify(formatted_messages)

    @app.route('/get_resolved_messages')
    def get_resolved_messages_json():
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        resolved_messages = get_resolved_messages(data_inicio, data_fim)
        formatted_resolved_messages = [
            {
                'id': msg[0],
                'title': msg[1],
                'content': msg[2],
                'priority': msg[3],
                'datetime': msg[4],
                'category': msg[5]
            }
            for msg in resolved_messages
        ]
        
        return jsonify(formatted_resolved_messages)

    @app.route('/edit_message/<int:message_id>', methods=['GET', 'POST'])
    def edit_message_route(message_id):
        if request.method == 'POST':
            new_title = request.form['title']
            new_content = request.form['content']
            new_priority = request.form['priority']
            update_message(message_id, new_title, new_content, new_priority)
            flash('Mensagem editada com sucesso', 'success')
            return redirect(url_for('admin'))

        with sqlite3.connect('messages.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, priority, datetime FROM messages WHERE id=?", (message_id,))
            message = cursor.fetchone()

        if message:
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
            return redirect(url_for('admin'))
        except Exception as e:
            print(f"Erro ao excluir a mensagem: {e}")
            flash('Erro ao excluir a mensagem.', 'error')
            return redirect(url_for('admin'))

    @app.route('/get_filtered_resolved_messages')
    def get_filtered_resolved_messages():
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        resolved_messages = get_resolved_messages(data_inicio, data_fim)
        formatted_resolved_messages = [
            {
                'id': msg[0],
                'title': msg[1],
                'content': msg[2],
                'priority': msg[3],
                'datetime': msg[4],
                'category': msg[5]
            }
            for msg in resolved_messages
        ]
        
        return jsonify(formatted_resolved_messages)

    @app.route('/message_history')
    def view_message_history_page():
        messages = get_messages()
        return render_template('message_history.html', messages=messages)

    @app.route('/resolve_message/<int:message_id>', methods=['POST'])
    def resolve_message_route(message_id):
        update_message(message_id, "", "", "resolvido")
        flash('Mensagem marcada como resolvida', 'success')
        return redirect(url_for('admin'))
