from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from moviepy.editor import VideoFileClip
import shutil
import json
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
CORS(app)

# 一時ディレクトリの設定
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

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
        
        format = request.form.get('format', 'mp3')
        
        # 安全なファイル名を生成
        safe_filename = secure_filename(file.filename)
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(temp_video_path)
        
        try:
            # 動画から音声を抽出
            video = VideoFileClip(temp_video_path)
            if video.audio is None:
                raise Exception('動画に音声トラックが含まれていません')
            
            audio = video.audio
            
            # 出力ファイル名を生成
            output_filename = os.path.splitext(safe_filename)[0] + '.' + format
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            # 音声を保存
            audio.write_audiofile(output_path)
            
            # ファイルを読み込んでレスポンスとして返す
            with open(output_path, 'rb') as f:
                file_data = f.read().hex()
            
            # リソースの解放
            video.close()
            audio.close()
            
            # 一時ファイルを削除
            os.remove(temp_video_path)
            os.remove(output_path)
            
            response = {
                'success': True,
                'message': '変換が完了しました',
                'file_name': output_filename,
                'file_data': file_data
            }
            
            return jsonify(response)
            
        except Exception as e:
            # エラーが発生した場合、一時ファイルを削除
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({'success': False, 'error': str(e)}), 500
            
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

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True) 