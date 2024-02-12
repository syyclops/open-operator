from unittest.mock import Mock
import unittest
from openoperator.core.cobie.cobie import COBie 
from openpyxl import Workbook
from io import BytesIO

class TestCOBie(unittest.TestCase):
    def setUp(self) -> None:
        self.facility_mock = Mock()
        self.embeddings_mock = Mock()
        self.cobie = COBie(facility=self.facility_mock, embeddings=self.embeddings_mock)
    
    def create_cobie_spreadsheet(self, modifications=None):
        """
        Create a basic COBie spreadsheet and apply modifications if provided.
        Modifications should be a dict with sheet names as keys and lists of rows as values.
        """
        wb = Workbook()
        sheets_data = {
            "Facility": [
                ["Name"],
                ["Test Facility"]
            ],
            "Floor": [
                ["Name"],
                ["Test Floor"],
                ["Test Floor 2"],
            ],
            "Space": [
                ["Name", "CreatedBy", "CreatedOn", "Category", "FloorName"],
                ["Test Space", "Test User", "2022-01-01", "Space", "Test Floor"],
                ["Test Space 2", "Test User", "2022-01-01", "Space", "Test Floor 2"]
            ],
            "Type": [
                ["Name", "CreatedBy", "CreatedOn", "Category"],
                ["Test Door", "Test User", "2022-01-01", "23-30 10: Doors"],
            ],
            "Component": [
                ["Name", "CreatedBy", "CreatedOn", "TypeName", "Space"],
                ["Test Component", "Test User", "2022-01-01", "Test Door", "Test Space"],
                ["Test Component 2", "Test User", "2022-01-01", "Test Door", "Test Space 2"]
            ],
            "System": [
                ["Name"],
                ["Test System"]
            ],
            "Attribute": [
                ["Name", "CreatedBy", "CreatedOn", "Category", "ComponentName"],
                ["Test Attribute", "Test User", "2022-01-01", "Attribute", "Test Component"],
                ["Test Attribute 2", "Test User", "2022-01-01", "Attribute", "Test Component 2"]
            ],
        }

        for sheet, rows in sheets_data.items():
            if sheet not in wb.sheetnames:
                wb.create_sheet(sheet)
            ws = wb[sheet]
            for row in rows:
                ws.append(row)

        # Apply modifications
        if modifications:
            for sheet, rows in modifications.items():
                ws = wb[sheet]
                for row in rows:
                    ws.append(row)

        file_content = BytesIO()
        wb.save(file_content)
        file_content.seek(0)
        return file_content.getvalue()

    def test_validate_spreadsheet_success(self):
        file_content = self.create_cobie_spreadsheet()
        errors_found, errors, _ = self.cobie.validate_spreadsheet(file_content)
        assert errors_found == False
        assert errors == {}

    def test_validate_spreadsheet_multiple_facility_records(self):
        """Test for multiple records in Facility sheet."""
        file_content = self.create_cobie_spreadsheet(modifications={
            "Facility": [["Name2", "Value2"]]
        })
        errors_found, errors, _ = self.cobie.validate_spreadsheet(file_content=file_content)
        assert errors_found == True
        assert "More than one record found in Facility sheet." in errors

    def test_validate_spreadsheet_empty_cells_in_column_A(self):
        """Test for empty or N/A cells in column A of any sheet."""
        modifications = {
            "Floor": [[None], # Adding an empty row to Floor
                      ['Floor 5']]  
        }
        file_content = self.create_cobie_spreadsheet(modifications=modifications)
        errors_found, errors, _ = self.cobie.validate_spreadsheet(file_content=file_content)
        assert errors_found == True
        assert "Empty or N/A cells found in column A of sheet." in errors

    def test_validate_spreadsheet_duplicate_names_in_column_A(self):
        """Test for duplicate names in column A of specific sheets."""
        modifications = {
            "Component": [["Test Component 2", "Test User", "2022-01-01", "Test Door", "Test Space 2"]]  # Duplicate Component1
        }
        file_content = self.create_cobie_spreadsheet(modifications=modifications)
        errors_found, errors, _ = self.cobie.validate_spreadsheet(file_content=file_content)
        assert errors_found == True
        assert "Duplicate names found in column A of sheet." in errors
   

if __name__ == "__main__":
    unittest.main()