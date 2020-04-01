
import os
import json
import platform
import requests

def uploadGyazo(file_name, imagedata, content_type, title, url, desc, timestamp):
    """
    画像のバイナリと各種メタデータを指定してGyazoへのアップロードを実行するメソッド
     
    Args:
        file_name (str): 画像のファイル名
        imagedata (binary): 画像のバイナリ
        content_type (str): 画像の mime content type
        title (str): 画像を取得したウェブサイトのタイトル
        url (str): 画像を取得したウェブサイトのURL
        desc (str): Gyazo の Description 欄に記入されるメモ
        timestamp (int): 画像の最終変更日時
    """
    # Device IDを取得する
    appdata_path = None
    appdata_filename = None
    if 'Darwin' in platform.system():
        appdata_path = os.path.expanduser('~/Library/Gyazo/')
        appdata_filename = 'id'
    elif 'Windows' in platform.system() or 'CYGWIN' in platform.system():
        appdata_path = os.getenv('APPDATA') + '\\Gyazo\\'
        appdata_filename = 'id.txt'
    elif 'Linux' in platform.system():
        appdata_path = os.path.expanduser('~/')
        appdata_filename = '.gyazo.id'
    with open(('%s%s' % (appdata_path, appdata_filename)), 'r') as device_id_file:
        device_id = device_id_file.read()

    # Gyazoにアップロードするための multipart/form-data をつくる
    # filedata
    files = {'imagedata': (file_name, imagedata, content_type)}

    # metadata
    metadata = {
        'app': "pdf-gyazo",
        'title': title,
        'url': url,
        'desc': desc
    }

    # formdata
    formdata = {
        'id': device_id,
        'scale': "1.0",
        'created_at': timestamp,
        'metadata': json.dumps(metadata)
    }

    gyazo_res = requests.post("https://upload.gyazo.com/upload.cgi", data=formdata, files=files)
    print(gyazo_res)
    print(gyazo_res.text)


from pathlib import Path


import subprocess
from shutil import which
import os.path as osp
def getPdfInfo(file_path):
    if 'Darwin' in platform.system():
        cmd = 'pdfinfo'
    elif 'Windows' in platform.system() or 'CYGWIN' in platform.system():
        cmd = 'pdfinfo.exe'
    if which(cmd) is None:
        raise RuntimeError('System command not found: %s' % cmd)

    if not osp.exists(file_path):
        raise RuntimeError('Provided input file not found: %s' % file_path)

    def _extract(row):
        """Extracts the right hand value from a : delimited row"""
        return row.split(':', 1)[1].strip()

    output = {}

    labels = ['Title', 'Author', 'Creator', 'Producer', 'CreationDate',
              'ModDate', 'Tagged', 'Pages', 'Encrypted', 'Page size',
              'File size', 'Optimized', 'PDF version']

    cmd_output = subprocess.check_output([cmd, file_path])
    for line in map(str, cmd_output.splitlines()):
        for label in labels:
            if label in line:
                output[label] = _extract(line)

    return output


from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
import io
import datetime
def uploadPdfFile(dir_path, file_path):
    pdf_path = os.path.join(dir_path, file_path)
    file_name = os.path.basename(pdf_path)
    print(pdf_path)
    title = ""
    timestamp = datetime.datetime.now().timestamp()
    try:
        pdf_info = getPdfInfo(pdf_path)
        title = pdf_info.get("Title", "")
        print(title)
        datestr = pdf_info.get("CreationDate", " ").split(" ")[0]
        print(datestr)
        try:
            datetimeobj = datetime.datetime.strptime(datestr, '%m/%d/%y')
        except ValueError as e:
             print(e)
             datefloat = os.stat(pdf_path).st_ctime
             datetimeobj = datetime.datetime.fromtimestamp(datefloat)
        timestamp = datetimeobj.timestamp()
    except subprocess.CalledProcessError:
        print("fuck")

    try:
        if title is "":
            title = "no title"
        desc = "#pdf-gyazo #{} #{}".format(title.replace(" ", "_").replace(".", ""), file_name.replace(" ", "_"))
        print(desc)
        # PDF -> Image に変換（150dpi）
        pages = convert_from_path(str(pdf_path), 150)
        for i, page in enumerate(pages):
            output = io.BytesIO()
            page.save(output, "JPEG")
            uploadGyazo(file_name, output.getvalue(), "image/jpeg", title, None, desc, timestamp)
    except PDFPageCountError:
        print("fuck")
    

def uploadPdfFileFromDir(dir_path, recursive):
    dir_path = os.path.abspath(dir_path)
    try:
        file_and_dir = os.listdir(dir_path)
        for file_or_dir in file_and_dir:
            isFile = os.path.isfile(os.path.join(dir_path, file_or_dir))
            if isFile and file_or_dir.endswith(".pdf"):
                if file_or_dir.startswith("."):
                    continue
                uploadPdfFile(dir_path, file_or_dir)
            else:
                if recursive:
                    uploadPdfFileFromDir(os.path.join(dir_path, file_or_dir), recursive)
    except NotADirectoryError:
        isFile = os.path.isfile(dir_path)
        if isFile and dir_path.endswith(".pdf"):
            uploadPdfFile("", dir_path)

import sys
targetMethod = None
optionalArg = False
if __name__ == "__main__":
    # poppler/binを環境変数PATHに追加する
    poppler_dir = Path(__file__).parent.absolute() / "poppler/bin"
    os.environ["PATH"] += os.pathsep + str(poppler_dir)
    if (len(sys.argv) == 1):
        print("python main.py dir_path recursive")
    if (len(sys.argv) >= 2):
        targetDir = sys.argv[1]
    if (len(sys.argv) >= 3):
        optionalArg = sys.argv[2]
    uploadPdfFileFromDir(targetDir, optionalArg)
