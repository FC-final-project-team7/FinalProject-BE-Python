import uuid
import time, os
import numpy as np
import boto3
import shutil
import json
import logging
from urllib import response
from flask import Flask, request

from moviepy.editor import *
from gtts import gTTS

app = Flask(__name__)

ACCESS_KEY_ID = ''
ACCESS_SECRET_KEY = ''
BUCKET_NAME = ''


@app.route('/', methods=['GET'])
def index():
    return {'status': 'hello'}


# 오디오 요청
# request: text, narration, username
# response: status, url
@app.route('/audios', methods=['GET', 'POST'])
def audio():
    # 예시
    if request.method == "GET":
        data = dict()
        data['text'] = '여기에는  텍스트가 들어갑니다. 텍스트가 길수록 오디오는 길어집니다.'
        data['narration'] = 'none'
        username = 'jeongsu'
        response_object = audio_request(data, username)
        return response_object

    else:
        post_string = request.get_json()
        post_data = json.loads(post_string)

        data = dict()
        data['text'] = post_data['text']
        data['narration'] = post_data['narration']
        username = post_data['username']
        response_object = audio_request(data, username)
        return response_object


# 비디오 요청
# request: username, project_name, audio_name, avatar, background
# response: status, url
@app.route('/video', methods=['GET', 'POST'])
def video():
    # 예시
    if request.method == 'GET':
        data = dict()
        data['username'] = 'jeongsu'
        data['audio_name'] = '4d1cc3ee'
        data['avatar'] = '아바타입니당'
        data['background'] = '배경입니당.'
        data['project_name'] = 'hello'
        data['is_audio'] = true
        response_object = video_request(data)
        return response_object

    else:
        post_string = request.get_json()
        post_data = json.loads(post_string)

        data = dict()
        data['is_audio'] = post_data['is_audio']
        data['username'] = post_data['username']
        data['audio_name'] = post_data['audio_name']
        data['avatar'] = post_data['avatar']
        data['background'] = post_data['background']
        data['project_name'] = post_data['project_name']
        response_object = video_request(data)
        return response_object


# 오디오 파일 생성 / data -> 텍스트와 성우(성우는 사용하지 않습니다.)
def audio_request(data, username, sr=44100):
    url = "wrong url"
    response_object = {'status': 'success'}
    audio_name = uuid.uuid4().hex[:8]
    createDirectory('audio')
    output = 'audio/' + audio_name + '.wav'
    text = data['text']
    narration = data['narration']
    # 오디오 생성
    tts = gTTS(text=text, lang='ko')
    tts.save(output)

    # s3에 오디오 업로드
    try:
        url = s3_upload_audio(output, username, audio_name)
    except ClientError as e:
        logging.error(e)
        response_object['status'] = 'fail'
        response_object['url'] = url
    else:
        response_object['url'] = url

    return response_object


# 비디오 파일 생성
def video_request(data):
    url = "wrong url"
    response_object = {'status': 'success'}
    wave = 'audio/' + data['audio_name'] + '.wav'
    if data['is_audio']:
        s3_download_audio(wave, data['username'], data['audio_name'])

    if duplicate_check(data['username'], data['project_name']):
        video_id = data['project_name'] + uuid.uuid4().hex[:2]
    else:
        video_id = data['project_name']

    createDirectory('video')
    output = 'video/' + video_id + '.mp4'

    audio_path = AudioFileClip(wave)
    video_path = ImageClip('temp.jpg', duration=audio_path.duration)
    video_path = video_path.set_audio(audio_path)
    video_path.write_videofile(output, fps=24, codec="libx264")

    # s3에 비디오 업로드
    try:
        url = s3_upload_video(output, data['username'], video_id)
    except:
        response_object['status'] = 'fail'
        response_object['url'] = url
    else:
        response_object['url'] = url

    os.remove('audio/' + data['audio_name'] + '.wav')
    os.remove('video/' + video_id + '.mp4')
    return response_object


# s3와 연결하는 함수
def s3_connection():
    return boto3.client('s3', aws_access_key_id=ACCESS_KEY_ID, aws_secret_access_key=ACCESS_SECRET_KEY)


# s3안의 버킷에 오디오를 저장하는 함수
def s3_upload_audio(path, username, audio_name):
    s3 = s3_connection()
    s3.upload_file(path, BUCKET_NAME, 'project/' + username + '/' + audio_name + '.wav')
    return "https://d16d8cj4lvx40k.cloudfront.net/" + 'project/' + username + "/" + audio_name + ".wav"


def s3_download_audio(path, username, audio_name):
    s3 = s3_connection()
    # download_file(다운로드 할 버킷, 다운로드 할 객체, 저장될 위치)
    s3.download_file(BUCKET_NAME, 'project/' + username + '/' + audio_name + '.wav', path)


# s3안의 버킷에 비디오를 저장하는 함수
def s3_upload_video(path, username, video_name):
    s3 = s3_connection()
    s3.upload_file(path, BUCKET_NAME, 'project/' + username + '/' + video_name + '.mp4')
    return "https://d16d8cj4lvx40k.cloudfront.net/" + 'project/' + username + "/" + video_name + ".mp4"


# 폴더를 생성하는 함수
def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory.')


# 버킷안에 영상명이 중복인지 검사하는 함수
def duplicate_check(username, video_name):
    s3 = s3_connection()
    key = username + '/video/' + video_name + '.mp4'
    try:
        s3.get_object(Bucket=BUCKET_NAME, Key=key)
    except:
        return False
    else:
        return True


# 포트를 변경하셔도 됩니다.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
