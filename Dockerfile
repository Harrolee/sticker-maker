FROM python:3.12

WORKDIR /code

COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /code/app

ENV PYTHONPATH=/code:/code/app:${PYTHONPATH}

EXPOSE 5001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]