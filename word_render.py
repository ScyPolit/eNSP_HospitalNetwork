from pathlib import Path
import sys,json,time
import win32com.client
import pymupdf
ROOT=Path(__file__).parent
def render(src,out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    word=win32com.client.DispatchEx('Word.Application');word.Visible=False;word.DisplayAlerts=0
    try:
        doc=word.Documents.Open(str(src.resolve()),ReadOnly=True,AddToRecentFiles=False)
        doc.Repaginate();pages=doc.ComputeStatistics(2)
        pdf=out/(src.stem+'.pdf');doc.ExportAsFixedFormat(str(pdf),17)
        positions=[]
        if src.name=='report-template.docx':
            for i in range(1,doc.Paragraphs.Count+1):
                p=doc.Paragraphs(i);positions.append(dict(i=i,page=p.Range.Information(3),text=p.Range.Text[:100]))
            (out/'template-positions.json').write_text(json.dumps(positions,ensure_ascii=False,indent=2),encoding='utf-8')
        doc.Close(False)
    finally:
        try:word.Quit()
        except Exception:pass
    pdfdoc=pymupdf.open(pdf)
    for i,page in enumerate(pdfdoc):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(out/f'page-{i+1}.png')
    print(json.dumps(dict(pdf=str(pdf),pages=len(pdfdoc)),ensure_ascii=False))
if __name__=='__main__':render(Path(sys.argv[1]),Path(sys.argv[2]))
