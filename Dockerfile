
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

COPY ["mlruns/282919090807413278/d032f6cdaf864e5286ca13fe404433a7/artifacts","app_streamlit.py", "data/1_cleaned_data.parquet","./"]

# Expose de port : tell to docker in this container the port should be open
EXPOSE 8501

# Say to docker what to RUN 
# ENTRYPOINT [ "gunicorn","--bind=0.0.0.0:9096","predict:app" ]
CMD ["streamlit", "run", "app_streamlit.py"]