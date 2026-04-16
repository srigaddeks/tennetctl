"""
Templates for exporting reports to PDF and DOCX.
"""

def get_pdf_watermark_html(b64_src: str) -> tuple[str, str]:
    """Returns (watermark_style, watermark_div) strings for xhtml2pdf"""
    watermark_style = """
        @frame watermark_static {
            -pdf-frame-content: watermark_content;
            left: 0pt; top: 0pt; width: 595pt; height: 842pt;
        }
    """
    watermark_div = f"""
        <div id="watermark_content" style="text-align: center; padding-top: 300pt;">
            <img src="{b64_src}" width="550" />
        </div>
    """
    return watermark_style, watermark_div

def get_pdf_html_template(title: str, html_content: str, watermark_style: str = "", watermark_div: str = "") -> str:
    """Returns the full HTML string for xhtml2pdf rendering"""
    return f"""
    <html>
    <head>
        <style>
            @page {{ 
                size: a4; 
                margin: 2cm; 
                {watermark_style}
            }}
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: #333; }}
            h1 {{ color: #1e3a5f; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            h2 {{ color: #2c5282; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ border: 1px solid #e2e8f0; padding: 8px; text-align: left; }}
            th {{ background-color: #f8fafc; font-weight: bold; }}
            pre {{ background-color: #f7fafc; padding: 10px; border-radius: 4px; font-family: monospace; }}
        </style>
    </head>
    <body>
        {watermark_div}
        <h1>{title}</h1>
        {html_content}
    </body>
    </html>
    """

def get_docx_watermark_anchor_xml(extent_cx: int, extent_cy: int, docpr_id: int, docpr_name: str) -> str:
    """Returns the XML string for making a picture float behind text in python-docx"""
    return f"""
    <wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
               distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0"
               behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">
        <wp:simplePos x="0" y="0"/>
        <wp:positionH relativeFrom="margin">
            <wp:align>center</wp:align>
        </wp:positionH>
        <wp:positionV relativeFrom="margin">
            <wp:align>center</wp:align>
        </wp:positionV>
        <wp:extent cx="{extent_cx}" cy="{extent_cy}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:wrapNone/>
        <wp:docPr id="{docpr_id}" name="{docpr_name}"/>
        <wp:cNvGraphicFramePr>
            <a:graphicFrameLocks noChangeAspect="1"/>
        </wp:cNvGraphicFramePr>
    </wp:anchor>
    """
