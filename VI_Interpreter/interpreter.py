import os
import uvicorn
import shutil
import redis
from openai import OpenAI
from fastapi import FastAPI, File, UploadFile


redis_pool = redis.ConnectionPool(host='192.168.10.9', port=6379, db=0, max_connections=4, password='')
app = FastAPI()
user = os.environ['USER']
with redis.StrictRedis(connection_pool=redis_pool) as conn:
    org = conn.hget('openai_key', 'organization').decode('utf-8')
    key = conn.hget('openai_key', 'OPENAI_API_KEY').decode('utf-8')
    actor = conn.hget('openai_key', 'actor1').decode('utf-8')
    gpt_model = conn.hget('openai_key', 'model').decode('utf-8')
client = OpenAI(
    organization=org,
    api_key=key,
)
conversation = [{"role": "system", "content": "You are a helpful assistant."}]

conf = 0


def translate(src, q):
    global client
    conversation.append({"role": "user", "content": src + q})
    response = client.chat.completions.create(
        model=gpt_model,
        messages=conversation,
        temperature=0,
        max_tokens=1000
    )
    answer = response.choices[0].message.content.strip()
    return answer


def tts(src):
    global client
    response = client.audio.speech.create(
        model="tts-1",
        voice=actor,
        input=src,
    )
    response.stream_to_file("./Sound/hear.mp3")
    os.system("mpg123 ./Sound/hear.mp3")


def stt(snd):
    global client
    audio_file = open(snd, "rb")
    transcript = client.audio.translations.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcript


def chat_gpt_speak():
    global client
    audio_file = open("./Sound/talk.mp3", "rb")
    speech = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    conversation.append({"role": "user", "content": speech})
    response = client.chat.completions.create(
        model=gpt_model,
        messages=conversation,
        temperature=0,
        max_tokens=1000
    )
    answer = response.choices[0].message.content.strip()
    print(answer)

    response = client.audio.speech.create(
        model="tts-1",
        voice=actor,
        input=answer,
    )
    response.stream_to_file("./Sound/answer.mp3")
    os.system("mpg123 ./Sound/answer.mp3")

    conversation.append({"role": "assistant", "content": answer}) 


@app.post("/interpreter/")
async def create_upload_file(file: UploadFile = File(...)):
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        language = conn.get('selected_lang1').decode('utf-8')
    print(language)

    with open('./Sound/receive_data.mp3', "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    question = "를 {0} 대화체로 의역해서 해설은 하지 말고 순수한 {1} 통역 내용만 보여주고 문장부호는 생략해줘! 그리고 이해를 못했을때는 아무 답변이나 멘트 말아줘!".format(language, language)
    source = stt("./Sound/receive_data.mp3")
    print(source)
    if 'Selected.' in source:
        print("empty")
    else:
        res = translate(source, question)
        print(res)
        tts(res)


@app.post("/self_interpreter/")
async def create_upload_file(file: UploadFile = File(...)):
    language = '한국어'
    with open('./Sound/receive_data.mp3', "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    question = "를 {0} 대화체로 의역해서 해설은 하지 말고 순수한 {1} 통역 내용만 보여주고 문장부호는 생략해줘! 그리고 이해를 못했을때는 아무 답변이나 멘트 말아줘!".format(language, language)
    source = stt("./Sound/receive_data.mp3")
    print(source)
    if 'Selected.' in source:
        print("empty")
    else:
        res = translate(source, question)
        if '.' in res:
            res = res.replace('.', '')
        elif '?' in res:
            res = res.replace('?', '')
        elif '!' in res:
            res = res.replace('!', '')
        return res


@app.post("/VtH_interpreter/")
async def receive_file():
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        first_word = conn.get('1st_word').decode('utf-8')
        second_word = conn.get('2nd_word').decode('utf-8')
        language = conn.get('selected_lang1').decode('utf-8')
    print(language)
    print(first_word)
    question = "단어를 {0}로 직역해서 해설은 하지 말고 순수한 {1} 통역 내용만 보여주고 문장부호는 생략해줘! 그리고 마침표가 붙은 단어만 높임말 서술어로 번역해줘!".format(language, language)

    if first_word != second_word:
        res = translate(first_word, question)
        print(res)
        if res == '가져가다':
            res = '가져가세요'
        tts(res)
        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            conn.set('2nd_word', first_word)


@app.get("/chatbot/")
async def chatbot_play():
    chat_gpt_speak()


if __name__ == "__main__":
    ip = os.popen("ping -c 2 google.com").read().strip()
    if 'transmitted' in ip:
        os.system("mpg123 ./Sound/start.mp3")
    uvicorn.run("interpreter:app", host="0.0.0.0", port=8000, log_level="debug")




