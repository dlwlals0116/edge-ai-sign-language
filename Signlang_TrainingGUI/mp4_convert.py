import glob
import subprocess
import time
import cv2
import numpy as np
import os
import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

select = input("작업을 선택하세요.\n\n1. 수어 영상 변환 및 단어 DB 입력\n2. 딥러닝 서버 학습 데이터셋 전송\n3. 청각장애인용 통역기 출력 영상 전송\n\n번호 선택: ")

if select == '1':
    try:
        path = './input_video/*'
        output = glob.glob(path)
        video_file = output[0]
        src = input("파일명 입력: ")
        save_path1 = './output_video/{}.mp4'.format(src)
        save_path2 = './tmp_video/{}.mp4'.format(src)
        fps = 29.97

        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            while True:
                context = input("수어내용 입력: ")
                if context == '':
                    break
                conn.set(context, './Video/{}.mp4'.format(src))
                conn.set(src, context)
                data = conn.get(context)
                print(data)

        cap = cv2.VideoCapture(video_file)

        if cap.isOpened():
            ret, img = cap.read()
            out = cv2.VideoWriter(save_path1, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), fps, (1280, 700))
            while True:
                ret, img = cap.read()
                if ret:
                    dst = img.copy()
                    dst = dst[30:466, 204:495]
                    stacked_img = np.hstack((dst, dst))
                    stacked_img_h, stacked_img_w, stacked_img_c = stacked_img.shape
                    print(stacked_img_w, stacked_img_h)
                    stacked_img = cv2.resize(stacked_img, (1280, 700))
                    cv2.imshow('save_mp4', stacked_img)
                    out.write(stacked_img)
                    cv2.waitKey(25)
                else:
                    break
            out.release()
        else:
            print("Can't open video.")

        cap = cv2.VideoCapture(video_file)

        if cap.isOpened():
            ret, img = cap.read()
            out = cv2.VideoWriter(save_path2, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), fps, (640, 480))
            while True:
                ret, img = cap.read()
                if ret:
                    resize_frame = cv2.resize(img, (640, 480), interpolation=cv2.INTER_CUBIC)
                    cv2.imshow('save_mp4', resize_frame)
                    out.write(resize_frame)
                    cv2.waitKey(25)
                else:
                    break
            out.release()
        else:
            print("Can't open video.")
        cap.release()
        cv2.destroyAllWindows()

        dir_path = "./tmp_video"
        f = open(dir_path + "/filelist.txt", 'w')

        for (root, directorie, files) in os.walk(dir_path):
            for file in files:
                if file.endswith('{}.mp4'.format(src)):
                    for x in range(5):
                        f.write("file ")
                        file += "\n"
                        f.write(file)
        f.close()

        os.system('ffmpeg -f concat -i ./tmp_video/filelist.txt -c copy ./train_video/{}.mp4'.format(src))

        os.remove(video_file)
        os.remove(save_path2)
        os.remove(dir_path + "/filelist.txt")
    except IndexError:
        print('\n입력 파일이 없습니다. 한국수어사전 사이트에서 단어 영상을 다운로드하세요.')
elif select == '2':
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        work = conn.get('server_work').decode('utf-8')
    if work == 'off':
        print('\n딥러닝 서버가 꺼져있습니다.')
    else:
        print('\n학습 데이터셋 전송을 시작합니다.')
        subprocess.call([r"./pscp.exe", "-scp", "-r", "-P", "", "-pw", "", "./train_video/*",
                         ""],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        print('\n학습 데이터셋 전송이 완료되었습니다.\n')
elif select == '3':
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        hip = conn.get('hi_ip').decode('utf-8')
        hi_state = conn.get('hi_work').decode('utf-8')
    if hi_state == 'off':
        print('\n청각장애인용 통역기가 꺼져있습니다.')
    else:
        print('\n출력 영상 전송을 시작합니다.')
        subprocess.call([r"./pscp.exe", "-scp", "-r", "-pw", "", "./output_video/*",
                         "".format(hip)],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        print('\n출력 영상 전송이 완료되었습니다.\n')
time.sleep(3)




