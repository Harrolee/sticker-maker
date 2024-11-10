FROM python:3.12

WORKDIR /code

COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /code/app

WORKDIR /code/app

EXPOSE 5001
CMD ["python", "main.py"]