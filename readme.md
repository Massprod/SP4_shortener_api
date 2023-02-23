# Shorty - simple Flask UrlShortener API [![Test](coverage.svg)](https://github.com/Massprod/SP4_shortener_api/actions/workflows/Coverage.yml)

# Routes
- **/all** - return all Urls in DB, or for particular api-key if provided
- **/add** - adds given Urls into DB
- **/custom** - adds custom names for given Urls
- **/clear** - deletes records for provided api-key

# Requests
[GET]
- **/all** - returns Json with all DB records, takes argument: **api_key**
  - ?api_key={used_key} - only records for {used_key}
- **/add** - returns Json with used Urls and their shortened versions, takes argument: **url_to**
  - ?url_to={url_to_short} - up to 10 arguments at request

[POST]
- **/custom** - returns Json with used Urls and their custom versions.
  - use {api-key} as header and Json body: {*URL*: *custom_name*}
- **/clear** - deletes all records for given api-key
  - use {api-key} as header

# TestHost
Temporally hosted on [:blue_book:](http://massprod.pythonanywhere.com/all). But **allows** only whitelisted domains from [:book:](https://www.pythonanywhere.com/whitelist/), due to provider rules.
