import cv2
import os
import numpy as np  
 
#image augmentation
def img_augmentation():

    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    img_path = DIR_PATH + "\extract_video"

    """
    image augmentation
    1. 좌우 반전
    2. 밝기 조정
    3. 2배 확대
    4. 0.5배 확대
    """
    og_img = []
    
    filenames = os.listdir(img_path)
    for filename in filenames:
        full_filename = os.path.join(img_path, filename)
        #print(full_filename)
        og_img.append(full_filename)
        
    # 비디오에서 프레임 추출
    img_last = None  # 이전 프레임을 저장할 변수

    #디렉토리 만들기 
    if not os.path.exists("./augmentation"):
        os.makedirs("./augmentation")
    save_dir = "./augmentation"  # 저장 디렉토리 이름
    frame_cnt = 0

    for src in og_img:
        
        print(src)
        og = cv2.imread(src)
        print(og)

        og_rgb = cv2.cvtColor(og, cv2.COLOR_BGR2RGB)
        fliped = cv2.flip(og,1) # 좌우 반전
        val = 70
        array = np.full(og.shape,(val,val,val),dtype=np.uint8)
        add = cv2.add(og,array) # 밝기 조정

        img_mag = cv2.resize(og,None,fx=2,fy=2,interpolation = cv2.INTER_CUBIC) #2배 확대
        #img_red = cv2.resize(og,None,fx=0.5,fy=0.5,interpolation = cv2.INTER_AREA)  # 0.5배

        # augmentation한 이미지 파일로 저장
        for p,a in zip(["_flip","_add","_mag","_red"],[fliped,add,img_mag]): #,img_red]) :
            try: 
                outfile = save_dir + "/" + src.split("\\")[-1][:-4]+p + ".jpg"  
                print("output: "+outfile)
                cv2.imwrite(outfile,a) 
            except Exception as e:
                print(str(e))

if __name__ == '__main__' :
    img_augmentation()