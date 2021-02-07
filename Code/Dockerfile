FROM python:3.8

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
#COPY requirements.txt ./app/

WORKDIR /app

CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "80"]