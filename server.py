from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from moviepy.editor import VideoFileClip
import shutil
import json
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__, static_folder='static')
CORS(app)

# 一時ディレクトリの設定
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB（Vercelの制限）

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/convert', methods=['POST'])
def convert_video():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'ファイルがアップロードされていません'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'ファイルが選択されていません'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'サポートされていないファイル形式です'}), 400
        
        # ファイルサイズのチェック
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            return jsonify({'success': False, 'error': 'ファイルサイズが大きすぎます。50MB以下のファイルを選択してください。'}), 413
        
        format = request.form.get('format', 'mp3')
        output_dir = request.form.get('output_dir', '')
        
        # 安全なファイル名を生成
        safe_filename = secure_filename(file.filename)
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # 効率的なファイル保存
        with open(temp_video_path, 'wb') as f:
            chunk_size = 1024 * 1024  # 1MB
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        
        try:
            # 動画から音声を抽出（メモリ使用量を抑えるため、一時ファイルを使用）
            video = VideoFileClip(temp_video_path)
            if video.audio is None:
                raise Exception('動画に音声トラックが含まれていません')
            
            audio = video.audio
            
            # 出力ファイル名を生成
            output_filename = os.path.splitext(safe_filename)[0] + '.' + format
            output_path = os.path.join(output_dir, output_filename) if output_dir else os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            # 音声を保存（メモリ使用量を抑えるため、一時ファイルを使用）
            audio.write_audiofile(output_path, codec='libmp3lame', bitrate='192k')
            
            # ファイルを読み込んでレスポンスとして返す
            with open(output_path, 'rb') as f:
                file_data = f.read().hex()
            
            # リソースの解放
            video.close()
            audio.close()
            
            # 一時ファイルを削除
            os.remove(temp_video_path)
            if not output_dir:
                os.remove(output_path)
            
            response = {
                'success': True,
                'message': '変換が完了しました',
                'file_name': output_filename,
                'file_data': file_data,
                'file_path': output_path if output_dir else None
            }
            
            return jsonify(response)
            
        except Exception as e:
            # エラーが発生した場合、一時ファイルを削除
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({'success': False, 'error': str(e)}), 500
            
    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'ファイルサイズが大きすぎます。50MB以下のファイルを選択してください。'}), 413
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Vercel用のエンドポイント
@app.route('/api/convert', methods=['POST'])
def api_convert():
    return convert_video()

# エラーハンドラー
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Not Found'}), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'ファイルサイズが大きすぎます。50MB以下のファイルを選択してください。'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

# すべてのエラーをJSONで返すように設定
@app.after_request
def after_request(response):
    if response.status_code >= 400:
        try:
            data = json.loads(response.get_data())
        except:
            data = {'success': False, 'error': response.get_data(as_text=True)}
        response.set_data(json.dumps(data))
        response.headers['Content-Type'] = 'application/json'
    return response

if __name__ == '__main__':
    app.run(debug=True) 