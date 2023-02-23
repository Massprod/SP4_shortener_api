FROM python:alpine

WORKDIR /shorty

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python"]
CMD ["shorty_app.py"]