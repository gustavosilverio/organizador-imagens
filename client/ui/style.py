APP_STYLESHEET = """
QMainWindow {
    background-color: #0F172A;
}

QWidget {
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    color: #E2E8F0;
    font-size: 13px;
}

QToolBar {
    background-color: #1E293B;
    border-bottom: 1px solid #334155;
    padding: 8px;
    spacing: 10px;
}

QToolButton {
    background-color: #334155;
    color: #F8FAFC;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #3B82F6;
    border-color: #60A5FA;
}

QToolButton:pressed {
    background-color: #2563EB;
}

#controlPanel {
    background-color: #1E293B;
    border-bottom: 1px solid #334155;
    padding: 10px 16px;
}

QLabel {
    color: #94A3B8;
    font-weight: 500;
}

QLineEdit {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F8FAFC;
}

QLineEdit:focus {
    border-color: #3B82F6;
}

QComboBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 12px;
    color: #F8FAFC;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #475569;
}

QComboBox:focus {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #334155;
    selection-background-color: #3B82F6;
    color: #F8FAFC;
    padding: 4px;
}

QScrollArea {
    background-color: #0F172A;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: #0F172A;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QStatusBar {
    background-color: #1E293B;
    border-top: 1px solid #334155;
    color: #94A3B8;
    font-size: 12px;
    padding: 4px;
}

QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton#btnDanger {
    background-color: #DC2626;
}

QPushButton#btnDanger:hover {
    background-color: #B91C1C;
}

QPushButton#btnSecondary {
    background-color: #334155;
    color: #E2E8F0;
    border: 1px solid #475569;
}

QPushButton#btnSecondary:hover {
    background-color: #475569;
}

QDialog {
    background-color: #0F172A;
}

QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #93C5FD;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QTextEdit {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    color: #F8FAFC;
}
"""
