import cv2
import os
import glob
import numpy as np 
from xml.etree.ElementTree import parse
 
# 비디오에서 프레임 추출해서 저장 (기본)
def extract_frame(dir,video):
    # 비디오에서 프레임 추출
    img_last = None  # 이전 프레임을 저장할 변수

    #디렉토리 만들기 
    if not os.path.exists(dir):
        os.makedirs(dir)
    save_dir = "./"+dir  # 저장 디렉토리 이름
    frame_cnt = 0
    cap = cv2.VideoCapture(video)  # mp4 파일 넣는 곳

    no = 0
    while True: 
        # 이미지 추출하기
        is_ok, frame = cap.read()  # 프레임 읽기

        if not is_ok:
            break
        try:
            if(int(cap.get(1))%5 == 0): #전체 프레임의 1/30의 프레임만 가져와서 저장
            #frame = cv2.resize(frame, (640, 800))  # 프레임 리사이징  

            # 프레임 이미지로 저장 
                outfile = save_dir + "/" + str(no) + ".jpg"
                cv2.imwrite(outfile, frame)
                no += 1 
        except Exception as e:
            print(str(e))

if __name__ == '__main__' :
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    video_path = DIR_PATH + '/video_data/test0.mp4'
    extract_frame('extract_video', video_path)
 