
# Install python 
FROM python:3.11.4-slim-bookworm

# Run some commands 
RUN pip install -U pip
RUN pip install pipenv

# Copy pipenv files

WORKDIR /app

COPY ["Pipfile","Pipfile.lock","./"]

# Install dependencies whitout creating  a virtual env 
RUN pipenv install --system --deploy

COPY ["predict.py","xgboost.bin","DictVectorizer.b","./"]

# Expose de port : tell to docker in this container the port should be open
EXPOSE  9096 

# Say to docker what to RUN 
ENTRYPOINT [ "gunicorn","--bind=0.0.0.0:9096","predict:app" ]