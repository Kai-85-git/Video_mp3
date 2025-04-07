from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
from moviepy.editor import VideoFileClip
import os
from werkzeug.utils import secure_filename
import tempfile
import traceback
import shutil

app = Flask(__name__, static_folder='static')
CORS(app)  # CORSを有効化
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB制限

# 静的ファイルの提供
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        file = request.files['file']
        output_format = request.form.get('format', 'mp3')
        output_dir = request.form.get('output_dir', '')  # 出力フォルダのパスを取得
        
        if file.filename == '':
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'サポートされていない形式のファイルです'}), 400
        
        temp_input = None
        temp_output = None
        
        try:
            # 一時ファイルの作成
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
            file.save(temp_input.name)
            temp_input.close()
            
            # 出力用の一時ファイル
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}')
            temp_output.close()
            
            # 動画から音声を抽出
            video = VideoFileClip(temp_input.name)
            if video.audio is None:
                raise Exception('動画に音声トラックが含まれていません')
                
            audio = video.audio
            audio.write_audiofile(temp_output.name)
            
            # リソースの解放
            video.close()
            audio.close()
            
            # 出力ファイル名の生成
            output_filename = f"{os.path.splitext(secure_filename(file.filename))[0]}.{output_format}"
            
            if output_dir and os.path.isdir(output_dir):
                # 指定された出力フォルダにファイルをコピー
                output_path = os.path.join(output_dir, output_filename)
                shutil.copy2(temp_output.name, output_path)
                return jsonify({
                    'success': True,
                    'message': f'ファイルを保存しました: {output_path}',
                    'file_path': output_path
                })
            else:
                # 出力フォルダが指定されていない場合は、ファイルをダウンロード
                with open(temp_output.name, 'rb') as f:
                    file_data = f.read()
                return jsonify({
                    'success': True,
                    'message': 'ファイルのダウンロードを開始します',
                    'file_data': file_data.hex(),
                    'file_name': output_filename
                })
            
        except Exception as e:
            # エラーの詳細情報を取得
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            print(f"エラーが発生しました: {error_details}")  # サーバー側のログに出力
            return jsonify({'error': f'変換に失敗しました: {str(e)}'}), 500
            
        finally:
            # 一時ファイルの削除
            if temp_input and os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if temp_output and os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
                
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        return jsonify({'error': '予期せぬエラーが発生しました'}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

if __name__ == '__main__':
    app.run(debug=True) 