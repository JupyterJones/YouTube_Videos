from flask import Flask, render_template, request, send_from_directory, send_file, url_for, redirect
import sqlite3
from datetime import datetime
from gtts import gTTS
import io
import base64  # Import the base64 module
from filters import encode_audio  # Import the custom filter function
import logging
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, concatenate_audioclips, CompositeVideoClip, CompositeAudioClip
import uuid
import shutil   
from logging.handlers import RotatingFileHandler
from flask import Flask

app = Flask(__name__)

# Configure logging
log_file = 'app.log'
max_log_size = 10 * 1024 * 1024  # 10 MB

handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Create a logger for the current module
logger = logging.getLogger(__name__)
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')



@app.route('/')
def index():
    return render_template('index.html')

# Register the custom Jinja2 filter

#def encode_audio(data):
#    return data.encode('base64').decode('utf-8')
def encode_audio(data):
    return base64.b64encode(data).decode('utf-8')


app.jinja_env.filters['encode_audio'] = encode_audio
# Log a message to verify the filter registration
if 'encode_audio' in app.jinja_env.filters:
    logger.info("Custom Jinja2 filter 'encode_audio' has been successfully registered.")
else:
    logger.warning("Custom Jinja2 filter 'encode_audio' could not be registered.")


@app.route('/searchdb', methods=['GET', 'POST'])
def searchdb():
    if request.method == 'POST':
        DATA = []
        ROWID = None  # Initialize ROWID

        search_term = request.form.get('search_input', '')  # Provide a default value
        conn = sqlite3.connect("notes.db")
        conn.text_factory = str
        c = conn.cursor()
        
        for row in c.execute("SELECT ROWID,* FROM PROJECT"):
            if search_term in row[1]:
                DATA.append("\nINFO Found in ROWID: " + str(row[0]) + "\n" + row[1])
                ROWID = row[0]  # Update ROWID
        
        return render_template('searchdb.html', DATA=DATA, ROWID=ROWID)
    
    return render_template('search_form.html')


@app.route('/show_input_form')
def show_input_form():
    # Log filter status before rendering the template
    if 'encode_audio' in app.jinja_env.filters:
        logger.debug("encode_audio filter is recognized when rendering 'input_form.html'.")
    else:
        logger.warning("encode_audio filter is NOT recognized when rendering 'input_form.html'.")

    return render_template('input_form.html')

@app.route('/insert', methods=['POST'])
def insert_into_db():
    data = request.form.get('data')
    if data:
        conn = sqlite3.connect("notes.db")
        conn.text_factory = str
        c = conn.cursor()
        
        timestamp = datetime.now().strftime("%A %x %H:%M:%S")
        data_with_timestamp = data + "\n" + timestamp
        
        c.execute("INSERT INTO PROJECT (input) VALUES (?)", (data_with_timestamp,))
        conn.commit()
        inserted_row_id = c.lastrowid  # Get the ID of the last inserted row
        
        # Retrieve the inserted row using its ID
        c.execute("SELECT * FROM PROJECT WHERE ROWID = ?", (inserted_row_id,))
        inserted_row = c.fetchone()
        
        conn.close()
        
        # Format the inserted data for display within <pre> tag
        formatted_data = "\n".join(inserted_row[0].split("\n"))
        
        return f"Data inserted successfully!\nInserted Row: <pre>{formatted_data}</pre>"
    else:
        return "No data provided."

    
    
@app.route('/delete/<int:row_id>', methods=['GET', 'POST'])
def delete_entry(row_id):
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()

    # Retrieve the data associated with the row_id
    c.execute("SELECT ROWID, * FROM PROJECT WHERE ROWID = ?", (row_id,))

    entry = c.fetchone()

    if entry:
        # Delete the entry based on the row_id
        c.execute("DELETE FROM PROJECT WHERE ROWID = ?", (row_id,))
        conn.commit()
        conn.close()

        return f"Entry with ROWID {row_id} deleted successfully!"
    else:
        conn.close()
        return f"No entry found with ROWID {row_id}."


@app.route('/static/text_history/<filename>')
def download_text(filename):
    return send_from_directory('static/text_history', filename)

@app.route('/read_text', methods=['GET', 'POST'])
def read_text():
    if request.method == 'POST':
        text = request.form.get('text', '')

        if text:
            # Save the entered text as a text file
            txt_filename = f"{text[:25].replace(' ', '-')}.txt"
            filepath = os.path.join('static', 'text_history', txt_filename)

            with open(filepath, 'w') as text_file:
                text_file.write(text)

            # Create a gTTS object to convert text to speech
            tts = gTTS(text)
            
            # Save the speech as an in-memory file
            speech_io = io.BytesIO()
            tts.write_to_fp(speech_io)
            speech_io.seek(0)

            # Generate a filename from the first 25 characters of the text for the audio file
            audio_filename = f"{text[:25].replace(' ', '-')}.mp3"
            audio_filepath = os.path.join('static', 'audio_mp3', audio_filename)

            # Save the audio file
            with open(audio_filepath, 'wb') as audio_file:
                audio_file.write(speech_io.read())

            return render_template('read_text.html', speech=speech_io.getvalue(), filename=audio_filename,app=app, txt_filename=txt_filename)

    return render_template('read_text.html', speech=None)


@app.route('/list_texts')
def list_texts():
    text_files = os.listdir(os.path.join(app.static_folder, 'text_history'))
    return render_template('list_texts.html', text_files=text_files)
@app.route('/view_texts/<filename>')
def view_texts(filename):
    return send_from_directory(os.path.join(app.static_folder, 'text_history'), filename)


@app.route('/list_audio')
def list_audio():
    audio_files = os.listdir(os.path.join(app.static_folder, 'audio_mp3'))
    return render_template('list_audio.html', audio_files=audio_files)

@app.route('/play_audio/<filename>')
def play_audio(filename):
    return send_from_directory(os.path.join(app.static_folder, 'audio_mp3'), filename)



@app.route('/create_video')
def create_video():
    gifs_directory = os.path.join(app.static_folder, 'gifs')
    video_filename = f"{uuid.uuid4().hex}gif.mp4"
    video_filepath = os.path.join(app.static_folder, 'videos', video_filename)

    gif_files = [f for f in os.listdir(gifs_directory) if f.endswith('.gif')]

    if gif_files:
        clips = [VideoFileClip(os.path.join(gifs_directory, gif)) for gif in gif_files]
        video_clip = concatenate_videoclips(clips)

        video_clip.write_videofile(video_filepath, codec='libx264')
        shutil.copy(video_filepath, 'static/videos/Gif.mp4')
        new_video ='static/videos/Gif.mp4'
        for clip in clips:
            clip.close()
        
        return render_template('create_video.html')
    else:
        return "No GIF files found."

@app.route('/static/videos/<filename>')
def download_video(filename):
    return send_from_directory('static/videos', filename)

@app.route('/show_video')
def show_video():
    return render_template('show_video.html')


if __name__ == '__main__':
    app.run(debug=True, port=5100)