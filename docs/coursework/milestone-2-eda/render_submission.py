"""Execute the submitted notebook and export a self-contained, reading-focused HTML."""
from pathlib import Path
import re
import html
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
P=Path(__file__).resolve().parent
nb=nbformat.read(P/'ProjectEDA_Team4.ipynb',as_version=4)
NotebookClient(nb,timeout=1800,resources={'metadata':{'path':str(P)}}).execute()
nbformat.write(nb,P/'ProjectEDA_Team4.ipynb')
exporter=HTMLExporter(exclude_input=True,exclude_input_prompt=True,exclude_output_prompt=True)
body,_=exporter.from_notebook_node(nb)
style='''<style id="submission-style">
:root{--jp-layout-color0:#fff;--jp-content-font-color0:#20334a;--jp-content-font-color1:#26394d;--jp-content-font-family:Arial,Helvetica,sans-serif;--jp-content-font-size1:16px;}
body{background:#fff!important;color:#26394d!important;}
main{max-width:1250px;margin:auto;}
.jp-Notebook{padding:35px 32px 65px!important;max-width:1250px;margin:auto!important;background:white!important;}
.jp-Cell{padding:0!important;margin:0 0 14px!important;}
.jp-MarkdownOutput{font-family:Arial,Helvetica,sans-serif!important;font-size:16px;line-height:1.65;color:#26394d!important;overflow-wrap:break-word;}
.jp-MarkdownOutput h1{font-size:38px!important;line-height:1.16;font-weight:750!important;letter-spacing:-1px;color:#20334a;margin:10px 0 15px!important;}
.jp-MarkdownOutput h2{font-size:25px!important;line-height:1.25;color:#20334a;border-top:1px solid #dce4e9;padding-top:24px;margin:32px 0 15px!important;}
.jp-MarkdownOutput h3{font-size:19px!important;color:#187d8d;margin:25px 0 12px!important;}
.jp-MarkdownOutput p{margin:0 0 16px!important;}
.jp-MarkdownOutput blockquote{border-left:4px solid #187d8d;background:#f3f8f9;padding:18px 22px;margin:25px 0!important;color:#20334a;}
.jp-MarkdownOutput blockquote p{margin:0!important;}
.jp-MarkdownOutput a,.jp-RenderedHTMLCommon a{color:#126e81;text-decoration:underline;text-underline-offset:2px;}
.jp-InputPrompt,.jp-OutputPrompt{display:none!important;}
.jp-OutputArea-output{width:100%;overflow-x:auto;font-family:Arial,Helvetica,sans-serif!important;}
.jp-OutputArea-output img{display:block;max-width:100%;height:auto;margin:18px auto 8px;}
table{width:100%;border-collapse:collapse!important;font-size:13px!important;line-height:1.45;margin:15px 0 22px!important;}
th{background:#edf3f5!important;color:#20334a!important;font-weight:700!important;text-align:left!important;padding:10px 9px!important;border-bottom:2px solid #bfcfd6!important;}
td{padding:9px!important;text-align:left!important;border-bottom:1px solid #e4eaee!important;vertical-align:top!important;}
tr:nth-child(even){background:#f8fafb!important;}
.table-caption{font-size:13px;color:#647484;font-style:italic;margin:10px 0 0!important;}
details{border:1px solid #d7e0e5;border-radius:3px;padding:12px 16px;margin:18px 0;overflow-x:auto;background:#fafcfd;}
summary{font-weight:600;color:#20334a;cursor:pointer;font-size:14px;}
@media(max-width:760px){.jp-Notebook{padding:20px 14px!important}.jp-MarkdownOutput h1{font-size:30px!important}.jp-MarkdownOutput{font-size:15px}table{font-size:12px!important}}
@media print{.jp-Notebook{padding:0!important}details{display:block}.jp-OutputArea-output img{break-inside:avoid}h2,h3{break-after:avoid}}
</style>'''
body=re.sub(r'<title>.*?</title>', '<title>Public investment and nearby business engagement | Team 4</title>', body, count=1)
alts=iter([
    'Five funded projects: location, project type, reported cost, opening date, and pre/post observation windows.',
    'Business coverage and matched sample size for each project. Water Works has only two eligible matched pairs.',
    'VADER sentiment labels by star rating and review length by project. Positive sentiment is common even in low-star reviews.',
    'Matched changes in reviews, check-ins, tips, stars, and VADER across five projects. Engagement and sentiment do not consistently move together.',
    'Review growth contrasts across within-city neighborhood income groups, with sample sizes and sparse cells flagged.',
    'Review growth contrasts across 250, 500, and 1000 meter buffers reveal sensitivity to geography.',
    'Unmatched changes in VADER and whole-review stars across six embedding categories and five projects.',
    'Sun Link corridor review composition changes. Engagement indicators have different relative growth rates.'
])
def describe_image(match):
    tag=match.group(0)
    if 'data:image/png;base64' not in tag:
        return tag
    alt=html.escape(next(alts), quote=True)
    return re.sub(r'alt="[^"]*"', 'alt="'+alt+'"', tag) if 'alt="' in tag else tag.replace('<img ', '<img alt="'+alt+'" ', 1)
body=re.sub(r'<img\b[^>]*>', describe_image, body)
body=body.replace('</head>',style+'\n</head>')
(P/'ProjectEDA_Team4.html').write_text(body)
print('Executed',sum(c.cell_type=='code' for c in nb.cells),'code cells; exported HTML with embedded figures.')
