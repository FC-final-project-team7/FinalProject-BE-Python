FROM python:3.8-slim

RUN apt update
RUN apt upgrade

WORKDIR /workspace

COPY requirements.txt /workspace/
COPY temp.jpg /workspace/
COPY app.py /workspace/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install boto3
RUN pip install moviepy
RUN pip install gTTS

CMD ["python3", "app.py"]