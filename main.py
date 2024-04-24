import json
import requests
import time
from urllib.parse import urlparse
import os
import urllib
import config
import shutil
import yt_dlp as youtube_dl

TOKEN = ""
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
DESC = "DESCRIÇÃO"
HELP = "AJUDA"
ffmpeg_path = shutil.which("ffmpeg")

if ffmpeg_path:
    os.environ['PATH'] += os.pathsep + os.path.dirname(ffmpeg_path)

YDL_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(id)s.%(ext)s',
    'ffmpeg_location': 'C:\\ffmpeg',
    'ffmpeg': 'C:\\ffmpeg\\ffmpeg.exe',
    'ffprobe': 'C:\\ffmpeg\\ffprobe.exe',
}

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def download_all(updates):
    for update in updates["result"]:
        if "message" not in update or "text" not in update["message"]:
            continue

        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        print(text)

        if text == r'/start':
            send_message(DESC, chat)
            continue
        if text == r'/help':
            send_message(HELP, chat)
            continue
        if not uri_validator(text):
            send_message("Envie-me um URL válido e farei o download para você."
                         "Não me mande lixo!", chat)
            continue

        with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
            try:
                info_dict = ydl.extract_info(text, download=True)
                send_message(
                    "Baixando e extraindo mp3 de {}".format(text), chat)
                result = info_dict.get('title', 'Untitled')
                send_message(
                    "{} baixado. Enviando para você...".format(result), chat)
            except Exception as e:
                send_message(
                    "Não foi possível fazer download do arquivo {}. Erro: {}".format(text, str(e)),
                    chat
                )
                continue

            try:
                downloaded_file = "{}.mp3".format(info_dict['id'])
                file_to_send = fix_filename(result) + ".mp3"
                os.rename(downloaded_file, file_to_send)
                if os.path.exists(file_to_send):
                    s = send_audio(file_to_send, chat)
                    if s['ok']:
                        os.remove(file_to_send)
                    else:
                        send_message("Falha no envio:(", chat)
            except Exception as e:
                send_message("Não foi possível enviar {}. Erro: {}".format(text, str(e)), chat)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)

def send_audio(filepath, chat_id):
    print("Enviando arquivo: {}".format(filepath))
    url = URL + "sendAudio?chat_id={}".format(chat_id)
    files = {'audio': open(filepath, 'rb')}
    r = requests.post(url, files=files)
    return json.loads(r.text)

def send_help(chat_id):
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(HELP, chat_id)
    get_url(url)

def uri_validator(x):
    try:
        result = urlparse(x)
        return result.scheme and result.netloc and result.path
    except:
        return False

def fix_filename(filename):
    keepcharacters = (' ', '.', '_')
    return "".join(
        c for c in filename if c.isalnum() or c in keepcharacters
    ).replace(" ", "_")

def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            download_all(updates)

if __name__ == '__main__':
    main()