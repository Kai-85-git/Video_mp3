import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from moviepy.editor import VideoFileClip
import os
from tkinter.ttk import Style
import threading
from pathlib import Path
import json
from tkinterdnd2 import DND_FILES, TkinterDnD

class ModernVideoToAudioConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("動画音声抽出ツール")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")
        
        # 設定の読み込み
        self.settings = self.load_settings()
        
        # スタイルの設定
        self.style = Style()
        self.style.configure('Modern.TButton', font=('Yu Gothic UI', 10))
        self.style.configure('Modern.TLabel', font=('Yu Gothic UI', 10))
        self.style.configure('Title.TLabel', font=('Yu Gothic UI', 16, 'bold'))
        
        self.setup_ui()
        
        # ドラッグ&ドロップの設定
        if hasattr(self.root, 'drop_target_register'):
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        
        # 変数の初期化
        self.video_path = None
        self.output_dir = None
        self.is_converting = False
        
    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'theme': 'light',
                'last_output_dir': None,
                'default_format': 'mp3'
            }
    
    def save_settings(self):
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.settings, f)
    
    def setup_ui(self):
        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(
            self.main_frame,
            text="動画から音声を抽出",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 20))
        
        # ドラッグ&ドロップエリア
        self.drop_frame = ttk.LabelFrame(
            self.main_frame,
            text="ここに動画ファイルをドラッグ&ドロップ",
            padding="30"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # ファイル選択ボタン
        self.select_button = ttk.Button(
            self.drop_frame,
            text="動画ファイルを選択",
            command=self.select_video,
            style='Modern.TButton'
        )
        self.select_button.pack(pady=20)
        
        # 選択されたファイル名表示
        self.file_label = ttk.Label(
            self.drop_frame,
            text="ファイルが選択されていません",
            style='Modern.TLabel'
        )
        self.file_label.pack(pady=10)
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(
            self.main_frame,
            text="設定",
            padding="10"
        )
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 出力形式選択
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            format_frame,
            text="出力形式:",
            style='Modern.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar(value=self.settings.get('default_format', 'mp3'))
        ttk.Radiobutton(
            format_frame,
            text="MP3",
            variable=self.format_var,
            value="mp3"
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            format_frame,
            text="WAV",
            variable=self.format_var,
            value="wav"
        ).pack(side=tk.LEFT, padx=10)
        
        # 出力フォルダ選択
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            folder_frame,
            text="出力フォルダ:",
            style='Modern.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_label = ttk.Label(
            folder_frame,
            text="デフォルト（動画と同じフォルダ）",
            style='Modern.TLabel'
        )
        self.folder_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            folder_frame,
            text="変更",
            command=self.select_output_folder,
            style='Modern.TButton'
        ).pack(side=tk.LEFT)
        
        # 変換ボタン
        self.convert_button = ttk.Button(
            self.main_frame,
            text="音声を抽出",
            command=self.convert_to_audio,
            style='Modern.TButton'
        )
        self.convert_button.pack(pady=10)
        self.convert_button.state(['disabled'])
        
        # プログレスバー
        self.progress = ttk.Progressbar(
            self.main_frame,
            mode='indeterminate'
        )
        
        # ステータスラベル
        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            style='Modern.TLabel'
        )
        self.status_label.pack(pady=10)
        
        # テーマ切り替えボタン
        theme_button = ttk.Button(
            self.main_frame,
            text="テーマ切り替え",
            command=self.toggle_theme,
            style='Modern.TButton'
        )
        theme_button.pack(side=tk.BOTTOM, pady=10)
    
    def handle_drop(self, event):
        file_path = event.data
        if self.is_valid_video_file(file_path):
            self.video_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.convert_button.state(['!disabled'])
        else:
            messagebox.showerror("エラー", "サポートされていない形式のファイルです")
    
    def is_valid_video_file(self, file_path):
        valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
        return file_path.lower().endswith(valid_extensions)
    
    def select_video(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("動画ファイル", "*.mp4 *.avi *.mov *.mkv")]
        )
        if file_path:
            self.video_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.convert_button.state(['!disabled'])
    
    def select_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_dir = folder_path
            self.folder_label.config(text=folder_path)
            self.settings['last_output_dir'] = folder_path
            self.save_settings()
    
    def convert_to_audio(self):
        if not self.video_path:
            messagebox.showerror("エラー", "動画ファイルが選択されていません")
            return
        
        self.convert_button.state(['disabled'])
        self.progress.pack(pady=10)
        self.progress.start()
        self.status_label.config(text="変換中...")
        
        # 出力パスの設定
        output_dir = self.output_dir or os.path.dirname(self.video_path)
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.{self.format_var.get()}")
        
        # 変換処理を別スレッドで実行
        thread = threading.Thread(
            target=self.convert_thread,
            args=(output_path,)
        )
        thread.start()
    
    def convert_thread(self, output_path):
        try:
            video = VideoFileClip(self.video_path)
            audio = video.audio
            audio.write_audiofile(output_path)
            
            # リソースの解放
            video.close()
            audio.close()
            
            self.root.after(0, self.conversion_complete, output_path)
            
        except Exception as e:
            self.root.after(0, self.conversion_error, str(e))
    
    def conversion_complete(self, output_path):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="変換が完了しました")
        self.convert_button.state(['!disabled'])
        messagebox.showinfo("完了", f"音声の抽出が完了しました\n保存先: {output_path}")
    
    def conversion_error(self, error_message):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="エラーが発生しました")
        self.convert_button.state(['!disabled'])
        messagebox.showerror("エラー", f"変換中にエラーが発生しました: {error_message}")
    
    def toggle_theme(self):
        current_theme = self.settings.get('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        
        if new_theme == 'dark':
            self.root.configure(bg='#2b2b2b')
            self.style.configure('Modern.TButton', background='#404040')
            self.style.configure('Modern.TLabel', background='#2b2b2b', foreground='white')
        else:
            self.root.configure(bg='#f0f0f0')
            self.style.configure('Modern.TButton', background='#e0e0e0')
            self.style.configure('Modern.TLabel', background='#f0f0f0', foreground='black')
        
        self.settings['theme'] = new_theme
        self.save_settings()

if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
        app = ModernVideoToAudioConverter(root)
        root.mainloop()
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        print("ドラッグ&ドロップ機能は使用できませんが、ファイル選択ボタンは使用できます。") 