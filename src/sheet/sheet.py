import gspread

# spreadsheet - complete document
# worksheet - page in the document

class Spreadsheet:
    def __init__(self, connection_string: dict, spreadsheet_id: str):
        self.gc = gspread.service_account_from_dict(connection_string)
        self.spreadsheet = self.gc.open_by_key(spreadsheet_id)

    def get_sheets_list(self):
        return [ws.title for ws in self.spreadsheet.worksheets()]

    def _open_worksheet(self, worksheet_name : str):
        return self.spreadsheet.worksheet(worksheet_name)

    def read_column_content(self, worksheet_name:str, column_number:int) -> list:
        worksheet = self._open_worksheet(worksheet_name)
        values = worksheet.col_values(column_number)
        return values[1:]
    