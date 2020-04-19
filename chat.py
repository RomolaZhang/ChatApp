from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)
users = {}
groups = {}

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/chat')
def chat():
    username = session.get('username')
    if username == '' or username == None:
        return redirect(url_for('index'))
    else:
        return render_template('chat.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form['username']
    if username not in users.keys():
        session['username'] = username
        myID = str(datetime.now().timestamp)
        users[username] = myID
        session['room'] = myID
        groups[username] = myID
        return redirect(url_for('chat'))
    else:
        error = 'This username is already taken.'
        return render_template('index.html', error=error)

@socketio.on('userList')
def sendUsers():
    otherUsers = []
    for user in users.keys():
        if user != session.get('username'):
            otherUsers.append(user)
    emit('activeUsers', {"users": otherUsers} )

@socketio.on('initRoom')
def initRoom():
    join_room(session['room'])

@socketio.on('join')
def joinUser(chosenUser):
    if chosenUser not in users.keys():
        emit('userGone', chosenUser)
    else:
        username = session['username']
        room = groups[chosenUser]
        members = ''
        number = 0
        for user in groups.keys():
            if groups[user] == room:
                members += (user + ' ')
                number = number + 1
        if number > 2:
            emit('roomFull')
        else:        
            members += username
            groups[username] = room
            leave_room(session['room'])
            oldRoom = session['room']

            oldMembers = ''
            for user in groups.keys():
                if groups[user] == oldRoom:
                    oldMembers += (user + ' ')
            msg = username + ' just left the room, current members: ' + oldMembers
            emit('message', {'msg': msg}, room=oldRoom)
            session['room'] = room
            join_room(room)
            msg = username + ' just entered the room, current members: ' + members
            emit('update')
            emit('message', {'msg': msg}, room=room)

@socketio.on('text')
def text(message):
    room = session['room']
    emit('message', {'msg': session['username'] + ': ' + message['msg']}, room=room)

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    username = session.get('username')
    session['username'] = ''
    del groups[username]
    del users[username]
    leave_room(room)
    members = ''
    for user in groups.keys():
        if groups[user] == room:
            members += (user + ' ')
    msg = username + ' just left the room, current members: ' + members
    emit('message', {'msg': msg}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)