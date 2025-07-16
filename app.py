from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp
import os
import tempfile
import re
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Для flash-сообщений


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        format_type = request.form.get('format', 'video')
        quality = request.form.get('quality', 'best')

        if not url:
            flash('Введите ссылку на видео!', 'error')
            return redirect(url_for('index'))

        if not is_valid_url(url):
            flash('Некорректная ссылка!', 'error')
            return redirect(url_for('index'))

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                if format_type == 'audio':
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }
                else:  # video
                    # Если пользователь выбрал качество, например 1080p
                    if quality == 'best':
                        fmt = 'bestvideo+bestaudio/best'
                    else:
                        fmt = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
                    ydl_opts = {
                        'format': fmt,
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'merge_output_format': 'mp4',
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = clean_filename(info.get('title', 'video'))
                    if format_type == 'audio':
                        filename = f"{title}.mp3"
                    else:
                        # Получаем расширение
                        ext = info.get('ext', 'mp4')
                        filename = f"{title}.{ext}"

                    filepath = os.path.join(tmpdir, filename)
                    # Иногда yt-dlp может дать другое расширение, ищем файл по маске
                    if not os.path.exists(filepath):
                        for f in os.listdir(tmpdir):
                            if f.startswith(title):
                                filepath = os.path.join(tmpdir, f)
                                break

                    return send_file(filepath, as_attachment=True, download_name=filename)
            except Exception as e:
                flash(f'Ошибка: {str(e)}', 'error')
                return redirect(url_for('index'))

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
