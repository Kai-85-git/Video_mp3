class VideoToAudioConverter {
    constructor() {
        this.initializeElements();
        this.initializeEventListeners();
        this.loadSettings();
    }

    initializeElements() {
        // DOM要素の取得
        this.dropZone = document.getElementById('drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.fileSelect = document.getElementById('file-select');
        this.fileInfo = document.getElementById('file-info');
        this.fileName = document.getElementById('file-name');
        this.removeFile = document.getElementById('remove-file');
        this.convertButton = document.getElementById('convert-button');
        this.progressContainer = document.querySelector('.progress-container');
        this.progress = document.getElementById('progress');
        this.status = document.getElementById('status');
        this.themeToggle = document.getElementById('theme-toggle');
        this.toast = document.getElementById('toast');
        this.toastIcon = document.getElementById('toast-icon');
        this.toastMessage = document.getElementById('toast-message');
        
        // 選択されたファイル
        this.selectedFile = null;
    }

    initializeEventListeners() {
        // ドラッグ&ドロップイベント
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('drag-over');
        });

        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('drag-over');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelection(files[0]);
            }
        });

        // ファイル選択ボタン
        this.fileSelect.addEventListener('click', () => {
            this.fileInput.click();
        });

        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelection(e.target.files[0]);
            }
        });

        // ファイル削除ボタン
        this.removeFile.addEventListener('click', () => {
            this.clearFileSelection();
        });

        // 変換ボタン
        this.convertButton.addEventListener('click', () => {
            this.startConversion();
        });

        // テーマ切り替え
        this.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });
    }

    loadSettings() {
        const theme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', theme);
        this.themeToggle.querySelector('.material-icons').textContent = 
            theme === 'dark' ? 'light_mode' : 'dark_mode';
    }

    handleFileSelection(file) {
        const validTypes = ['.mp4', '.avi', '.mov', '.mkv'];
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(extension)) {
            this.showToast('error', 'サポートされていない形式のファイルです');
            return;
        }

        this.selectedFile = file;
        this.fileName.textContent = file.name;
        this.fileInfo.hidden = false;
        this.convertButton.disabled = false;
    }

    clearFileSelection() {
        this.selectedFile = null;
        this.fileInput.value = '';
        this.fileInfo.hidden = true;
        this.convertButton.disabled = true;
    }

    async startConversion() {
        if (!this.selectedFile) return;

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('format', document.querySelector('input[name="format"]:checked').value);

        this.convertButton.disabled = true;
        this.progressContainer.hidden = false;
        this.status.textContent = '変換中...';

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '変換に失敗しました');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = this.selectedFile.name.replace(/\.[^/.]+$/, '.mp3');
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showToast('success', '変換が完了しました');
            this.clearFileSelection();
        } catch (error) {
            console.error('変換エラー:', error);
            this.showToast('error', error.message);
        } finally {
            this.convertButton.disabled = false;
            this.progressContainer.hidden = true;
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        this.themeToggle.querySelector('.material-icons').textContent = 
            newTheme === 'dark' ? 'light_mode' : 'dark_mode';
    }

    showToast(type, message) {
        this.toast.className = 'toast ' + type;
        this.toastIcon.textContent = type === 'error' ? 'error' : 'check_circle';
        this.toastMessage.textContent = message;
        this.toast.hidden = false;

        setTimeout(() => {
            this.toast.hidden = true;
        }, 3000);
    }
}

// アプリケーションの初期化
window.addEventListener('DOMContentLoaded', () => {
    new VideoToAudioConverter();
}); 