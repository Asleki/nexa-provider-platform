import csv,io
class CSVSourceReader:
    media_types={"text/csv","application/csv"}
    def read(self,data:bytes):
        text=data.decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(text))
        if not reader.fieldnames: raise ValueError("CSV header is required")
        return [dict(row) for row in reader]
