from shorty_app import shorty, Custom, Urls, db
import pytest
import os
from dotenv import load_dotenv

load_dotenv("./keys.env")
ADMIN = os.getenv("ADMIN_KEY")

test_api_keys = ["1111", "2222", "3333", "4444", "5555", "6666"]
test_shorty_routes = ["custom", "clear"]

test_random_urls = [
    "https://stackoverflow.com/questions/7023052/configure-flask-dev-server-to-be-visible-across-the-network",
    "https://www.pythonanywhere.com/",
    "https://stackoverflow.com/questions/73961938/flask-sqlalchemy-db-create-all-raises-runtimeerror-working-outside-of-applicat",
    "https://www.w3schools.com/python/ref_string_replace.asp",
    "https://docs.python.org/3/tutorial/inputoutput.html",
    "https://tcl.tk/man/tcl8.6/TkCmd/pack.htm",
    "https://stackoverflow.com/questions/42999093/generate-random-number-in-range-excluding-some-numbers",
    "https://flask.palletsprojects.com/en/2.2.x/patterns/flashing/",
    "https://www.mock-server.com/mock_server/getting_started.html",
    "https://tkdocs.com/tutorial/canvas.html",
    "https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml",
]

test_broken_urls = [
    "https://www.pythonanywhere.com/teststsdsd",
    "https://www.reddit.com/test/",
]

test_random_names = [f"test{_}" for _ in range(0, 11)]

test_json = {}
for _ in range(0, 11):
    test_json[test_random_urls[_]] = test_random_names[_]

test_broken_json = {}
for _ in range(0, 2):
    test_broken_json[test_broken_urls[_]] = "broken" + test_random_names[_]


@pytest.fixture()
def app():
    app = shorty
    app.config.update({
        "TESTING": True,
    })
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_clear_route_with_empty_db(client):
    request_empty_db = client.post("/clear", headers={"api-key": ADMIN})
    assert request_empty_db.status_code == 200
    assert request_empty_db.json["response"] == {"succes": "There's was no records in DB"}
    request_wrong_api_key = client.post("/clear", headers={"api-key": "1234"})
    assert request_wrong_api_key.status_code == 200
    assert request_wrong_api_key.json["response"] == {"error": "There was no records in DB for this 'api-key'"}
    request_without_header = client.post("/clear")
    assert request_without_header.status_code == 400
    assert request_without_header.json["response"] == {"error": "Request 'header' doesn't have 'api-key'."}


def test_all_route_with_empty_db(client):
    request_empty_db = client.get("/all")
    assert request_empty_db.status_code == 200
    assert request_empty_db.json["response"] == {"succes": "no records done yet"}
    assert len(Custom.query.all()) + len(Urls.query.all()) == 0


def test_all_route_with_over_limit_api_keys(client):
    request_empty_db_with_args = client.get(f"/all?{''.join(['api_key=' + _ + '&' for _ in test_api_keys])}")
    assert request_empty_db_with_args.status_code == 413
    assert request_empty_db_with_args.json["response"] == {"error": "Only 5 API_KEY's at request allowed."}


def test_add_route_with_over_limit_new_urls(client):
    request_add_new_random = client.get(f"/add?{''.join(['url_to=' + _ + '&' for _ in test_random_urls])}")
    assert request_add_new_random.json["response"] == {"error": "Only 10 URLs at request allowed."}
    assert request_add_new_random.status_code == 413


def test_add_route_with_empty_args(client):
    request_add_empty_random = client.get("/add")
    assert request_add_empty_random.status_code == 200
    assert "There's no URL given or all of them are not responding." in request_add_empty_random.json["response"]


def test_add_route_with_broken_urls(client):
    request_add_broken_random = client.get("/add?url_to=test999&url_to=test888&url_to=https://www.reddit.com/test/")
    assert request_add_broken_random.status_code == 200
    assert request_add_broken_random.json["response"] == {"There's no URL given or all of them are not responding.":
                                                          ["test999", "test888", "https://www.reddit.com/test/"]}
    for value in request_add_broken_random.json["response"]:
        assert Urls.query.filter_by(long_url=value).first() is None


def test_add_route_with_single_new_url(client):
    request_add_working_random = client.get(f"/add?url_to={test_random_urls[-1]}")
    assert request_add_working_random.status_code == 200
    exist = Urls.query.filter_by(long_url=test_random_urls[-1]).first()
    assert request_add_working_random.json["response"] == {f"long id{exist.id} - {test_random_urls[-1]}":
                                                           f"new short - {exist.short_url}"}


def test_add_route_with_single_duplicate_url(client):
    request_add_working_duplicate = client.get(f"/add?url_to={test_random_urls[-1]}")
    assert request_add_working_duplicate.status_code == 200
    exist = Urls.query.filter_by(long_url=test_random_urls[-1]).first()
    assert request_add_working_duplicate.json["response"] == {f"long id{exist.id} - {test_random_urls[-1]}":
                                                              f"existed short - {exist.short_url}"}


def test_add_route_with_multiple_urls(client):
    request_add_multiple = client.get(f"/add?{''.join(['url_to=' + _ + '&' for _ in test_random_urls[3:-1]])}")
    assert request_add_multiple.status_code == 200
    assert_new = {}
    for _ in test_random_urls[3:-1]:
        if exist := Urls.query.filter_by(long_url=_).first():
            assert_new[f"long id{exist.id} - {_}"] = f"new short - {exist.short_url}"
    assert request_add_multiple.json["response"] == assert_new


def test_add_route_with_multiple_duplicates_urls(client):
    request_add_multiple_duplicates = client.get(
        f"/add?{''.join(['url_to=' + _ + '&' for _ in test_random_urls[3:-1]])}")
    assert request_add_multiple_duplicates.status_code == 200
    assert_new = {}
    for _ in test_random_urls[3:-1]:
        exist = Urls.query.filter_by(long_url=_).first()
        assert_new[f"long id{exist.id} - {_}"] = f"existed short - {exist.short_url}"
    assert request_add_multiple_duplicates.json["response"] == assert_new


def test_add_route_with_multiple_combo_urls(client):
    new_urls = test_random_urls[0:3]
    duplicate = test_random_urls[3:6]
    combo_urls = test_random_urls[0:6] + test_broken_urls
    assert_combo = {}
    for _ in duplicate:
        if exist := Urls.query.filter_by(long_url=_).first():
            assert_combo[f"long id{exist.id} - {_}"] = f"existed short - {exist.short_url}"
    request_add_working_multiple = client.get(f"/add?{''.join(['url_to=' + _ + '&' for _ in combo_urls])}")
    for _ in new_urls:
        if exist := Urls.query.filter_by(long_url=_).first():
            assert_combo[f"long id{exist.id} - {_}"] = f"new short - {exist.short_url}"
    assert request_add_working_multiple.status_code == 200
    assert request_add_working_multiple.json["response"] == assert_combo
    for _ in test_broken_urls:
        assert Urls.query.filter_by(long_url=_).first() is None


def test_custom_route_without_header(client):
    request_custom_no_header = client.post("/custom")
    assert KeyError
    assert request_custom_no_header.status_code == 403
    assert request_custom_no_header.json["response"] == {"error": "Make sure to fill 'Header' with correct 'api-key'."}


def test_custom_route_with_header_no_body(client):
    request_custom_no_body = client.post("/custom", headers={"api-key": test_api_keys[0]})
    assert request_custom_no_body.status_code == 400
    assert request_custom_no_body.json is None


def test_custom_route_with_header_empty_body(client):
    request_custom_empty_body = client.post("/custom", headers={"api-key": test_api_keys[0]}, json={})
    assert request_custom_empty_body.status_code == 400
    assert request_custom_empty_body.json["response"] == {"error": "Empty body"}


def test_custom_route_with_over_limit_urls(client):
    request_custom_over_limit = client.post("/custom", headers={"api-key": test_api_keys[0]}, json=test_json)
    assert request_custom_over_limit.status_code == 413
    assert request_custom_over_limit.json["response"] == {"error": "Only 10 URLs at request allowed."}


def test_custom_route_with_only_broken_urls(client):
    request_custom_broken = client.post("/custom", headers={"api-key": test_api_keys[0]}, json=test_broken_json)
    assert request_custom_broken.status_code == 200
    assert request_custom_broken.json["response"] == {"error": "All given URLs are not responding."}


def test_custom_route_with_combo_urls(client):
    test_working = {key: value for key, value in test_json.items() if int(value[-1]) < 7}
    test_combo = test_broken_json | test_working
    request_custom_combo = client.post("/custom", headers={"api-key": test_api_keys[0]}, json=test_combo)
    root = request_custom_combo.request.url_root
    assert request_custom_combo.status_code == 200
    assert len(Custom.query.filter_by(api_key=test_api_keys[0]).all()) == 8
    for api_key in test_api_keys[1:5]:
        request_custom_combo = client.post("/custom", headers={"api-key": api_key}, json=test_combo)
        assert request_custom_combo.status_code == 200
        for key in test_broken_json:
            assert Custom.query.filter_by(long_url=key).first() is None
        for key, value in test_working.items():
            assert Custom.query.filter_by(custom_url=root + value, api_key=api_key).first().long_url == key
        assert len(Custom.query.filter_by(api_key=api_key).all()) == 8


def test_custom_route_with_duplicates(client):
    test_working = {key: value for key, value in test_json.items() if int(value[-1]) > 3}
    test_combo = test_broken_json | test_working
    request_duplicates = client.post("/custom", headers={"api-key": test_api_keys[5]}, json=test_combo)
    root = request_duplicates.request.url_root
    assert request_duplicates.status_code == 200
    for key in test_broken_json:
        assert Custom.query.filter_by(long_url=key).first() is None
    for key, value in test_working.items():
        assert Custom.query.filter_by(custom_url=root + value, api_key=test_api_keys[5]).first().long_url == key
    assert len(Custom.query.filter_by(api_key=test_api_keys[5]).all()) == 6


def test_custom_route_with_conflict_url(client):
    request_root = client.get("/all")
    root = request_root.request.url_root
    request_root.close()
    conflict_url = "https://flask.palletsprojects.com/en/2.2.x/api/"
    conflict_short = "conflict"
    conflict_data = Urls(long_url=conflict_url,
                         short_url=root + conflict_short,
                         time="232323",
                         )
    db.session.add(conflict_data)
    db.session.commit()
    request_conflict = client.post("/custom", headers={"api-key": "conflict"}, json={conflict_url: conflict_short})
    assert request_conflict.status_code == 200
    assert Urls.query.filter_by(short_url=root + conflict_short, long_url=conflict_url).first()
    assert Custom.query.filter_by(custom_url=root + conflict_short).first() is None


def test_custom_route_with_same_combo_urls_diff_api_key(client):
    test_same = {key: value for key, value in test_json.items() if int(value[-1]) < 9}
    request_same_combo_urls = client.post("/custom", headers={"api-key": "same_combo_urls"}, json=test_same)
    root = request_same_combo_urls.request.url_root
    assert request_same_combo_urls.status_code == 200
    for key, value in test_same.items():
        assert Custom.query.filter_by(long_url=key, custom_url=root + value).first()
    assert len(Custom.query.filter_by(api_key="same_combo_urls").all())


def test_custom_route_with_short_duplicate_with_diff_api_key(client):
    duplicate = {"https://stackoverflow.com/": "test0"}
    short_duplicate = "short test"
    request_short_duplicate = client.post("/custom", headers={"api-key": short_duplicate}, json=duplicate)
    root = request_short_duplicate.request.url_root
    assert request_short_duplicate.status_code == 200
    for key, value in duplicate.items():
        assert Custom.query.filter_by(custom_url=root + value).first()
        assert Custom.query.filter_by(api_key=short_duplicate, long_url=key).first() is None


def test_all_route_with_api_keys(client):
    test_keys = test_api_keys[:5]
    request_with_keys = client.get(f"/all?{''.join(['api_key=' + _ + '&' for _ in test_keys])}")
    assert request_with_keys.status_code == 200
    for key in test_keys:
        assert request_with_keys.json["response"][key]


def test_all_route_with_no_data_api_key(client):
    test_key = "9999"
    request_with_key = client.get(f"/all?api_key={test_key}")
    assert request_with_key.status_code == 200
    assert request_with_key.json["response"][test_key] == "No data for this Key. Make sure it's used before."


def test_all_route_without_key(client):
    request_without_key = client.get("/all")
    assert_custom = {}
    assert_random = {}
    assert request_without_key.status_code == 200
    for _ in Custom.query.all():
        assert_custom[str(_.id)] = {"api_key": _.api_key,
                                    "original_url": _.long_url,
                                    "custom_url": _.custom_url,
                                    "creation_time": _.time,
                                    }
        assert assert_custom[str(_.id)] == request_without_key.json["custom_created"][str(_.id)]
    assert len(Custom.query.all()) == len(assert_custom)
    for _ in Urls.query.all():
        assert_random[str(_.id)] = {"id": _.id,
                                    "original_url": _.long_url,
                                    "shortened_url": _.short_url,
                                    "creation_time": _.time,
                                    }
        assert assert_random[str(_.id)] == request_without_key.json["random_created"][str(_.id)]
    assert len(Urls.query.all()) == len(assert_random)


# def test_redirect_route_with_api_name(client):
#     for _ in test_shorty_routes:
#         request_with_api_name = client.get(f"/{_}")
#         assert request_with_api_name.status_code == 400
#         assert request_with_api_name.json["response"]
#         request_with_api_name.close()
#
#
# def test_redirect_route_with_random_url(client):
#     for url in test_random_urls:
#         test_short_url = Urls.query.filter_by(long_url=url).first().short_url[-3:]
#         request_redirect = client.get(f"/{test_short_url}")
#         assert request_redirect.status_code == 302
#         assert request_redirect.location == url
#         request_redirect.close()
#
#
# def test_redirect_route_with_custom_url(client):
#     for name in test_random_names:
#         request_redirect_custom = client.get(f"/{name}")
#         root = request_redirect_custom.request.url_root
#         assert request_redirect_custom.status_code == 302
#         assert request_redirect_custom.location == Custom.query.filter_by(custom_url=root + name).first().long_url
#         request_redirect_custom.close()
#
#
# def test_redirect_route_with_wrong_url(client):
#     wrong_customs = [f"test{_}" for _ in range(30, 40)]
#     for name in wrong_customs:
#         request_redirect_wrong = client.get(f"/{name}")
#         assert request_redirect_wrong.status_code == 404
#         assert request_redirect_wrong.json["response"]
#         request_redirect_wrong.close()
#
#
# def test_clear_route_with_api_key(client):
#     for key in test_api_keys[-4:]:
#         request_clear_with_key = client.post("/clear", headers={"api-key": key})
#         assert request_clear_with_key.status_code == 200
#         assert request_clear_with_key.json["response"]
#         assert Custom.query.filter_by(api_key=key).first() is None
#
#
# def test_clear_route_with_wrong_key(client):
#     for key in test_api_keys[-4:]:
#         request_clear_with_wrong = client.post("/clear", headers={"api-key": key})
#         assert request_clear_with_wrong.status_code == 200
#         assert request_clear_with_wrong.json["response"]
#         assert Custom.query.filter_by(api_key=key).first() is None
#
#
# def test_clear_route_with_admin_key(client):
#     request_admin = client.post("/clear", headers={"api-key": ADMIN})
#     assert request_admin.status_code == 200
#     assert request_admin.json["response"]
#     assert len(Urls.query.all()) + len(Custom.query.all()) == 0
