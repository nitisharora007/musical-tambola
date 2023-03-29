from flask import Flask, render_template, url_for, request, jsonify, flash, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import csv
import os
import random
import base64
import smtplib
import email.message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


ALLOWED_EXT = {'csv'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FILE_PATH")
app.config['SONGS_DIRECTORY'] = os.getenv("SONGS_DIRECTORY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['FROM_EMAIL'] = os.getenv("FROM_EMAIL")
app.config['BCC_EMAIL'] = os.getenv("BCC_EMAIL")
app.config['CC_EMAIL'] = os.getenv("CC_EMAIL")
app.config['SMTP_SERVER'] = os.getenv("SMTP_SERVER")
app.config['SUBJECT_EMAIL'] = os.getenv("SUBJECT_EMAIL")
app.config['SEND_EMAIL'] = True if int(os.getenv("IS_SEND_EMAIL")) > 0 else False
app.config['BASE_URL'] = os.getenv("BASE_URL") if os.getenv("BASE_URL") != "" else request.url

db = SQLAlchemy(app)
#game_status = ["created", "running", "completed"]
songs_path = app.config['SONGS_DIRECTORY']


class Game(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    code = db.Column(db.String(30), unique=True)        # auto-generated
    status = db.Column(db.String(30))      # Starting, Playing, Completed

    def __repr__(self):
        return f"Game({self.name}, {self.code}, {self.status})"


class Player(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    email = db.Column(db.String(40), unique=True, nullable=False)

    def __repr__(self):
        return f"Player({self.name}, {self.email})"


class GamePlayer(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)             # reference to the Game
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)       # reference to Player
    ticket_code = db.Column(db.String(40), default='', nullable=False)

    def __repr__(self):
        return f"GamePlayer({self.ticket_code}, {self.game_id}, {self.player_id})"


class GameTicket(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    game_player_id = db.Column(db.Integer, db.ForeignKey('game_player.id'), nullable=False)  # reference to the GamePlayer
    col1 = db.Column(db.String(40))
    col2 = db.Column(db.String(40))
    col3 = db.Column(db.String(40))
    col4 = db.Column(db.String(40))
    col5 = db.Column(db.String(40))
    col6 = db.Column(db.String(40))

    def __repr__(self):
        return f"GameTicket({self.game_player_id}, {self.col1}, {self.col2}, {self.col3}, {self.col4}, {self.col5}, {self.col6})"


class GameSong(db.Model):

    game_song_id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer)       # reference to the Game
    song_name = db.Column(db.Integer)        # reference to user-id

    def __repr__(self):
        pass


#db.drop_all()
db.create_all()
db.session.commit()


def allowed_ext(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def read_csv(file_path):

    data = []

    if os.path.exists(file_path):
        with open(file_path, 'r') as fh:
            rows = list(csv.DictReader(fh))

            if len(rows) == 0:
                return {'status': False, 'message': 'Empty csv file uploaded', 'data': []}

            col_names = dict((rows[0]))
            if 'Email' not in col_names.keys():
                return {'status': False, 'message': 'Email field not found in the csv', 'data': []}
            if 'Name' not in col_names.keys():
                return {'status': False, 'message': 'Name field not found in the csv', 'data': []}

            for row in rows:
                data.append(row)
        return {'status': True, 'message': 'File uploaded successfully', 'data': data}
    return {'status': False, 'message': 'Unable to find file', 'data': []}


songs = [fl for fl in os.listdir(songs_path) if fl.endswith(".mp3")]
print(songs)

u1 = {'name': 'Nitish Arora', 'email': 'niaro@danskeit.co.in'}
u2 = {'name': 'Suman', 'email': 'sum@danskeit.co.in'}
users = [u1, u2]


def get_random_song():

    return songs[random.randrange(0, len(songs))]


def create_ticket():
    ticket = []
    ticket_songs = []

    for i in range(0, 3):
        cols = ['' for j in range(0, 6)]
        j = 0
        while j < 3:
            col_idx = random.randrange(0, len(cols))
            song = get_random_song()
            # print(f"Generated song {song} for col: {col_idx}")
            if song not in ticket_songs and cols[col_idx] == '':
                ticket_songs.append(song)
                cols[col_idx] = song
                j += 1
        ticket.append(cols)

    print(ticket)
    return ticket


def send_email(name, ticket_code, gm_plyr_id, email):

    db_game_ticket = db.session.query(GameTicket).filter_by(game_player_id=gm_plyr_id).all()
    if db_game_ticket is None:
        print(f"Unable to fetch the game ticket for email {email}")
        return False

    ticket = []
    for game_ticket in db_game_ticket:
        row = [game_ticket.col1, game_ticket.col2, game_ticket.col3, game_ticket.col4, game_ticket.col5, game_ticket.col6 ]
        ticket.append(row)

    # TODO: Use the from-email in env. variables
    email_message = MIMEMultipart('alternative')
    email_message['From'] = app.config['FROM_EMAIL']
    email_message['To'] = email
    if app.config['CC_EMAIL'] != "":
        email_message['Cc'] = app.config['CC_EMAIL']
    email_message['Bcc'] = app.config['BCC_EMAIL']
    email_message['Subject'] = app.config['SUBJECT_EMAIL']
    content = render_template("game/ticket-email.html", name=name, ticket_code=ticket_code, ticket=ticket,
                              email=email, base_url=app.config['BASE_URL'])
    print(f"MailContent: {content}")
    email_message.attach(MIMEText(content, 'html'))

    try:
        if app.config['SEND_EMAIL']:
            print(f"Sending email: {email}")
            with smtplib.SMTP(host=app.config['SMTP_SERVER'], port=25) as server:
                server.connect(app.config['SMTP_SERVER'], 25)
                server.send_message(email_message)
        return True
    except Exception as e:
        print(f"Error in sending email: {email}")
        return False


# Return true if ticket generation is successful
def write_ticket(game_player_id, email):

    print(f"Generating ticket for {email}")
    ticket = create_ticket()

    if len(ticket) <= 0:
        print(f"Unable to generate the ticket for {email}")
        return False

    for row in ticket:
        gt = GameTicket(game_player_id=game_player_id, col1=row[0], col2=row[1], col3=row[2], col4=row[3], col5=row[4],
                        col6=row[5])
        db.session.add(gt)
        db.session.commit()
        print(f"Added game ticket for {email}, tid: {gt.id}")

    return True

# TODO: Can be done later on
def send_all_tickets(gcode):
    # TODO1: Get all the users for the game code

    u1 = {'name': 'Nitish Arora', 'email': 'niaro@danskeit.co.in'}
    u2 = {'name': 'Suman', 'email': 'sum@danskeit.co.in'}
    users = [u1, u2]

    # TODO2: Get the ticket for the user

    for elem in users:
        tckt = create_ticket()


# Ticket code for every user
def generate_ticket_code(email):
    print(f"Generating ticket code for {email}")
    return f"{email[:3]}{random.randint(10, 1000)}"


# Generate the game code for playing
def generate_game_code(name):
    return f"MT-{name[:2].upper()}-{random.randint(1,10000)}"


# AJAX Calls Start

# Get the game details of previously created
@app.route("/get-game-details")
def get_game_details():

    game_code = request.args.get("gcode")
    start_game = False

    if game_code is None or game_code == "":
        return jsonify({'message': 'Unable to get the game details, as game code is empty', 'status': False,
                        'players': [], 'start_game': start_game})

    game_code = request.args.get("gcode")
    start_game = False
    if game_code == '' or game_code is None:
        return jsonify({'message': 'Require the game code to be passed', 'start_game': start_game})

    db_game = db.session.query(Game).filter_by(code=game_code).first()
    if db_game is None:
        return jsonify({'message': 'Invalid game-code is passed', 'start_game': start_game})

    status = db_game.status.lower()
    if status == 'completed':  # Tickets can be generated, if status is created for game.
        return jsonify({'message': 'Game is either running or completed', 'start_game': start_game})

    if status.lower() == 'created':        # Game can be in running stage, then no-one can start the game
        start_game = True

    db_gm_players = db.session.query(GamePlayer).filter_by(game_id=db_game.id).all()
    players = []

    for game_player in db_gm_players:

        db_player = db.session.query(Player).filter_by(id=game_player.player_id).first()
        player = {'name': db_player.name, 'email': db_player.email}
        players.append(player)

    if len(players) == 0:
        start_game = False
    return jsonify({'message': '', 'status': True, 'players': players, 'start_game': start_game})


# Post the files to the create-game, it will return the game code, No. of Users
@app.route("/create-game", methods=["POST"])
def create_game():

    # get the file in post or get method and starts processing it
    game_name = request.form['gameName']
    file = request.files['uploadFile']
    if game_name is None or game_name == "":
        game_name = "Musical Tambola"

    gcode = generate_game_code(game_name)

    base_file_path = app.config['UPLOAD_FOLDER']

    file_path = os.path.join(base_file_path, gcode + ".csv")
    if not os.path.exists(base_file_path):
        os.makedirs(base_file_path)
    file.save(file_path)
    print(f"Saved the file @ {file_path}")
    fl_details = read_csv(file_path)

    if not fl_details['status']:
        return jsonify({'message': fl_details['message'], 'status': False, 'game_code': '', 'players': []})
    players = fl_details['data']

    game = Game(name=game_name, code=gcode, status='created')
    db.session.add(game)
    db.session.commit()

    for elem in players:

        db_player = db.session.query(Player).filter_by(email=elem['Email']).first()

        if db_player is None:
            player = Player(name=elem['Name'], email=elem['Email'])
            db.session.add(player)
            db.session.commit()
            db_player = player

        game_player = GamePlayer(game_id=game.id, player_id=db_player.id)
        db.session.add(game_player)
        db.session.commit()

        print(db_player)
        print(game_player)
        print(f"GameId: {game.id}, PlayerId: {db_player.id}, GamePlayer: {game_player.id}")

    print(game)

    return jsonify({'message': f'Game has been created successfully with {len(players)} players', 'game_code': gcode,
                    'players': players, 'status': True})


# Return the stats about the ticket generation for users
@app.route("/generate-tickets")
def generate_ticket():

    game_code = request.args.get("gcode")
    start_game = False
    if game_code == '' or game_code is None:
        return jsonify({'message': 'Require the game code to be passed', 'start_game': start_game})

    db_game = db.session.query(Game).filter_by(code=game_code).first()

    if db_game is None:
        return jsonify({'message': 'Invalid game-code is passed', 'start_game': start_game})

    status = db_game.status.lower()

    if status != 'created':        # Tickets can be generated, if status is created for game.
        return jsonify({'message': 'Game is either running or completed', 'start_game': start_game})

    db_gm_players = db.session.query(GamePlayer).filter_by(game_id=db_game.id).all()
    tkt_count = email_cnt = 0
    tkt_fail = []
    email_fail = []

    for game_player in db_gm_players:

        ticket_exists = db.session.query(GameTicket).filter_by(game_player_id=game_player.id).first()
        player = db.session.query(Player).filter_by(id=game_player.player_id).first()
        print(game_player)
        print(player)
        if ticket_exists is None:
            if write_ticket(game_player.id, player.email):
                tkt_count += 1
                ticket_exists = True

            else:
                tkt_fail.append(player.email)
        else:
            tkt_count += 1

        db_ticket_code = game_player.ticket_code
        if db_ticket_code is None or db_ticket_code == '':
            db_ticket_code = generate_ticket_code(player.email)
            print(f"Ticket Code generated: {db_ticket_code}")
            gp = db.session.query(GamePlayer).filter_by(id=game_player.id)
            gp.update({GamePlayer.ticket_code: db_ticket_code})
            db.session.commit()

        if ticket_exists and send_email(player.name, db_ticket_code, game_player.id, player.email):
            email_cnt += 1
        else:
            email_fail.append(player.email)

    if tkt_count > 0 and email_cnt > 0:
        start_game = True

    message = f"Tickets generated: {tkt_count}, Email Sent: {email_cnt}."
    if len(tkt_fail) > 0:
        message += f' Unable to generate tickets for {",".join(tkt_fail)}.'

    if len(email_fail) > 0:
        message += f' Error in sending email for {",".join(email_fail)}.'

    return jsonify({'message': message, 'start_game': start_game})


@app.route("/next-song")
def next_song():

    game_code = request.args.get("gcode")
    if game_code is None or game_code == '':
        return jsonify({'message': 'Game code is not provided to send the next song', 'song': ''})

    db_game = db.session.query(Game).filter_by(code=game_code).first()
    if db_game is None:
        return jsonify({'message': f"Unable to find the game code {game_code}", 'song': ''})

    db_game_songs = db.session.query(GameSong).filter_by(game_id=db_game.id).all()
    songs_played = []
    if db_game_songs is not None:
        for game_song in db_game_songs:
            songs_played.append(game_song.song_name)

    print(f"GameCode: {game_code}, SongsPlayed: {songs_played}")

    song = None
    while song is None:
        song = songs[random.randrange(0, len(songs))]
        print(song)
        if song in songs_played:
            song = None
        print(f"Songs: {len(songs)}, SongsPlayed: {len(songs_played)}")
        if len(songs_played) >= len(songs):
            return {'message': 'Hope, you enjoyed the game. All songs in the game had been played & you can end this game. If you want to play more, create a new game. STAY SAFE & ENJOY PLAYING !!! ', 'song': ''}

    game_song = GameSong(game_id=db_game.id, song_name=song)
    db.session.add(game_song)
    db.session.commit()

    return {'message': '', 'song': song}


@app.route('/cut-song')
def cut_song():

    tcode = request.args.get("tcode")
    row = request.args.get("row")
    col = request.args.get("col")
    song = request.args.get("song")

    if tcode is None or tcode == "":
        return jsonify({'message': 'Unable to fetch the ticket for which the song is crossed', 'status': False,
                        'row': row, 'col': col})

    if row == "" or row is None:
        return jsonify({'message': 'Unable to fetch the row for which the song is crossed', 'status': False,
                        'row': row, 'col': col})

    if col == "" or col is None:
        return jsonify({'message': 'Unable to fetch the column for which the song is crossed', 'status': False,
                        'row': row, 'col': col})

    if song is None or song == "":
        return jsonify({'message': 'Please provide the song to be cut.', 'status': False,
                        'row': row, 'col': col})

    db_game_player = db.session.query(GamePlayer).filter_by(ticket_code=tcode).first()
    if db_game_player is None:
        return jsonify({'message': f'Unable to find the game ticket with code {tcode}', 'status': False,
                        'row': row, 'col': col})

    db_game_songs = db.session.query(GameSong).filter_by(game_id=db_game_player.game_id).all()
    songs_played = []
    if db_game_songs is not None:
        for game_song in db_game_songs:
            songs_played.append(game_song.song_name)

    print(f"SongsPlayed: {songs_played}")
    if song not in songs_played:
        return jsonify({'message': f'Song {song} not played in the game', 'status': False,
                        'row': row, 'col': col})

    db_game_ticket = db.session.query(GameTicket).filter_by(game_player_id=db_game_player.id).all()
    found = False
    for game_ticket in db_game_ticket:
        ticket_songs = {game_ticket.col1, game_ticket.col2, game_ticket.col3, game_ticket.col4, game_ticket.col5,
                        game_ticket.col6}
        if song in ticket_songs:
            found = True
            break

    return jsonify({'message': '', 'status': found, 'row': row, 'col': col})


@app.route('/get-played-songs')
def get_played_songs():

    tcode = request.args.get("tcode")
    game_code = request.args.get("gcode")
    db_game_songs = None

    if game_code == '' and tcode == "":
        return jsonify({'message': 'Unable to fetch the game.', 'songs': []})

    if game_code == "":         # ticket code is specified
        db_game_player = db.session.query(GamePlayer).filter_by(ticket_code=tcode).first()
        if db_game_player is None:
            return jsonify({'message': f'Unable to fetch the ticket for which the songs played', 'songs': []})
        db_game_songs = db.session.query(GameSong).filter_by(game_id=db_game_player.game_id).all()
    else:                       # game code is specified
        db_game = db.session.query(Game).filter_by(code=game_code).first()
        if db_game is None:
            return jsonify({'message': f"Unable to find the game code {game_code}", 'song': ''})
        db_game_songs = db.session.query(GameSong).filter_by(game_id=db_game.id).all()

    if db_game_songs is None:
        return jsonify({'message': f"Unable to find the game songs", 'song': []})

    songs_played = []
    if db_game_songs is not None:
        for game_song in db_game_songs:
            songs_played.append(game_song.song_name)

    print(f"SongsPlayed: {songs_played}")
    return jsonify({'message': '', 'songs': songs_played})


@app.route('/game-completed')
def game_completed():

    game_code = request.args.get('gcode')
    if game_code is None or game_code == '':
        return jsonify({'message': 'Game code is not provided to end the game', 'status': False})

    db_game_obj = db.session.query(Game).filter_by(code=game_code)
    db_game = db_game_obj.first()
    if db_game is None:
        return jsonify({'message': f"Unable to find the game to mark complete.", 'status': False})

    game_status = db_game.status.lower()
    if game_status == 'completed':
        return jsonify({'message': f"{db_game.name} game is already completed. Create a new game to play.",
                        'status': True})

    db_game_obj.update({Game.status: 'completed'})
    db.session.commit()
    return jsonify({'message': f"{db_game.name} game is completed. Thanks a lot for playing.",
                    'status': False})

# AJAX Calls Ends

@app.route("/status")
def status():
    return jsonify({'message': 'Game is up & running', 'status': 'ok'})


@app.route("/")
def home():
    return render_template("home.html", hide_logo=True)


@app.route("/new-game")
def new_game():
    return render_template("game/new.html")


@app.route("/view-game")
def view_game():

    return render_template("game/view.html", users=users)


@app.route("/play-game")
def play_game():

    game_code = request.args.get("gcode")
    if game_code is None or game_code == '':
        return render_template("error.html", error="In-valid URL used for playing the game")

    game_code = str(base64.b64decode(game_code), 'utf-8')

    db_game_obj = db.session.query(Game).filter_by(code=game_code)
    db_game = db_game_obj.first()
    if db_game is None:
        return render_template("error.html", error="Unable to find the game. Please create a new game.")

    game_status = db_game.status.lower()
    if game_status == 'completed':
        return render_template("error.html", error="Game has been completed. Please create a new game.")

    db_game_obj.update({Game.status: 'running'})
    db.session.commit()

    db_players = db.session.query(GamePlayer).filter_by(game_id=db_game.id).all()

    players = []

    for game_player in db_players:

        db_player = db.session.query(Player).filter_by(id=game_player.player_id).first()
        print(game_player)
        print(db_player)
        player = {'name': db_player.name, 'email': db_player.email, 'tcode': game_player.ticket_code}
        players.append(player)

    return render_template("game/play.html", gname=db_game.name, players=players,gcode=game_code)


@app.route("/view-ticket")
def view_ticket():

    if request.args.get('tcode') is None or request.args.get('tcode') == '':
        return render_template("error.html", error="In-valid URL used for viewing the ticket")

    tcode = request.args.get("tcode")
    user_email = request.args.get("email")  # Get parameter

    if tcode is None or tcode == "":
        return render_template("error.html", error="Ticket code was not found")

    if user_email is None or user_email == "":
        return render_template("error.html", error="Email was not found")

    db_game_player = db.session.query(GamePlayer).filter_by(ticket_code=tcode).first()
    if db_game_player is None:
        return render_template("error.html", error=f"Ticket code {tcode} not found. Please use the valid ticket code.")

    db_player = db.session.query(Player).filter_by(id=db_game_player.player_id).first()
    if user_email != db_player.email:
        return render_template("error.html", error=f"Mismatch between Ticket code {tcode} & Email {user_email}")

    db_game = db.session.query(Game).filter_by(id=db_game_player.game_id).first()
    if db_game.status == 'completed':
        return render_template("error.html", error=f"Thanks a lot for playing the game. It had been completed.")

    db_game_ticket = db.session.query(GameTicket).filter_by(game_player_id=db_game_player.id).all()
    if db_game_ticket is None:
        return render_template("error.html", error=f"Unable to find the ticket with details provided.")

    print(db_game_ticket)
    ticket = []
    for game_ticket in db_game_ticket:
        row = [game_ticket.col1, game_ticket.col2, game_ticket.col3, game_ticket.col4, game_ticket.col5, game_ticket.col6]
        ticket.append(row)

    tckt_dtls = {'name': db_player.name, 'email': db_player.email, 'ticket': ticket, 'code': tcode}
    # Get the list of rows & cols from the ticket based upon the ticket_code and user details
    return render_template("game/view-ticket.html", ticket=tckt_dtls)

@app.route('/send-ticket')
def send_ticket_email():

    ticket= [['Seeti Maar.mp3', '', '', 'Blue Eyes.mp3', 'womaniya.mp3', ''], ['', '', '', 'Lungi dance.mp3', 'All is Well.mp3', 'Nakka Mukka.mp3'], ['inkem inkem .mp3', '', '', '', 'Gangan Style.mp3', 'Paani Paani.mp3']]
    return render_template("game/ticket-email.html", name="Nitish Arora", ticket_code="TC-123123", ticket=ticket,
                              email="email", base_url=app.config['BASE_URL'])
