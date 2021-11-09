from flask import Flask, render_template, url_for, request, jsonify, flash, redirect
from flask_sqlalchemy import SQLAlchemy
import csv
import os
import base64
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class PolicyDB(db.Model):

    PolicyId = db.Column(db.Integer, primary_key=True)
    PurchaseDate = db.Column(db.Date)
    CustomerId = db.Column(db.Integer)
    Fuel = db.Column(db.String(5))
    Segment = db.Column(db.String(2))
    Premium = db.Column(db.Float)
    BodInjLiab = db.Column(db.String(1))
    PersInjProt = db.Column(db.String(1))
    PropDamageLiab = db.Column(db.String(1))
    Collision = db.Column(db.String(1))
    Comprehensive = db.Column(db.String(1))
    Gender = db.Column(db.String(12))
    IncomeGroup = db.Column(db.String(30))
    Region = db.Column(db.String(10))
    MaritalStatus = db.Column(db.String(1))

    def __repr__(self):
        return f"PolicyId : ({self.PolicyId}, CustomerId: {self.CustomerId}, PurchaseDate: {self.PurchaseDate})"


db.drop_all()
db.create_all()
db.session.commit()

@app.route("/status")
@app.route("/")
def status():
    return jsonify({'message': 'Server is up & running', 'status': 'ok'})

@app.route("/refreshData", methods=["GET"])
def load_data():

    file_name = "client.csv"
    if os.path.exists(file_name):
        with open(file_name, 'r') as fh:
            rows = list(csv.DictReader(fh))

            if len(rows) == 0:
                return {'status': False, 'message': 'Empty csv file', 'data': []}

            for row in rows:
                purchase_date = datetime.strptime(row["Date of Purchase"], "%m/%d/%Y")

                policy = PolicyDB(PolicyId = row["Policy_id"], PurchaseDate = purchase_date,
                                CustomerId = row["Customer_id"], Fuel = row["Fuel"], Segment = row["VEHICLE_SEGMENT"],
                                Premium = row["Premium"], BodInjLiab = row["bodily injury liability"],
                                PersInjProt = row[" personal injury protection"],
                                PropDamageLiab = row[" property damage liability"], Collision = row[" collision"],
                                Comprehensive = row[" comprehensive"], Gender = row["Customer_Gender"],
                                IncomeGroup = row["Customer_Income group"], Region = row["Customer_Region"],
                                MaritalStatus = row["Customer_Marital_status"])
                db.session.add(policy)
                db.session.commit()
        return {'status': True, 'message': f"Rows {len(rows)} uploaded successfully"}
    return {'status': False, 'message': 'Unable to find file', 'data': []}


@app.route("/data", methods=["GET"])
def get_data():
    page_num = request.arge.get("pageNo", default=1)
    limit = request.args.get("limit", default=10)

    db_game_obj = db.session.query(PolicyDB).order_by(PolicyId)
    return render_template("game/new.html")


@app.route("/data", methods=["POST"])
def update_data():

    policy_id = request.args.get("policyId")
    policy_obj = db.session.query(PolicyDB).filter_by(PolicyId=policy_id)
    db_policy = policy_obj.first()
    if db_policy is None:
        return jsonify({'message': f"Unable to find the policy.", 'status': False})

    game_status = db_policy.status.lower()
    if game_status == 'completed':
        return jsonify({'message': f"{db_game.name} game is already completed. Create a new game to play.",
                        'status': True})
    customer_id = request.args.get("customerId")
    policy_obj.update({PolicyDB.CustomerId: customer_id})
    db.session.commit()
    return jsonify({'message': f"Policy updated successfully.", 'status': False})

@app.route("/search")
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


if __name__ == '__main__':
    print(f"Running the server")
    app.run(debug=False)