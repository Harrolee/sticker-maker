FROM python:3.12

WORKDIR /code

COPY fastapp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY fastapp/ /code/fastapp
COPY fastapp/.env /code/env/.env

EXPOSE 5001
CMD ["uvicorn", "fastapp.main:app", "--host", "0.0.0.0", "--port", "5001"]