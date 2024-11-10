FROM python:3.12

WORKDIR /code

COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /code/app

# Be explicit about the full path
ENV PYTHONPATH=/code/app

WORKDIR /code/app

# Add a directory list step to verify our files
RUN ls -la

EXPOSE 5001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]