table_association.py pulls docs + OCR + labels for a dataset/labelset
and saves a list of custom objects (CellLabelAssociation) that stores 
the relationships (cells, rows, columns) between labels on a tables
in a document per page.


NOTE: in order to pull xlsx from Indico you need to make the following
modification to the indico client serialization (indico/http/serialization.py: text_deserialization):
def text_deserialization(content, charset="utf-8"):
    try:
        return content.decode(charset)
    except Exception:
        raw_bytes(content)