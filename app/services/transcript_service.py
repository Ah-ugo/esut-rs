import io
import qrcode
from datetime import datetime
from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64
import json


# ESUT Brand Colors
ESUT_GREEN = colors.HexColor("#1a5c38")
ESUT_GOLD = colors.HexColor("#c9a84c")
ESUT_DARK = colors.HexColor("#1a1a2e")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MID_GRAY = colors.HexColor("#888888")
TABLE_HEADER = colors.HexColor("#1a5c38")
TABLE_ALT = colors.HexColor("#f0f7f4")


def generate_qr_code(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a5c38", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_transcript_pdf(
    student: Dict,
    programme: Dict,
    semesters: List[Dict],
    cgpa: float,
    degree_class: str,
    verification_url: str = None
) -> bytes:
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title=f"Academic Transcript - {student.get('full_name', '')}",
        author="ESUT Registry"
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # ─── HEADER ───────────────────────────────────────────────
    header_data = [[
        Paragraph(
            f"""<font color="#1a5c38" size="18"><b>ENUGU STATE UNIVERSITY</b></font><br/>
            <font color="#c9a84c" size="13"><b>OF SCIENCE AND TECHNOLOGY</b></font><br/>
            <font color="#555555" size="9">Agbani, Enugu State, Nigeria</font><br/>
            <font color="#555555" size="8">Tel: +234-042-551234 | registry@esut.edu.ng | www.esut.edu.ng</font>""",
            ParagraphStyle("header", alignment=TA_CENTER)
        )
    ]]
    
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 2, ESUT_GREEN),
        ("LINEBELOW", (0, 0), (-1, 0), 3, ESUT_GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))
    
    # Title
    title_style = ParagraphStyle(
        "TranscriptTitle",
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=ESUT_DARK,
        alignment=TA_CENTER,
        spaceAfter=4
    )
    story.append(Paragraph("OFFICIAL ACADEMIC TRANSCRIPT", title_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=ESUT_GOLD))
    story.append(Spacer(1, 0.3*cm))
    
    # ─── STUDENT INFO ─────────────────────────────────────────
    label_style = ParagraphStyle("label", fontSize=8, textColor=MID_GRAY, fontName="Helvetica-Bold")
    value_style = ParagraphStyle("value", fontSize=9, textColor=ESUT_DARK, fontName="Helvetica-Bold")
    
    # Generate QR code
    qr_data = verification_url or f"https://esut.edu.ng/verify/{student.get('matric_number', '')}"
    qr_buffer = generate_qr_code(qr_data)
    qr_image = RLImage(qr_buffer, width=2.5*cm, height=2.5*cm)
    
    student_info = [
        [
            Table([
                [Paragraph("STUDENT INFORMATION", ParagraphStyle("sec", fontSize=10, fontName="Helvetica-Bold", textColor=ESUT_GREEN))],
                [Table([
                    [Paragraph("Full Name:", label_style), Paragraph(student.get("full_name", ""), value_style)],
                    [Paragraph("Matriculation No:", label_style), Paragraph(student.get("matric_number", ""), value_style)],
                    [Paragraph("Programme:", label_style), Paragraph(programme.get("name", ""), value_style)],
                    [Paragraph("Department:", label_style), Paragraph(programme.get("department", ""), value_style)],
                    [Paragraph("Faculty:", label_style), Paragraph(programme.get("faculty", ""), value_style)],
                    [Paragraph("Entry Year:", label_style), Paragraph(str(student.get("entry_year", "")), value_style)],
                    [Paragraph("Gender:", label_style), Paragraph(student.get("gender", ""), value_style)],
                ], colWidths=[3.5*cm, 9*cm], style=TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]))],
            ], colWidths=[13*cm]),
            Table([
                [qr_image],
                [Paragraph(f"<font size='7' color='#888888'>Scan to verify<br/>{student.get('matric_number', '')}</font>",
                          ParagraphStyle("qr", alignment=TA_CENTER, fontSize=7))],
            ], colWidths=[3.5*cm])
        ]
    ]
    
    info_table = Table(student_info, colWidths=[13.5*cm, 3.5*cm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))
    
    # ─── SEMESTER RESULTS ──────────────────────────────────────
    for sem_data in semesters:
        semester_label = f"{sem_data['session']} Academic Session — {sem_data['semester'].title()} Semester"
        story.append(Paragraph(semester_label, ParagraphStyle(
            "SemHeader", fontSize=10, fontName="Helvetica-Bold",
            textColor=ESUT_GREEN, spaceBefore=6, spaceAfter=4
        )))
        
        # Table header
        col_headers = ["S/N", "Course Code", "Course Title", "Units", "Score", "Grade", "Points"]
        col_widths = [0.8*cm, 2.5*cm, 7.5*cm, 1.5*cm, 1.5*cm, 1.3*cm, 1.5*cm]
        
        table_data = [col_headers]
        total_units = 0
        total_points = 0.0
        
        for idx, result in enumerate(sem_data.get("results", []), 1):
            units = result.get("course_units", 0)
            gp = result.get("grade_point", 0.0)
            quality_pts = units * gp
            total_units += units
            total_points += quality_pts
            
            row = [
                str(idx),
                result.get("course_code", ""),
                result.get("course_title", ""),
                str(units),
                f"{result.get('score', 0):.1f}",
                result.get("grade", ""),
                f"{quality_pts:.1f}",
            ]
            table_data.append(row)
        
        gpa = round(total_points / total_units, 2) if total_units > 0 else 0.0
        table_data.append([
            "", "", Paragraph("SEMESTER TOTAL / GPA", ParagraphStyle("tot", fontSize=8, fontName="Helvetica-Bold")),
            str(total_units), "", "",
            Paragraph(f"GPA: {gpa:.2f}", ParagraphStyle("gpa", fontSize=8, fontName="Helvetica-Bold", textColor=ESUT_GREEN))
        ])
        
        result_table = Table(table_data, colWidths=col_widths)
        result_table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Data rows
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "LEFT"),
            # Alternating rows
            *[("BACKGROUND", (0, i), (-1, i), TABLE_ALT) for i in range(2, len(table_data), 2) if i < len(table_data)-1],
            # Total row
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            # Grid
            ("GRID", (0, 0), (-1, -2), 0.3, colors.HexColor("#cccccc")),
            ("LINEABOVE", (0, -1), (-1, -1), 1, ESUT_GREEN),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(result_table)
        story.append(Spacer(1, 0.3*cm))
    
    # ─── CGPA SUMMARY ─────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ESUT_GOLD))
    
    summary_data = [
        [
            Paragraph("CUMULATIVE ACADEMIC PERFORMANCE", ParagraphStyle(
                "cgpa_title", fontSize=11, fontName="Helvetica-Bold", textColor=ESUT_GREEN, alignment=TA_CENTER
            ))
        ],
        [
            Table([
                [
                    Table([
                        [Paragraph("Cumulative GPA (CGPA):", label_style),
                         Paragraph(f"<b>{cgpa:.2f} / 5.00</b>", ParagraphStyle("cgpa_val", fontSize=14, fontName="Helvetica-Bold", textColor=ESUT_GREEN))],
                        [Paragraph("Degree Classification:", label_style),
                         Paragraph(f"<b>{degree_class}</b>", ParagraphStyle("dc_val", fontSize=10, fontName="Helvetica-Bold", textColor=ESUT_DARK))],
                        [Paragraph("Date Issued:", label_style),
                         Paragraph(datetime.now().strftime("%d %B, %Y"), value_style)],
                    ], colWidths=[4*cm, 8*cm])
                ]
            ], colWidths=[17*cm])
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[17*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 1, ESUT_GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(Spacer(1, 0.3*cm))
    story.append(summary_table)
    
    # ─── GRADING SCALE ────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("GRADING SCALE", ParagraphStyle("gs_title", fontSize=9, fontName="Helvetica-Bold", textColor=ESUT_DARK)))
    
    scale_data = [
        ["Score Range", "Grade", "Grade Point", "Remark"],
        ["70 – 100", "A", "5.0", "Excellent"],
        ["60 – 69", "B", "4.0", "Very Good"],
        ["50 – 59", "C", "3.0", "Good"],
        ["45 – 49", "D", "2.0", "Pass"],
        ["40 – 44", "E", "1.0", "Fail"],
        ["0 – 39", "F", "0.0", "Fail"],
    ]
    scale_table = Table(scale_data, colWidths=[3.5*cm, 2*cm, 3*cm, 3.5*cm])
    scale_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ALT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(scale_table)
    
    # ─── SIGNATURE BLOCK ──────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    sig_data = [[
        Table([
            [Paragraph("_________________________", ParagraphStyle("sig", alignment=TA_CENTER, fontSize=9))],
            [Paragraph("REGISTRAR", ParagraphStyle("sig_label", alignment=TA_CENTER, fontSize=8, fontName="Helvetica-Bold", textColor=ESUT_GREEN))],
            [Paragraph("Enugu State University of Science<br/>and Technology", ParagraphStyle("sig_sub", alignment=TA_CENTER, fontSize=7, textColor=MID_GRAY))],
        ], colWidths=[6*cm]),
        Table([
            [Paragraph("_________________________", ParagraphStyle("sig", alignment=TA_CENTER, fontSize=9))],
            [Paragraph("DEAN, STUDENT AFFAIRS", ParagraphStyle("sig_label", alignment=TA_CENTER, fontSize=8, fontName="Helvetica-Bold", textColor=ESUT_GREEN))],
            [Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", ParagraphStyle("sig_sub", alignment=TA_CENTER, fontSize=7, textColor=MID_GRAY))],
        ], colWidths=[6*cm]),
    ]]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    story.append(sig_table)
    
    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.3, color=ESUT_GOLD))
    story.append(Paragraph(
        f"<font size='7' color='#888888'>This transcript is an official document of ESUT. Any alteration renders it invalid. "
        f"Verify at: {qr_data} | Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}</font>",
        ParagraphStyle("footer", alignment=TA_CENTER, fontSize=7)
    ))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
