#!/usr/bin/env python3
import sys
import os
import traceback
import tempfile
from PIL import Image
import nudenet

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QPlainTextEdit, QMessageBox, QHBoxLayout,
    QScrollArea, QStatusBar, QGraphicsDropShadowEffect, QDialog, QTabWidget, QTextBrowser
)
from PySide6.QtGui import QPixmap, QIcon, QColor, QAction
from PySide6.QtCore import Qt, QThread, Signal, QSize, QSettings

# Constantes para configurações e caminhos
APP_TITLE = "DEXTER - Detecção e Censura"
ICON_PATH = r"C:\Projetos\dexter\punisher1.ico"
WINDOW_SIZE = (800, 600)
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif')


# Janela de boas-vindas
class WelcomeDialog(QDialog):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bem-vindo ao DEXTER")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setFixedSize(*WINDOW_SIZE)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Cria abas para "Sobre" e "Como Usar"
        tabs = QTabWidget()
        about_tab = QTextBrowser()
        about_tab.setHtml("""
            <h2 style="color: #dc143c;"><strong>DEXTER - Detecção e Censura</strong></h2>
            <p><strong>Versão 0.2</strong></p>
            <p>Desenvolvido por <strong>MGKzzz</strong></p>
            <hr>
            <p><strong>Este software utiliza uma rede neural para detecção e censura automática de pornografia infantil e conteúdo explícito em imagens, realizando a análise completa em pastas sem que o usuário tenha contato direto com o conteúdo sensível.</strong></p>
            <p><strong>Recursos principais:</strong></p>
            <ul>
                <li><strong>Processamento em lote de pastas</strong></li>
                <li><strong>Visualização opcional dos resultados</strong></li>
                <li><strong>Censura automática para preservação da vítima/terceiro</strong></li>
                <li><strong>Registro detalhado de atividades</strong></li>
                <li><strong>Segurança e privacidade</strong></li>
            </ul>
            <p>⚠️ <strong>Aviso Importante: Este software não garante 100% de precisão. Sempre revise os resultados.</strong></p>
        """)
        
        tutorial_tab = QTextBrowser()
        tutorial_tab.setHtml("""
            <h2 style="color: #dc143c;">Como Usar</h2>
            <ol>
                <li>Clique em <strong>'Selecionar Pasta'</strong> para escolher a pasta com as imagens.</li>
                <li>Ajuste as configurações se necessário (em desenvolvimento).</li>
                <li>Clique em <strong>'Iniciar Análise'</strong>.</li>
                <li>Aguarde o processamento completo.</li>
                <li>Use <strong>'Ver Censuras'</strong> para visualizar os resultados.</li>
            </ol>
            <h3>Dicas Importantes:</h3>
            <ul>
                <li>Formatos suportados: PNG, JPG, JPEG, WEBP, BMP, tiff, tif</li>
                <li>Mantenha backups das imagens originais</li>
                <li>O processamento pode demorar para um grande número de imagens</li>
            </ul>
        """)
        
        tabs.addTab(about_tab, "Sobre")
        tabs.addTab(tutorial_tab, "Como Usar")
        
        btn_ok = QPushButton("Começar!")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("background-color: #8b0f0f; color: white; padding: 8px;")
        
        layout.addWidget(tabs)
        layout.addWidget(btn_ok)


# Thread de processamento de imagens
class ImageProcessor(QThread):
    progress = Signal(int)
    status = Signal(str, str)  # (texto, cor)
    log = Signal(str)
    finished_processing = Signal(list)

    def __init__(self, folder_path: str) -> None:
        super().__init__()
        self.folder_path = folder_path
        self.cancel_requested = False
        self.detector = None
        self.initialization_error = None
        self.temp_dir = None
        self.censored_images = []

        # Inicializa o detector de nudez
        try:
            self.detector = nudenet.NudeDetector()
        except Exception as e:
            self.initialization_error = str(e)
            self.log.emit(f"Erro ao inicializar NudeDetector: {e}")

    def validate_image(self, file_path: str) -> bool:
        """
        Valida se o arquivo é uma imagem válida.
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            self.log.emit(f"Imagem inválida: {os.path.basename(file_path)} - {str(e)}")
            return False

    def run(self) -> None:
        if not self.detector:
            self.log.emit("Erro: Detector não inicializado!")
            self.status.emit("Erro de inicialização", "red")
            return

        try:
            # Cria diretório temporário para imagens censuradas
            self.temp_dir = tempfile.TemporaryDirectory(prefix="dexter_")
            files = [
                f for f in os.listdir(self.folder_path)
                if f.lower().endswith(SUPPORTED_EXTENSIONS)
            ]
            total = len(files)

            if total == 0:
                self.log.emit("Nenhuma imagem válida encontrada!")
                self.status.emit("Concluído", "green")
                return

            for idx, file in enumerate(files, 1):
                if self.cancel_requested:
                    break

                full_path = os.path.join(self.folder_path, file)
                if not self.validate_image(full_path):
                    continue

                self.log.emit(f"Analisando: {file}")
                try:
                    detections = self.detector.detect(full_path)
                    if detections:
                        self.log.emit("Nudez detectada - Censurando...")
                        censored_path = self.censor_image(full_path)
                        self.censored_images.append(censored_path)
                except Exception as e:
                    self.log.emit(f"Erro ao processar {file}: {traceback.format_exc()}")

                self.progress.emit(int((idx / total) * 100))

            self.finished_processing.emit(self.censored_images)
            status_text = "Cancelado" if self.cancel_requested else "Concluído"
            color = "orange" if self.cancel_requested else "green"
            self.status.emit(status_text, color)

        except Exception as e:
            self.log.emit(f"Erro fatal: {traceback.format_exc()}")
            self.status.emit("Erro crítico", "red")

    def censor_image(self, file_path: str) -> str:
        """
        Aplica censura na imagem e salva no diretório temporário.
        """
        try:
            output_path = os.path.join(self.temp_dir.name, os.path.basename(file_path))
            return self.detector.censor(file_path, output_path=output_path)
        except Exception as e:
            self.log.emit(f"Erro na censura: {traceback.format_exc()}")
            raise

    def cancel(self) -> None:
        """Sinaliza o cancelamento do processamento."""
        self.cancel_requested = True
        self.log.emit("Processamento cancelado pelo usuário!")

    def cleanup(self) -> None:
        """Realiza a limpeza manual do diretório temporário."""
        if self.temp_dir:
            self.temp_dir.cleanup()


# Classe principal da aplicação
class DexterApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.folder_path: str = ""
        self.processor: ImageProcessor | None = None
        self.censored_images: list[str] = []
        self.current_image_index: int = 0

        self.setup_window()
        self.init_ui()
        self.show_welcome_dialog()
        
    def show_welcome_dialog(self) -> None:
        # Definição correta do método de boas-vindas
        dialog = WelcomeDialog(self)
        dialog.exec()

    def setup_window(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, *WINDOW_SIZE)
        self.setMinimumSize(*WINDOW_SIZE)
        self.setWindowIcon(QIcon(ICON_PATH))

    def init_ui(self) -> None:
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.setup_styles()
        self.create_header()
        self.create_folder_controls()
        self.create_progress_bar()
        self.create_log_panel()
        self.create_status_bar()

    def setup_styles(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QPushButton {
                background-color: #8b0f0f;
                color: white;
                border: 2px solid #5a0a0a;
                padding: 8px 12px;
                border-radius: 4px;
                min-width: 120px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a0a0a;
                border-color: #8b0f0f;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
                border-color: #666;
            }
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                background: #222;
                height: 25px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ff4444;
                width: 10px;
            }
            QPlainTextEdit {
                background-color: #222;
                color: #ddd;
                border: 1px solid #333;
                border-radius: 3px;
                font-family: Consolas;
                font-size: 10pt;
                padding: 5px;
            }
            QLabel { color: #ddd; margin: 5px; }
            QScrollArea { border: none; }
            QDialog { background-color: #2a2a2a; }
            QTextBrowser { background-color: #1a1a1a; color: #ddd; border: none; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab {
                background: #333;
                color: #ddd;
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #8b0f0f;
                color: white;
            }
        """)

    def create_header(self) -> None:
        header = QLabel("DEXTER - Detecção e Censura")
        header.setAlignment(Qt.AlignCenter)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(2, 2)
        header.setGraphicsEffect(shadow)
        header.setStyleSheet("font-size: 20px; color: #dc143c; font-weight: bold; margin: 15px 0;")
        self.main_layout.addWidget(header)

    def create_folder_controls(self) -> None:
        self.btn_select_folder = QPushButton("📁 Selecionar Pasta")
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_folder.setIconSize(QSize(20, 20))
        self.main_layout.addWidget(self.btn_select_folder)

        self.lbl_folder = QLabel("Nenhuma pasta selecionada")
        self.lbl_folder.setStyleSheet("color: #888; font-style: italic;")
        self.main_layout.addWidget(self.lbl_folder)

    def create_progress_bar(self) -> None:
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Progresso: %p%")
        self.main_layout.addWidget(self.progress_bar)

    def create_log_panel(self) -> None:
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Log de atividades...")
        self.txt_log.document().setMaximumBlockCount(1000)
        self.main_layout.addWidget(self.txt_log)

    def create_status_bar(self) -> None:
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_start = QPushButton("▶ Iniciar Análise")
        self.btn_start.clicked.connect(self.start_processing)

        self.btn_cancel = QPushButton("⏹ Cancelar")
        self.btn_cancel.clicked.connect(self.cancel_processing)
        self.btn_cancel.setEnabled(False)

        self.btn_view = QPushButton("👁 Ver Censuras")
        self.btn_view.clicked.connect(self.view_images)
        self.btn_view.setEnabled(False)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_cancel)
        control_layout.addWidget(self.btn_view)
        status_bar.addPermanentWidget(control_panel)

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta com Imagens")
        if folder:
            self.folder_path = os.path.abspath(folder)
            self.lbl_folder.setText(f"Pasta selecionada: {self.folder_path}")
            self.txt_log.appendPlainText(f"Pasta selecionada: {self.folder_path}")
            self.btn_view.setEnabled(False)

    def start_processing(self) -> None:
        if not self.folder_path:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta primeiro!")
            return

        if self.processor and self.processor.isRunning():
            QMessageBox.warning(self, "Aviso", "Processamento já em andamento!")
            return

        self.processor = ImageProcessor(self.folder_path)
        if self.processor.initialization_error:
            QMessageBox.critical(
                self,
                "Erro de Inicialização",
                f"Falha ao inicializar o detector:\n{self.processor.initialization_error}"
            )
            return

        # Conecta sinais
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.log.connect(self.txt_log.appendPlainText)
        self.processor.finished_processing.connect(self.processing_finished)
        self.processor.status.connect(self.update_status)

        # Atualiza a interface
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_view.setEnabled(False)
        self.statusBar().showMessage("Status: Processando...")
        self.processor.start()

    def cancel_processing(self) -> None:
        if self.processor:
            self.processor.cancel()
            self.btn_cancel.setEnabled(False)
            self.btn_start.setEnabled(True)
            self.statusBar().showMessage("Status: Cancelado pelo usuário")

    def processing_finished(self, censored_images: list) -> None:
        self.censored_images = censored_images
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_view.setEnabled(bool(censored_images))
        self.progress_bar.setValue(0)
        
        if censored_images:
            self.statusBar().showMessage("Status: Processamento concluído com sucesso")
        else:
            self.statusBar().showMessage("Status: Nenhuma censura necessária")

    def view_images(self) -> None:
        if not self.censored_images:
            QMessageBox.information(self, "Informação", "Nenhuma imagem censurada disponível")
            return

        valid_images = [img for img in self.censored_images if os.path.exists(img)]
        if not valid_images:
            QMessageBox.warning(self, "Aviso", "As imagens censuradas não estão mais disponíveis")
            return

        viewer = QMainWindow(self)
        viewer.setWindowTitle(f"Visualizador de Censuras ({len(valid_images)} imagens)")
        viewer.resize(*WINDOW_SIZE)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)

        for img_path in valid_images:
            try:
                label = QLabel()
                label.setAlignment(Qt.AlignCenter)
                pixmap = QPixmap(img_path)
                if pixmap.isNull():
                    continue
                scaled_pixmap = pixmap.scaledToWidth(750, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.setStyleSheet("""
                    QLabel {
                        margin: 10px;
                        border: 2px solid #8b0f0f;
                        border-radius: 5px;
                        background: #1a1a1a;
                    }
                """)
                container_layout.addWidget(label)
            except Exception as e:
                self.txt_log.appendPlainText(f"Erro ao carregar imagem: {str(e)}")

        scroll_area.setWidget(container)
        viewer.setCentralWidget(scroll_area)

        # Garante que os arquivos temporários não sejam apagados durante a visualização
        viewer.destroyed.connect(self.cleanup_temp_files)
        viewer.show()

    def cleanup_temp_files(self) -> None:
        if self.processor and hasattr(self.processor, 'temp_dir'):
            try:
                self.processor.temp_dir.cleanup()
            except Exception as e:
                self.txt_log.appendPlainText(f"Erro na limpeza de arquivos temporários: {str(e)}")

    def update_status(self, text: str, color: str) -> None:
        self.statusBar().showMessage(f"Status: {text}")
        self.statusBar().setStyleSheet(f"color: {color};")

    def closeEvent(self, event) -> None:
        if self.processor and self.processor.isRunning():
            reply = QMessageBox.question(
                self,
                'Processamento em Execução',
                'Deseja realmente sair enquanto o processamento está em andamento?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.processor.cancel()
                self.processor.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            # Exemplo: reinicialização de configurações ao fechar (opcional)
            # self.reset_settings()

    def reset_settings(self) -> None:
        settings = QSettings("DexterApp", "Config")
        settings.clear()
        QMessageBox.information(self, "Configurações", "Todas as preferências foram resetadas!")
        self.show_welcome_dialog()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DexterApp()
    window.show()
    sys.exit(app.exec())