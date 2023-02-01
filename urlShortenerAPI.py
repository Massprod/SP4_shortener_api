import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
import os
import random
import string
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy

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
routes = ["all", "add", "custom", "clear"]
limiter = Limiter(
    get_remote_address,
    app=shorty,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",
)


class Urls(db.Model):
    __tablename__ = "urls"
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(200), nullable=False)
    short_url = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)


class Custom(db.Model):
    __tablename__ = "custom"
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.Integer, nullable=False)
    long_url = db.Column(db.String(200), nullable=False)
    custom_url = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)


with shorty.app_context():
    db.create_all()


@shorty.route("/all", methods=['GET'])
@limiter.limit("40 per hour")
def all_urls():
    keys = request.args.getlist("api_key")
    if 1 <= len(keys) < 5:
        keys_data = {}
        for key in keys:
            custom_key_urls = Custom.query.filter_by(api_key=key).all()
            keys_data[key] = {}
            for _ in custom_key_urls:
                keys_data[key][_.id] = {
                    f"long - {_.long_url}": f"short - {_.custom_url}",
                    "created": _.time
                }
        return jsonify(response=keys_data)
    elif 5 < len(keys):
        return jsonify(response={"error": "Only 5 API_KEY's at request allowed."}), 413
    else:
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


@shorty.route("/add", methods=['GET'])
@limiter.limit("150 per hour")
def add_url():
    urls = request.args.getlist('url_to')
    if len(urls) <= 10:
        not_responding = []
        session = requests.Session()
        for _ in urls:
            if Urls.query.filter_by(long_url=_).first():
                pass
            else:
                try:
                    con = session.head(_, timeout=5)
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
        elif 1 < len(urls) <= 10:
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
        return jsonify(response={"error": "Only 10 URLs at request allowed."}), 413


@shorty.route("/clear", methods=["POST"])
def clearing_db():
    try:
        if request.headers["api-key"] == ADMIN:
            if len(Urls.query.all()) == 0:
                return jsonify(response={"succes": "There's was no records in DB"}), 200
            else:
                for _ in Urls.query.all():
                    db.session.delete(_)
                for _ in Custom.query.all():
                    db.session.delete(_)
                db.session.commit()
                return jsonify(response={"succes": "all DB's cleared"}), 200
        elif Custom.query.filter_by(api_key=request.headers["api-key"]).first():
            if len(Custom.query.filter_by(api_key=request.headers["api-key"]).all()) == 0:
                return jsonify(response={"succes": "There's was no records in DB for this 'api-key'"}), 200
            else:
                for _ in Custom.query.filter_by(api_key=request.headers["api-key"]).all():
                    db.session.delete(_)
                db.session.commit()
                return jsonify(response={"succes": f"all record's for {request.headers['api-key']} key, deleted."})
        else:
            return jsonify(response={"error": "Wrong API-key"}), 403
    except KeyError:
        return jsonify(response={"error": "Request 'header' doesn't have 'api-key'."}), 400


@shorty.route("/<url>", methods=["GET"])
def redirect_to_url(url):
    if url in routes:
        return jsonify(response={"error": "Try to avoid using API routes as custom URL."}), 400
    elif Urls.query.filter_by(short_url=request.url_root + url).first():
        return redirect(Urls.query.filter_by(short_url=request.url_root + url).first().long_url, 302)
    elif Custom.query.filter_by(custom_url=request.url_root + url).first():
        return redirect(Custom.query.filter_by(custom_url=request.url_root + url).first().long_url, 302)
    else:
        return jsonify(response={"error": f"There's no such short url - {url}"}), 404


@shorty.route("/custom", methods=["POST"])
def custom_url():
    try:
        api_key = request.headers["api-key"]
        not_responding = []
        custom_urls = request.json
        if len(custom_urls) == 0:
            return jsonify(response={"error": "Empty body"}), 400
        elif 1 < len(custom_urls) <= 10:
            session = requests.Session()
            for key in custom_urls:
                if Custom.query.filter_by(long_url=key).first():
                    pass
                else:
                    try:
                        con = session.head(key, timeout=5)
                        if con.status_code >= 400:
                            not_responding.append(key)
                    except requests.RequestException:
                        not_responding.append(key)
            session.close()
            for key in not_responding:
                del custom_urls[key]
            added = {}
            for key in custom_urls:
                if Urls.query.filter_by(short_url=request.url_root + custom_urls[key]).first():
                    added[f"long - {Urls.query.filter_by(short_url=request.url_root + custom_urls[key]).first().long_url}"] = \
                          f"already used - {request.url_root + custom_urls[key]}"
                elif Custom.query.filter_by(custom_url=request.url_root + custom_urls[key]).first():
                    added[f"long - {Custom.query.filter_by(custom_url=request.url_root +custom_urls[key]).first().long_url}"] = \
                          f"already used - {request.url_root + custom_urls[key]}"
                else:
                    added[f"long - {key}"] = f"custom - {request.url_root + custom_urls[key]}"
                    custom_data = Custom(
                        api_key=api_key,
                        long_url=key,
                        custom_url=request.url_root + custom_urls[key],
                        time=creation_time,
                    )
                    db.session.add(custom_data)
            db.session.commit()
            return jsonify(added=added)
        else:
            return jsonify(response={"error": "Only 10 URLs at request allowed."}), 413
    except KeyError:
        return jsonify(response={"error": "Make sure to fill 'Header' with correct 'api-key'."})


@shorty.after_request
def after_request(response):
    logger.info({
        "datetime": dt.datetime.now().isoformat(),
        "user_ip": request.remote_addr,
        "method": request.method,
        "request_url": request.path,
        "response_status": response.status,
        "request_referrer": request.referrer,
        "request_user_agent": request.user_agent,
        "response_body": response.json,
    })
    return response


if __name__ == "__main__":
    handler = RotatingFileHandler("shorty_log.log", maxBytes=100000)
    logger = logging.getLogger('werkzeug')
    logger.addHandler(handler)
    shorty.run(debug=True)
