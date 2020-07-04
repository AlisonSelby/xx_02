FROM python:3.8.3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ls

CMD [ "python", "./src/main.py" ]