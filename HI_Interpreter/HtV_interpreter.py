import os
import time
import redis
import uvicorn
import shutil
from fastapi import FastAPI, File, UploadFile
import cv2
from PIL import ImageFont, ImageDraw, Image
import numpy as np


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')
app = FastAPI()


def video_play(video_file, arg):
    cap = cv2.VideoCapture(video_file)
    if cap.isOpened():
        while True:
            ret, img = cap.read()
            if ret:
                fontpath = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
                font = ImageFont.truetype(fontpath, size=40)
                W, H = (650, 1200)
                img_pil = Image.fromarray(img)
                draw = ImageDraw.Draw(img_pil)
                _, _, w, h = font.getbbox(arg)
                draw.text(((W - w) / 2, (H - h) / 2 - 70), arg, font=font, fill=(255, 255, 255, 0))
                img = np.array(img_pil)
                cv2.imshow(video_file, img)
                cv2.waitKey(15)
            else:
                break
    else:
        print("Can't open video.")
    cap.release()
    cv2.destroyAllWindows()


def ttv(arg):
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        v = conn.get(arg)
        if v is not None:
            if arg == '니' or arg == '자' or arg == '나요' or arg == '니까' or arg == '까요' or arg == '가요' or arg == '습니까' or arg == '은가요' or arg == '할까요':
                pass
            elif arg[-3:] == '습니까':
                arg = arg[:-3]
            elif arg[-3:] == '은가요':
                arg = arg[:-3]
            elif arg[-3:] == '할까요':
                arg = arg[:-3]
            elif arg[-2:] == '나요':
                arg = arg[:-2]
            elif arg[-2:] == '니까':
                arg = arg[:-2]
            elif arg[-2:] == '까요':
                arg = arg[:-2]
            elif arg[-2:] == '가요':
                arg = arg[:-2]
            elif arg[-2:] != '하자' and arg[-1:] == '자':
                arg = arg[:-1]
            elif arg[-1:] == '니':
                arg = arg[:-1]
            video_file = v.decode('utf-8')
            video_play(video_file, arg)
        else:
            pass
    print(arg)


@app.post("/HtV_interpreter/")
async def create_upload_file():
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        res = conn.get('send_txt').decode('utf-8')
        conn.set('send_txt', '')
        # print(res)
        tmp = conn.hgetall('compound_key')
        for x in tmp:
            wrd = str(x.decode('utf-8'))
            # print(wrd)
            if wrd in res:
                res = res.replace(wrd, str(tmp[x].decode('utf-8')))
        v = conn.get(res)
    print(res)

    if v is not None:
        ttv(res)
    else:
        words = res.split()
        n = len(words)
        # print(n)
        for x in range(n):
            if x < n-1:
                if conn.get(words[x]) == conn.get(words[x] + ' ' + words[x+1]):
                    ttv(words[x])
                else:
                    ttv(words[x])
                    ttv(words[x] + ' ' + words[x+1])
            else:
                print(words[n - 1][-3:])
                if words[n-1][-3:] == '습니까':
                    ttv(words[n-1])
                    ttv('습니까')
                elif words[n-1][-3:] == '은가요':
                    ttv(words[n-1])
                    ttv('은가요')
                elif words[n-1][-3:] == '할까요':
                    ttv(words[n-1])
                    ttv('할까요')
                elif words[n-1][-2:] == '나요':
                    ttv(words[n-1])
                    ttv('나요')
                elif words[n-1][-2:] == '니까':
                    ttv(words[n-1])
                    ttv('니까')
                elif words[n-1][-2:] == '까요':
                    ttv(words[n-1])
                    ttv('까요')
                elif words[n-1][-2:] == '가요':
                    ttv(words[n-1])
                    ttv('가요')
                elif words[n-1][-2:] != '하자' and words[n-1][-1:] == '자':
                    ttv(words[n-1])
                    ttv('자')
                elif words[n-1][-1:] == '니':
                    ttv(words[n-1])
                    ttv('니')
                else:
                    ttv(words[n-1])


if __name__ == "__main__":
    uvicorn.run("HtV_interpreter:app", host="0.0.0.0", port=8000, log_level="debug")
 