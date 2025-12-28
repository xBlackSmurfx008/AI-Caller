"""Export analytics functionality"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import csv
import io
from io import BytesIO
from datetime import datetime

from src.database.database import get_db
from src.api.schemas.analytics import ExportRequest
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from . import overview, call_volume

logger = get_logger(__name__)
router = APIRouter()


@router.post("/export")
@handle_service_errors_sync
def export_analytics(
    request: ExportRequest,
    db: Session = Depends(get_db),
):
    """Export analytics data as CSV or PDF"""
    if request.format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers based on report type
        if request.report_type == "overview":
            writer.writerow(["Metric", "Value"])
            metrics = overview.get_overview(request.from_date, request.to_date, request.business_id, db)
            writer.writerow(["Total Calls", metrics.total_calls])
            writer.writerow(["Active Calls", metrics.active_calls])
            writer.writerow(["Completed Calls", metrics.completed_calls])
            writer.writerow(["Failed Calls", metrics.failed_calls])
            writer.writerow(["Escalated Calls", metrics.escalated_calls])
            writer.writerow(["Average QA Score", metrics.average_qa_score])
            writer.writerow(["Average Call Duration", metrics.average_call_duration])
            writer.writerow(["Escalation Rate", metrics.escalation_rate])
        elif request.report_type == "calls":
            writer.writerow(["Period", "Total Calls", "Inbound", "Outbound", "Completed", "Escalated"])
            if request.from_date and request.to_date:
                volume_data = call_volume.get_call_volume(
                    request.from_date,
                    request.to_date,
                    "day",
                    request.business_id,
                    None,
                    db
                )
                for data in volume_data:
                    writer.writerow([
                        data.period,
                        data.total_calls,
                        data.inbound_calls,
                        data.outbound_calls,
                        data.completed_calls,
                        data.escalated_calls,
                    ])
        # Add other report types as needed
        
        output.seek(0)
        csv_content = output.getvalue()
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="analytics-{request.report_type}-{datetime.utcnow().date()}.csv"'
            }
        )
    else:
        # PDF export using reportlab
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(f"Analytics Report - {request.report_type.title()}", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Date range
            date_text = f"Period: {request.from_date or 'All time'} to {request.to_date or 'Now'}"
            elements.append(Paragraph(date_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Generate report data based on type
            if request.report_type == "overview":
                metrics = overview.get_overview(request.from_date, request.to_date, request.business_id, db)
                
                data = [
                    ['Metric', 'Value'],
                    ['Total Calls', str(metrics.total_calls)],
                    ['Active Calls', str(metrics.active_calls)],
                    ['Completed Calls', str(metrics.completed_calls)],
                    ['Failed Calls', str(metrics.failed_calls)],
                    ['Escalated Calls', str(metrics.escalated_calls)],
                    ['Average QA Score', f"{metrics.average_qa_score:.2f}"],
                    ['Average Call Duration', f"{metrics.average_call_duration:.2f}s"],
                    ['Escalation Rate', f"{metrics.escalation_rate:.2f}%"],
                ]
                
                table = Table(data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                
            elif request.report_type == "calls":
                if request.from_date and request.to_date:
                    volume_data = call_volume.get_call_volume(
                        request.from_date,
                        request.to_date,
                        "day",
                        request.business_id,
                        None,
                        current_user,
                        db
                    )
                    
                    data = [['Period', 'Total', 'Inbound', 'Outbound', 'Completed', 'Escalated']]
                    for v in volume_data:
                        data.append([
                            v.period[:10] if len(v.period) > 10 else v.period,
                            str(v.total_calls),
                            str(v.inbound_calls),
                            str(v.outbound_calls),
                            str(v.completed_calls),
                            str(v.escalated_calls),
                        ])
                    
                    table = Table(data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ]))
                    elements.append(table)
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            
            from fastapi.responses import Response
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="analytics-{request.report_type}-{datetime.utcnow().date()}.pdf"'
                }
            )
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF export requires 'reportlab' library. Install with: pip install reportlab"
            )
        except Exception as e:
            logger.error("pdf_export_failed", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {str(e)}"
            )

