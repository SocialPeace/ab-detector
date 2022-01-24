import os
import argparse
from types import MethodType
from flask.json import JSONDecoder
import telegram
import requests,json
from werkzeug.utils import redirect
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, make_response,Response
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    get_jwt_identity, jwt_required,
    set_access_cookies, set_refresh_cookies, 
    unset_jwt_cookies, create_refresh_token,
    jwt_refresh_token_required
)
from config import *
from oauth_controller import Oauth
from model import UserModel, UserData

parser = argparse.ArgumentParser(description='parse')
parser.add_argument('--type', type=int, default=0)
args = parser.parse_args()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = "eseafsd."
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 30
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 100
jwt = JWTManager(app)

abnormal = False

# path 변수들
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

yolo_custom_weights = DIR_PATH + "\models\yolov4-custom.weights"
yolo_custom_cfg = DIR_PATH + "\models\yolov4-custom.cfg"

# 동영상 작동 용
if args.type == 0 :
    video_path = DIR_PATH + '/video_data/test0.mp4'  
    camera = cv2.VideoCapture(video_path)

# 웹캠 용
elif args.type == 1:
    camera = cv2.VideoCapture(0)

# 학습한 class list => obj.names의 순서대로 입력해야 한다.
classes_custom = ["stand", "punch", "kick", "push"]

# 네트워크 불러오기
net_yolo_custom = cv2.dnn.readNet(yolo_custom_weights, yolo_custom_cfg)

# GPU 할당
net_yolo_custom.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net_yolo_custom.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# 클래스의 갯수만큼 랜덤 RGB 배열을 생성
colors = np.random.uniform(0, 255, size=(len(classes_custom),4))

def yolo(frame, size, score_threshold, nms_threshold):

    global abnormal
    # 네트워크 지정
    
    net = net_yolo_custom
    classes = classes_custom

    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # 이미지의 높이, 너비, 채널 받아오기
    height, width, channels = frame.shape

    # 네트워크에 넣기 위한 전처리
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (size, size), (0, 0, 0), True, crop=False)

    # 전처리된 blob 네트워크에 입력
    net.setInput(blob)

    # 결과 받아오기
    outs = net.forward(output_layers)

    # 각각의 데이터를 저장할 리스트 생성 및 초기화
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # 정확도가 0.75보다 크다면 bounding box를 칠한다.
            if confidence > 0.75:
                # 탐지된 객체의 너비, 높이 및 중앙 좌표값 찾기
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # 객체의 사각형 테두리 중 좌상단 좌표값 찾기
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # 노이즈 제거 (Non Maximum Suppression) (겹쳐있는 박스 중 상자가 물체일 확률이 가장 높은 박스만 남겨둠)
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=score_threshold, nms_threshold=nms_threshold)

    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            class_name = classes[class_ids[i]]

            # 프레임에 작성할 텍스트 및 색깔 지정
            label = f"{class_name}: {confidences[i]:.2f}"

            color = colors[class_ids[i]]

            # 프레임에 사각형 테두리 그리기 및 텍스트 쓰기
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(frame, (x - 1, y), (x + len(class_name) * 13 + 80, y - 25), color, -1)
            cv2.putText(frame, label, (x, y - 8), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), 2)
            print(class_name)

            # 검출된 box의 class_name이 punch, kick, push일 경우 이상행동이므로
            # abnormal 변수를 True로 바꿔준다.
            if class_name == "punch" or class_name == "kick" or class_name == "push":
                abnormal = True 
                class_type = class_name

    return frame

# 웹캠을 frame 단위로 받아 yolo모델을 통과한 결과 frame을 반환하는 함수 
def gen_frames():
    
    while True:
        ret, frame = camera.read()  # read the camera frame
        if not ret:
            break     
        else : 
            frame = yolo(frame=frame, size=416, score_threshold=0.45, nms_threshold=0.4)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # concat frame one by one and show result
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  
            cv2.destroyAllWindows()
 
# main page routing
@app.route("/")
def home(): 
    user_id = get_jwt_identity()
    print(user_id)
    if user_id :
        return render_template('index.html') 
    return redirect('/login')

@app.route("/login")
def login(): 
    return render_template('login.html') 

@app.route("/kakao")
def kakao(): 
    return render_template('kakao.html') 

@app.route("/index")
def index():
    return render_template('index.html')

@app.route("/main")
def main():
    return render_template('main.html')

@app.route('/oauth/url')
def oauth_url_api():
    """
    Kakao OAuth URL 가져오기
    """
    kakao_oauth_url="https://kauth.kakao.com/oauth/authorize?client_id=%s&redirect_uri=%s&response_type=code" \
    % (CLIENT_ID, REDIRECT_URI)
    print(kakao_oauth_url)
    return jsonify(
        kakao_oauth_url
    )

@app.route("/oauth")
def oauth_api():
    """
    # OAuth API [GET]
    사용자로부터 authorization code를 인자로 받은 후,
    아래의 과정 수행함
    1. 전달받은 authorization code를 통해서
        access_token, refresh_token을 발급.
    2. access_token을 이용해서, Kakao에서 사용자 식별 정보 획득
    3. 해당 식별 정보를 서비스 DB에 저장 (회원가입)
    3-1. 만약 이미 있을 경우, (3) 과정 스킵
    4. 사용자 식별 id를 바탕으로 서비스 전용 access_token 생성
    """
    code = str(request.args.get('code'))
    
    oauth = Oauth()
    auth_info = oauth.auth(code)
    user = oauth.userinfo("Bearer " + auth_info['access_token'])
    user['location'] = None
    user['friend'] = None

    user = UserData(user)
    result = UserModel().upsert_user(user) 
    
    if result == 1: #처음 로그인
        resp = redirect('/location')
    else: # 이미 회원일때
        resp = redirect('/index')
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)   
    resp.set_cookie("logined", "true")
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp
 
@app.route('/token/remove')
def token_remove_api():
    """
    Cookie에 등록된 Token 제거
    """
    resp = jsonify({'result': True})
    unset_jwt_cookies(resp)
    resp.delete_cookie('logined')
    return resp

@app.route("/userinfo")
@jwt_required
def userinfo():
    """
    Access Token을 이용한 DB에 저장된 사용자 정보 가져오기
    """
    user_id = get_jwt_identity()
    userinfo = UserModel().get_user(user_id).serialize()
    return jsonify(userinfo)


@app.route("/location")  
def location(): 
    return render_template('location.html')    

@app.route("/location_save", methods = ['POST'])  
def location_save(): 
    addr = request.form['result_addr'] 
    LOCATION = addr
    print(addr) 
    return redirect('/info_reg')  

@app.route("/save_chat")  
def save_chat(): 
    bot = telegram.Bot(token=TOKEN)
    #알림봇 업데이트 로그 가져옴
    updates = bot.get_updates() 
    #비상연락망 chat id 저장 
    CHAT_ID = updates[-1]['message']['chat']['id']
    print(CHAT_ID)
    return redirect('/index')   

@app.route("/info_reg")
def info_reg():
    return render_template('info_reg.html')    
 
@app.route("/mypage")
def mypage():
    print(LOCATION)
    return render_template('mypage.html',location=LOCATION)

@app.route('/get/status')
def get_status():
    """
    abnormal 탐지 결과 보내기
    """
    global abnormal
    print(abnormal)
    resp = jsonify({'abnormal': abnormal}) 
    abnormal = False
    return resp

@app.route('/send/msg')
def send_msg():
    bot = telegram.Bot(token=TOKEN)
    #알림봇 업데이트 로그 가져옴
    updates = bot.get_updates() 
    #비상연락망 chat id 저장 
    CHAT_ID = updates[-1]['message']['chat']['id'] 
    print(CHAT_ID)
    #해당 chat id로 메시지 전송
    bot.sendMessage(chat_id=CHAT_ID,text="비정상 행동이 감지되었습니다."+" 위치 :"+LOCATION); 
    resp = jsonify({'result': True})
    return resp 

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
  
if __name__ == '__main__' :
    app.run(host='127.0.0.1', port=5050, debug=True)
    