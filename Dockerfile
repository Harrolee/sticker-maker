FROM python:3.12

WORKDIR /code

COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /code/app

# Since we're running from /code/app, we only need this path
ENV PYTHONPATH=/code/app:${PYTHONPATH}

WORKDIR /code/app

EXPOSE 5001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]