from PyQt6.QtWidgets import QToolTip, QLabel
from PyQt6.QtCore import Qt

def get_score_tooltip_text(language_manager):
    """
    Returns the tooltip text for score guide based on language
    """
    if language_manager.current_language == 'tr':
        return (
            "<b>📊 Skor Rehberi</b><br>"
            "🚀 <b>90-100:</b> Güçlü Alım (Çok yüksek potansiyel)<br>"
            "📈 <b>80-89:</b> Alım (İyi fırsatlar)<br>"
            "⚖️ <b>70-79:</b> Zayıf Alım (Temkinli yaklaşım)<br>"
            "⏸️ <b>60-69:</b> Bekle (Risk yüksek)<br>"
            "⛔ <b>&lt;60:</b> İşlem Yapma! (Yüksek risk)<br>"
            "<i>💡 Yeni başlayanlar için 80+ önerilir</i>"
        )
    elif language_manager.current_language == 'en':
        return (
            "<b>📊 Score Guide</b><br>"
            "🚀 <b>90-100:</b> Strong Buy (Very high potential)<br>"
            "📈 <b>80-89:</b> Buy (Good opportunities)<br>"
            "⚖️ <b>70-79:</b> Weak Buy (Cautious approach)<br>"
            "⏸️ <b>60-69:</b> Wait (High risk)<br>"
            "⛔ <b>&lt;60:</b> Don't Trade! (High risk)<br>"
            "<i>💡 80+ recommended for beginners</i>"
        )
    elif language_manager.current_language == 'es':
        return (
            "<b>📊 Guía de Puntuación</b><br>"
            "🚀 <b>90-100:</b> Compra Fuerte (Muy alto potencial)<br>"
            "📈 <b>80-89:</b> Compra (Buenas oportunidades)<br>"
            "⚖️ <b>70-79:</b> Compra Débil (Enfoque cauteloso)<br>"
            "⏸️ <b>60-69:</b> Esperar (Alto riesgo)<br>"
            "⛔ <b>&lt;60:</b> ¡No Operar! (Alto riesgo)<br>"
            "<i>💡 80+ recomendado para principiantes</i>"
        )
    else:  # Deutsch
        return (
            "<b>📊 Punktzahl-Leitfaden</b><br>"
            "🚀 <b>90-100:</b> Starker Kauf (Sehr hohes Potenzial)<br>"
            "📈 <b>80-89:</b> Kauf (Gute Chancen)<br>"
            "⚖️ <b>70-79:</b> Schwacher Kauf (Vorsichtiger Ansatz)<br>"
            "⏸️ <b>60-69:</b> Warten (Hohes Risiko)<br>"
            "⛔ <b>&lt;60:</b> Nicht Handeln! (Hohes Risiko)<br>"
            "<i>💡 80+ für Anfänger empfohlen</i>"
        )

# Minimum skor widget'ı için örnek kullanım
def create_min_score_widget(parent_frame, language_manager):
    """
    Minimum skor seçimi widget'ı ve bilgi butonu
    """
    # Ana frame
    score_frame = QLabel(parent_frame)
    score_frame.pack(fill='x', pady=5)
    
    # Label
    score_label = QLabel(score_frame, text=language_manager.__('min_score') + ':')
    score_label.pack(side='left', padx=(0, 10))
    
    # Score input
    score_var = QToolTip(score_frame, text="75")
    score_var.setStyleSheet("QLineEdit { background-color: white; }")
    score_var.pack(side='left', padx=(0, 5))
    
    # Bilgi butonu (? işareti)
    info_button = QToolTip(score_frame, text="?")
    info_button.setStyleSheet("QPushButton { background-color: white; }")
    info_button.pack(side='left', padx=(5, 0))
    
    # Tooltip metni - dil desteğiyle
    tooltip_text = get_score_tooltip_text(language_manager)
    
    # Tooltip'i butona bağla
    ToolTip(info_button, tooltip_text)
    
    return score_frame, score_var

# Bonus: Skor derecesine göre dinamik renk değişimi
def update_score_color(entry_widget, score_value):
    """
    Skor değerine göre entry widget'ının rengini değiştirir
    """
    try:
        score = int(score_value)
        if score >= 90:
            entry_widget.setStyleSheet("QLineEdit { color: green; }")
        elif score >= 80:
            entry_widget.setStyleSheet("QLineEdit { color: blue; }")
        elif score >= 70:
            entry_widget.setStyleSheet("QLineEdit { color: orange; }")
        elif score >= 60:
            entry_widget.setStyleSheet("QLineEdit { color: brown; }")
        else:
            entry_widget.setStyleSheet("QLineEdit { color: red; }")
    except ValueError:
        entry_widget.setStyleSheet("QLineEdit { color: black; }")

# Ana window'da kullanım örneği:
"""
# Mevcut kodunuzda şu şekilde kullanabilirsiniz:

# Minimum skor frame'ini oluştur
min_score_frame, min_score_var = create_min_score_widget(settings_frame, lang_manager)

# İsteğe bağlı: Skor değiştiğinde renk güncelle
def on_score_change(*args):
    update_score_color(score_entry, min_score_var.text())

min_score_var.textChanged.connect(on_score_change)
"""