FROM python:3.8.3

WORKDIR /usr/src/app

RUN mkdir /input
RUN mkdir /output

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY data_structural ./data_structural/
COPY src ./src/


CMD [ "python", "./src/main.py" ]