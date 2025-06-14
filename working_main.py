from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote, unquote
import threading
from contextlib import contextmanager

# Minimal web server implementation
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess

# Importing components
from database import DatabaseManager   
from auth import AuthenticationManager
from car_manager import CarManager
from booking_manager import BookingManager
from gemini import GeminiIntegration   
from web import WebInterfacez
from security import SecurityUtils



application = Flask(__name__)
application.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(application)


CLI_COMMAND = ["python", "gemini.py"]

@application.route('/')
def index():
    return render_template('index.html')

def read_process_output(process):
    """Read stdout from your CLI app and send to frontend."""
    while True:
        output = process.stdout.readline().decode()
        if output:
            socketio.emit('app_output', {'output': output})
        else:
            break

@socketio.on('command')
def handle_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    output = stdout.decode() + stderr.decode()
    emit('output', output)


@socketio.on('app_input')
def handle_input(data):
    """Send user input to your CLI app's stdin."""
    global process
    process.stdin.write(data['input'].encode() + b'\n')
    process.stdin.flush()

@socketio.on('connect')
def connect():
    global process
    # Start your CLI app (not a shell!)
    process = subprocess.Popen(
        CLI_COMMAND,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        text=False
    )
    socketio.start_background_task(read_process_output, process)

if __name__ == '__main__':
    socketio.run(application, debug=True)
    application.run
