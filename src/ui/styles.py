"""
Modern and aesthetic stylesheet for IELTS Shadowing Desktop Application.
Features clean typography, soft mint/emerald highlights, and seamless layout.
"""

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #f8fafc;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    color: #1e293b;
    font-size: 13px;
}

/* Header & Top Bar */
#topBarFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px;
}

#topicInput {
    background-color: #f1f5f9;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    color: #0f172a;
    font-weight: 500;
}

#topicInput:focus {
    border: 1.5px solid #10b981;
    background-color: #ffffff;
}

#btnGenerate {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    color: white;
    font-weight: 600;
    font-size: 13px;
    border-radius: 8px;
    padding: 8px 18px;
    border: none;
}

#btnGenerate:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
}

#btnGenerate:disabled {
    background-color: #94a3b8;
    color: #f8fafc;
}

#btnSecondary {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 4px 12px;
}

#btnSecondary:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}

#saveKeyBtn {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 2px 10px;
    min-height: 24px;
}

#saveKeyBtn:hover {
    background-color: #e2e8f0;
    color: #0f172a;
    border-color: #10b981;
}

#apiKeyInput {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    color: #334155;
}

#apiKeyInput:focus {
    border: 1px solid #10b981;
}

/* IELTS Part Tabs */
QTabBar {
    qproperty-drawBase: 0;
    background: transparent;
    border: none;
    margin-bottom: -1px;
}

QTabBar::tab {
    background: #e2e8f0;
    color: #475569;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 24px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    border: 1.5px solid #cbd5e1;
    border-bottom: 1.5px solid #a7f3d0;
    min-width: 110px;
}

QTabBar::tab:selected {
    background: #d1fae5;
    color: #065f46;
    border: 1.5px solid #10b981;
    border-bottom: 2px solid #d1fae5;
}

QTabBar::tab:hover:!selected {
    background: #f1f5f9;
    color: #0f172a;
}

/* Script Display Area */
#scriptContainer {
    background-color: #eef7ee; /* Matching soft green tint from wireframe */
    border: 1.5px solid #a7f3d0;
    border-radius: 10px;
}

#scriptBrowser {
    background-color: transparent;
    border: none;
    padding: 14px;
    font-size: 14px;
    line-height: 1.6;
}

/* Audio Player Bottom Bar */
#playerFrame {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 12px;
    padding: 8px 16px;
}

#playPauseBtn {
    background-color: #10b981;
    border-radius: 22px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border: none;
}

#playPauseBtn:hover {
    background-color: #059669;
}

#playPauseBtn:disabled {
    background-color: #cbd5e1;
}

/* Seek Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #10b981;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #059669;
    border: 2px solid #ffffff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #047857;
    transform: scale(1.2);
}

/* Status / Info Badges */
#statusBadge {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

#timeLabel {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    min-width: 90px;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #10b981;
}

QComboBox::drop-down {
    border: none;
}
"""

def generate_script_html(content: dict, active_chunk_idx: int = -1) -> str:
    """
    Renders the IELTS Question and bilingual chunks into styled HTML for QTextBrowser.
    Supports highlighting the actively spoken chunk.
    """
    part_name = content.get("part_name", f"IELTS Part {content.get('part', 1)}")
    topic = content.get("topic", "")
    question = content.get("question", "")
    band_title = content.get("band_title", "")
    band_notes = content.get("band_notes", "")
    chunks = content.get("chunks", [])

    # Format question into HTML (handling cue cards bullet points)
    formatted_question = question.replace("\n", "<br>")

    cards_html = ""
    for idx, chunk in enumerate(chunks):
        en = chunk.get("en", "")
        tr = chunk.get("tr", "")

        is_active = (idx == active_chunk_idx)
        card_bg = "#dcfce7" if is_active else "#ffffff"
        border_color = "#10b981" if is_active else "#e2e8f0"
        shadow_style = "box-shadow: 0 2px 8px rgba(16,185,129,0.25);" if is_active else "box-shadow: 0 1px 3px rgba(0,0,0,0.05);"
        active_badge = '<span style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 8px;">▶ ŞU AN ÇALIYOR</span>' if is_active else ""

        cards_html += f"""
        <div style="background-color: {card_bg}; border: 1.5px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; {shadow_style}">
            <div style="font-size: 11px; font-weight: 700; color: #059669; text-transform: uppercase; margin-bottom: 4px;">
                Adım {idx + 1} {active_badge}
            </div>
            <div style="font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; margin-bottom: 6px;">
                {en}
            </div>
            <div style="font-size: 13px; color: #475569; font-style: italic; line-height: 1.3;">
                {tr}
            </div>
        </div>
        """

    notes_html = ""
    if band_notes:
        label = f"💡 {band_title} Değerlendirme & Kelime Notları:" if band_title else "💡 Seviye & Kelime Notları:"
        notes_html = f"""
        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 8px 12px; border-radius: 6px; margin-bottom: 14px; font-size: 12px; color: #92400e;">
            <strong>{label}</strong> {band_notes}
        </div>
        """

    level_badge = f'<span style="background-color: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 8px; font-weight: 700;">{band_title}</span>' if band_title else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', -apple-system, sans-serif;
                background-color: transparent;
                margin: 0;
                padding: 4px;
            }}
        </style>
    </head>
    <body>
        <!-- Header Question Box -->
        <div style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px;">
            <div style="font-size: 12px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.5px;">
                {part_name} &bull; Konu: {topic} {level_badge}
            </div>
            <div style="font-size: 15px; font-weight: 700; color: #1e293b; margin-top: 6px; line-height: 1.4;">
                {formatted_question}
            </div>
        </div>

        {notes_html}

        <!-- Speech Chunks (Hear-Pause-Repeat) -->
        <div style="margin-top: 10px;">
            {cards_html}
        </div>
    </body>
    </html>
    """
    return html
