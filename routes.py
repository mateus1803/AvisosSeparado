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
    get_resolved_messages
)
from flask_socketio import SocketIO
import sqlite3
import datetime

socketio = SocketIO()

from db_utils import get_messages  # Certifique-se de importar a função correta

def setup_routes(app):
    @app.route('/check_message_edit/<int:message_id>')
    def check_message_edit(message_id):
        try:
            # Obter todas as mensagens
            messages = get_messages()  # Pode ser necessário ajustar os parâmetros conforme sua necessidade
            old_message = next((msg for msg in messages if msg[0] == message_id), None)
            if not old_message:
                return jsonify({"error": "Mensagem não encontrada"}), 404
            
            # Suponha que a edição tenha ocorrido e você queira comparar com o novo estado
            # Obter as mensagens após a edição (a lógica pode precisar de ajuste)
            messages_after = get_messages()
            new_message = next((msg for msg in messages_after if msg[0] == message_id), None)
            if not new_message:
                return jsonify({"error": "Mensagem não encontrada"}), 404

            old_priority, old_datetime = old_message[3], old_message[4]  # Ajuste conforme o índice correto
            new_priority, new_datetime = new_message[3], new_message[4]  # Ajuste conforme o índice correto
            
            edited = (old_priority != new_priority or old_datetime != new_datetime)
            return jsonify({"edited": edited, "newDatetime": new_datetime})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/admin', methods=['GET', 'POST'])
    def admin():
        if request.method == 'POST':
            try:
                title = request.form['title']
                content = request.form['content']
                priority = request.form['priority']
                autor = request.form['autor']

                insert_message(title, content, priority, autor)
                flash('Mensagem enviada com sucesso', 'success')
            except Exception as e:
                flash(f'Erro ao enviar a mensagem: {e}', 'error')
            return redirect(url_for('admin'))

        messages = get_messages()
        resolved_messages = get_resolved_messages()
        return render_template('admin.html', messages=messages, resolved_messages=resolved_messages)
    
    @app.route('/get_information')
    def get_information_route():
        try:
            information = get_information()  # Função que retorna uma lista de informações do banco de dados
            formatted_information = [
                {"title": info[0], "content": info[1], "datetime": info[2]}
                for info in information
            ]
            return jsonify(formatted_information)
        except Exception as e:
            return jsonify({"error": str(e)}), 500




    @app.route('/messages')
    def view_messages():
        messages = get_messages()
        info_messages = get_information()  # Obtém informações do banco de dados
        birthdays = get_birthdays()  # Obtém aniversários do banco de dados
        return render_template('messages.html', messages=messages, info_messages=info_messages, birthdays=birthdays)

    
    @app.route('/admin/add_info', methods=['GET', 'POST'])
    def add_info_route():
        if request.method == 'POST':
            try:
                title = request.form['infoTitle']
                content = request.form['infoContent']
                datetime_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                add_info(title, content)

                socketio.emit('info_updated', {
                    'title': title,
                    'content': content,
                    'datetime': datetime_info
                })

                flash('Informação adicionada com sucesso!', 'success')
            except Exception as e:
                flash(f'Erro ao adicionar a informação: {e}', 'error')
            return redirect(url_for('view_messages'))

        return render_template('add_info.html')

    @app.route('/edit_info/<int:info_id>', methods=['GET', 'POST'])
    def edit_info_route(info_id):
            if request.method == 'POST':
                try:
                    new_title = request.form['title']
                    new_content = request.form['content']
                    update_info(info_id, new_title, new_content)
                    flash('Informação editada com sucesso', 'success')
                except Exception as e:
                    flash(f'Erro ao editar a informação: {e}', 'error')
                return redirect(url_for('admin'))

            try:
                with sqlite3.connect('messages.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, title, content, datetime FROM information WHERE id=?", (info_id,))
                    info = cursor.fetchone()

                if info:
                    return render_template('edit_info.html', info=info)
                else:
                    flash('Informação não encontrada.', 'error')
                    return redirect(url_for('admin'))
            except Exception as e:
                flash(f'Erro ao buscar a informação: {e}', 'error')
                return redirect(url_for('admin'))   
    

    @app.route('/delete_info/<int:info_id>', methods=['POST'])
    def delete_info_route(info_id):
        try:
            delete_info(info_id)
            flash('Informação excluída com sucesso.', 'success')
        except Exception as e:
            flash(f'Erro ao excluir a informação: {e}', 'error')
        return redirect(url_for('admin'))



        @app.route('/admin/add_birthday', methods=['GET', 'POST'])
        def add_birthday_route():
            if request.method == 'POST':
                name = request.form['birthdayName']
                birth_date = request.form['birthdayDate']
                add_birthday(name, birth_date)
                
                # Emitir evento para o frontend
                socketio.emit('birthday_updated', {'name': name, 'birth_date': birth_date})
                
                flash('Aniversário adicionado com sucesso!', 'success')
                return redirect(url_for('view_messages'))

            return render_template('add_birthday.html')




    @app.route('/admin/add_content', methods=['POST'])
    def add_content_route():
        try:
            content_type = request.form['content_type']
            title = request.form['title']
            content = request.form['content'] if content_type == 'info' else request.form['date']
            datetime_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if content_type == 'info':
                add_info(title, content)
                socketio.emit('info_updated', {
                    'title': title,
                    'content': content,
                    'datetime': datetime_info
                })
                flash('Informação adicionada com sucesso!', 'success')
            elif content_type == 'birthday':
                add_birthday(title, content)
                socketio.emit('aniversario_updated', {
                    'nome': title,
                    'data': content
                })
                flash('Aniversariante adicionado com sucesso!', 'success')
            else:
                flash('Tipo de conteúdo desconhecido.', 'error')

        except Exception as e:
            flash(f'Erro ao adicionar o conteúdo: {e}', 'error')
        return redirect(url_for('admin'))





    @app.route('/get_messages')
    def get_messages_json():
        try:
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/get_resolved_messages')
    def get_resolved_messages_json():
        try:
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/edit_message/<int:message_id>', methods=['GET', 'POST'])
    def edit_message_route(message_id):
        if request.method == 'POST':
            try:
                new_title = request.form['title']
                new_content = request.form['content']
                new_priority = request.form['priority']
                update_message(message_id, new_title, new_content, new_priority)
                flash('Mensagem editada com sucesso', 'success')
            except Exception as e:
                flash(f'Erro ao editar a mensagem: {e}', 'error')
            return redirect(url_for('admin'))

        try:
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
        except Exception as e:
            flash(f'Erro ao buscar a mensagem: {e}', 'error')
            return redirect(url_for('admin'))

    @app.route('/delete_message/<int:message_id>', methods=['POST'])
    def delete_message_route(message_id):
        try:
            delete_message(message_id)
            flash('Mensagem excluída com sucesso.', 'success')
        except Exception as e:
            flash(f'Erro ao excluir a mensagem: {e}', 'error')
        return redirect(url_for('admin'))

    @app.route('/get_filtered_resolved_messages')
    def get_filtered_resolved_messages():
        try:
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/message_history')
    def view_message_history_page():
        messages = get_messages()
        return render_template('message_history.html', messages=messages)

    @app.route('/resolve_message/<int:message_id>', methods=['POST'])
    def resolve_message_route(message_id):
        try:
            update_message(message_id, "", "", "resolvido")
            flash('Mensagem marcada como resolvida', 'success')
        except Exception as e:
            flash(f'Erro ao marcar a mensagem como resolvida: {e}', 'error')
        return redirect(url_for('admin'))
