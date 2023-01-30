from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import datetime as dt
import random
import string
import requests

load_dotenv("keys.env")
KEY = os.getenv("SHORTY_KEY")
ADMIN = os.getenv("ADMIN_KEY")

shorty = Flask(__name__)
shorty.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shorty.db"
shorty.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
shorty.config["JSON_SORT_KEYS"] = False
db = SQLAlchemy(shorty)
shorty.config["SECRET_KEY"] = KEY
creation_time = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


class Urls(db.Model):
    __tablename__ = "urls"
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(200), nullable=False)
    short_url = db.Column(db.String(50), nullable=False, )
    time = db.Column(db.String(50), nullable=False)


with shorty.app_context():
    db.create_all()


@shorty.route("/all", methods=['GET'])
def all_urls():
    if request.method == 'GET':
        json_all = {}
        all_created = Urls.query.all()
        if len(all_created) == 0:
            return jsonify(response={"succes": "no records done yet"}), 200
        else:
            for _ in all_created:
                json_all[f'{_.id}'] = {
                    "id": _.id,
                    "original_url": _.long_url,
                    "shortened_url": _.short_url,
                    "creation_time": _.time,
                }
                return jsonify(json_all), 200
    else:
        return jsonify(response={"error": "Incorrect method. Only GET allowed."}), 405


@shorty.route("/add", methods=['POST'])
def add_url():
    if request.method == 'POST':
        urls = request.args.getlist('url_to')
        not_responding = []
        session = requests.Session()
        for _ in urls:
            try:
                con = session.head(_, timeout=4)
                if con.status_code >= 400:
                    not_responding.append(_)
            except requests.exceptions.ConnectionError:
                not_responding.append(_)
        session.close()
        urls = [url for url in urls if url not in not_responding]
        used = Urls.query.with_entities(Urls.short_url).all()
        if len(urls) == 0:
            return jsonify(
                response={"There's no URL given or all of them are not responding.": not_responding}
                          ), 200
        elif len(urls) == 1:
            if Urls.query.filter_by(long_url=urls[0]).first():
                short_url = Urls.query.filter_by(long_url=urls[0]).first().short_url
                return jsonify(
                    response={f'long id{Urls.query.filter_by(long_url=urls[0]).first().id} - {urls[0]}':
                              f'existed short- {short_url}'}
                              ), 200
            else:
                while True:
                    new_short = request.url_root + ''.join(random.choices(string.ascii_letters + string.digits, k=3))
                    if new_short not in used:
                        new_data = Urls(long_url=urls[0],
                                        short_url=new_short,
                                        time=creation_time,
                                        )
                        db.session.add(new_data)
                        db.session.commit()
                        return jsonify(
                            response={f'long id{Urls.query.filter_by(long_url=urls[0]).first().id} - {urls[0]}':
                                      f'new short - {new_short}'}
                                      ), 200
        elif len(urls) > 1:
            answers = {}
            for element in urls:
                stop = False
                if Urls.query.filter_by(long_url=element).first():
                    answers[f'long id{Urls.query.filter_by(long_url=element).first().id}- {element}'] = \
                        f'existed short - {Urls.query.filter_by(long_url=element).first().short_url}'
                else:
                    while not stop:
                        new_short = request.url_root + ''.join(
                            random.choices(string.ascii_letters + string.digits, k=3))
                        if new_short not in used:
                            new_data = Urls(long_url=element,
                                            short_url=new_short,
                                            time=creation_time,
                                            )
                            db.session.add(new_data)
                            db.session.commit()
                            answers[f'long id{Urls.query.filter_by(long_url=element).first().id} - {element}'] = \
                                f'new short - {Urls.query.filter_by(long_url=element).first().short_url}'
                            stop = True
            return jsonify(response=answers), 200
    else:
        return jsonify(response={"error": "Incorrect method. Only POST allowed."}), 405


@shorty.route("/clear", methods=["POST"])
def clearing_db():
    if request.method == "POST" and request.args.get("API_KEY"):
        if len(Urls.query.all()) == 0:
            return jsonify(response={"succes": "There's was no records in DB"}), 200
        elif request.args.get("API_KEY") == ADMIN:
            for _ in Urls.query.all():
                db.session.delete(_)
            db.session.commit()
            return jsonify(response={"succes": "all records cleared"}), 200
        return jsonify(response={"error": "Wrong API_KEY"}), 403
    else:
        return jsonify(response={"error": "Incorrect method. Only GET allowed."}), 405


@shorty.route("/<url>", methods=["GET"])
def redirect_to_url(url):
    if request.method == "GET":
        if Urls.query.filter_by(short_url=request.url_root + url).first():
            return redirect(Urls.query.filter_by(short_url=request.url_root + url).first().long_url, 302)
        else:
            return jsonify(response={"error": f"There's no such short url - {url}"}), 404
    else:
        return jsonify(response={"error": "Incorrect method. Only GET allowed."}), 405


@shorty.route("/custom", methods=["POST"])
def custom_url_creation():
    if request.method == "POST":
        user_id = request.headers["x-api-id"]
        api_key = request.headers["x-api-key"]
        json_urls = request.json
        print(user_id, api_key, json_urls)
        return jsonify(response={"heh": "hehs"})
    else:
        return jsonify(response={"error": "Incorrect method. Only POST allowed."}), 405


if __name__ == "__main__":
    shorty.run(debug=True)
