"""PDF report generation for investigations."""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


class PDFReportService:
    def generate_investigation_report(self, report_data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1e3a5f"), alignment=TA_CENTER)
        heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#0891b2"), spaceAfter=12)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, alignment=TA_JUSTIFY, spaceAfter=8)

        story = []

        # Header
        story.append(Paragraph("SurakshAI", title_style))
        story.append(Paragraph("Investigation Report", styles["Heading2"]))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M IST')}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # FIR Details
        fir = report_data.get("fir", {})
        story.append(Paragraph("FIR Details", heading_style))
        fir_table_data = [
            ["FIR Number", fir.get("fir_number", "N/A")],
            ["Crime Type", fir.get("crime_type", "N/A")],
            ["Status", fir.get("status", "N/A")],
            ["Priority", fir.get("priority", "N/A")],
            ["Incident Date", str(fir.get("incident_date", "N/A"))],
            ["District", fir.get("district", "N/A")],
        ]
        t = Table(fir_table_data, colWidths=[2 * inch, 4 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # Executive Summary
        ai_content = report_data.get("ai_content", {})
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(ai_content.get("executive_summary", fir.get("summary", fir.get("description", "No summary available."))), body_style))
        story.append(Spacer(1, 10))

        # Key Findings
        findings = ai_content.get("findings", [])
        if findings:
            story.append(Paragraph("Key Findings", heading_style))
            for i, finding in enumerate(findings, 1):
                story.append(Paragraph(f"{i}. {finding}", body_style))

        # Evidence
        evidence = report_data.get("evidence", [])
        if evidence:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Evidence", heading_style))
            ev_data = [["Type", "Description", "Verified"]]
            for ev in evidence[:20]:
                ev_data.append([ev.get("evidence_type", ""), ev.get("description", "")[:80], "Yes" if ev.get("is_verified") else "No"])
            ev_table = Table(ev_data, colWidths=[1.2 * inch, 3.5 * inch, 0.8 * inch])
            ev_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891b2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(ev_table)

        # Timeline
        timeline = report_data.get("timeline", [])
        if timeline:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Investigation Timeline", heading_style))
            for event in timeline[:15]:
                story.append(Paragraph(f"- {event.get('date', '')}: {event.get('event', '')}", body_style))

        # Recommendations
        recommendations = ai_content.get("recommendations", [])
        if recommendations:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Recommendations", heading_style))
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", body_style))

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("-- Confidential -- Karnataka Police Intelligence System --", ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()


pdf_service = PDFReportService()
