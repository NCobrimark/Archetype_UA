from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from typing import Dict, Any

def generate_pdf_report(
    user_name: str,
    meta_archetype_title: str,
    scoring_data: Dict[str, Any],
    strategy_content: str,
    chart_buffer: io.BytesIO
) -> io.BytesIO:
    """
    Generates a PDF report.
    Returns BytesIO.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1, # Center
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    heading_style = styles['Heading2']
    
    # 1. Cover Page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("ARCHETYPE STRATEGY REPORT", title_style))
    story.append(Spacer(1, 0.5 * inch))
    if meta_archetype_title:
        story.append(Paragraph(f"Your Meta-Archetype:<br/><b>{meta_archetype_title}</b>", title_style))
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(f"Prepared for: {user_name}", normal_style))
    story.append(PageBreak())
    
    # 2. Chart Section
    story.append(Paragraph("Your Archetype Profile", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Add Chart Image
    # ReportLab needs a file path or PIL image? It accepts file-like usually?
    # Image(filename_or_object, width, height)
    img = Image(chart_buffer, width=6*inch, height=6*inch)
    story.append(img)
    story.append(PageBreak())
    
    # 3. Strategy Content (Markdown to Paragraphs - Simplified)
    # Ideally we parse markdown. For MVP, we treat as raw text or simple split.
    story.append(Paragraph("Strategic Recommendations", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Split by newlines and add paragraphs
    lines = strategy_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        if line.startswith('#'):
            story.append(Paragraph(line.lstrip('#').strip(), heading_style))
        elif line.startswith('- '):
             story.append(Paragraph(f"• {line[2:]}", normal_style))
        else:
            story.append(Paragraph(line, normal_style))
            
    # Build
    doc.build(story)
    buffer.seek(0)
    return buffer
