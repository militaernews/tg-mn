FROM python:3.12.0-alpine

RUN apk update
RUN apk add git

COPY requirements.txt requirements.txt

RUN python -m pip install -r requirements.txt --force-reinstall

COPY . .

CMD ["python3", "-m" , "main.py"]