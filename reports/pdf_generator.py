from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from datetime import datetime
from typing import Dict, Any

def generate_pdf_report(
    user_name: str,
    user_phone: str,
    meta_archetype_title: str,
    scoring_data: Dict[str, Any],
    strategy_content: str,
    chart_buffer: io.BytesIO
) -> io.BytesIO:
    """
    Generates a PRO 10-12 page style report (compacted for PDF usability).
    """
    import os
    import json
    
    # Load detailed info
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    info_path = os.path.join(base_dir, "data", "archetype_info.json")
    archetype_info = {}
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            archetype_info = json.load(f)
    except Exception as e:
        print(f"Error loading info: {e}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    font_registered = False
    # Try common Linux paths for DejaVuSans (standard in many Docker images)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                font_name = 'DejaVuSans'
                font_registered = True
                break
            except:
                continue
    
    if not font_registered:
        font_name = 'Helvetica' # Default fallback (no Cyrillic support)

    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], fontName=font_name, fontSize=28, alignment=1, spaceAfter=40, textColor=colors.darkblue)
    subtitle_style = ParagraphStyle('SubTitle', parent=styles['Heading2'], fontName=font_name, fontSize=18, alignment=1, spaceAfter=20, textColor=colors.blue)
    heading_pro = ParagraphStyle('HeadingPro', parent=styles['Heading2'], fontName=font_name, fontSize=16, spaceBefore=20, spaceAfter=10, textColor=colors.darkblue)
    normal_pro = ParagraphStyle('NormalPro', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=14, spaceAfter=10)
    bullet_style = ParagraphStyle('Bullet', parent=normal_pro, leftIndent=20, firstLineIndent=-10)

    # 1. COVER PAGE
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("БРЕНД-СТРАТЕГІЯ ЗА АРХЕТИПАМИ", title_style))
    if meta_archetype_title:
        story.append(Paragraph(f"Ваш персональний профіль: {meta_archetype_title}", subtitle_style))
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(f"<b>Клієнт:</b> {user_name}", normal_pro))
    story.append(Paragraph(f"<b>Телефон:</b> {user_phone}", normal_pro))
    story.append(Paragraph(f"<b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}", normal_pro))
    story.append(PageBreak())

    # 2. THE ARCHETYPE WHEEL
    story.append(Paragraph("Ваша архітектура особистості", heading_pro))
    story.append(Paragraph("Цей графік відображає баланс 12 базових архетипів у вашому поточному стані. Домінантні архетипи визначають вашу стратегію поведінки та сприйняття світу.", normal_pro))
    img = Image(chart_buffer, width=5*inch, height=5*inch)
    story.append(img)
    story.append(PageBreak())

    # 3. DOMINANT ARCHETYPES (DNA)
    story.append(Paragraph("Глибинний аналіз домінантних архетипів", heading_pro))
    primary = scoring_data.get('primary_cluster', [])
    for arch_key in primary:
        # Resolve key
        key = arch_key.value if hasattr(arch_key, 'value') else str(arch_key)
        info = archetype_info.get(key, {})
        if not info: continue
        
        story.append(Paragraph(f"<b>Архетип: {info.get('title')}</b>", heading_pro))
        story.append(Paragraph(f"<i>'{info.get('motto')}'</i>", normal_pro))
        story.append(Paragraph(f"<b>Головне бажання:</b> {info.get('core_desire')}", normal_pro))
        story.append(Paragraph(f"<b>Ціль:</b> {info.get('goal')}", normal_pro))
        story.append(Paragraph(f"<b>Стратегія:</b> {info.get('strategy')}", normal_pro))
        story.append(Paragraph(f"<b>Тіньовий аспект (Shadow Side):</b> {info.get('shadow')}", normal_pro))
        story.append(Paragraph(f"<b>Словник бренду:</b> {', '.join(info.get('vocabulary', []))}", normal_pro))
        story.append(Spacer(1, 0.2 * inch))
    
    story.append(PageBreak())

    # 4. AI-GENERATED STRATEGY
    story.append(Paragraph("Персоналізована стратегія бренду", heading_pro))
    story.append(Paragraph("Цей розділ згенеровано нейромережею на основі вашої унікальної комбінації архетипів.", normal_pro))
    story.append(Spacer(1, 0.1 * inch))

    lines = strategy_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        # Simple Markdown parsing
        import re
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        
        if line.startswith('###'):
            story.append(Paragraph(line.lstrip('#').strip(), heading_pro))
        elif line.startswith('##'):
            story.append(Paragraph(line.lstrip('#').strip(), heading_pro))
        elif line.startswith('#'):
            story.append(Paragraph(line.lstrip('#').strip(), heading_pro))
        elif line.startswith('- ') or line.startswith('* '):
             story.append(Paragraph(f"• {line[2:]}", bullet_style))
        else:
            story.append(Paragraph(line, normal_pro))

    # Build
    doc.build(story)
    buffer.seek(0)
    return buffer
