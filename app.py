from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import datetime
from db_utils import create_tables
from routes import setup_routes

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
socketio = SocketIO(app)

# Configurações e inicialização do banco de dados
create_tables()

# Configuração das rotas
setup_routes(app)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='192.168.1.58')

   
    socketio.init_app(app)
