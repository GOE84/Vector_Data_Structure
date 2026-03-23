from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Algorithm Problem: Grade Calculation (If-Else)', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()
pdf.set_font('Arial', '', 12)
text = """
Problem Definition:
Given an array (or vector) of student scores (integers between 0 and 100), write a function to evaluate and return an array of their corresponding letter grades.
The grading criteria is as follows using if-else conditions:
- Score >= 80: 'A'
- Score >= 70 and < 80: 'B'
- Score >= 60 and < 70: 'C'
- Score >= 50 and < 60: 'D'
- Score < 50: 'F'

Concept and Theory:
This problem tests basic control flow operations, specifically 'if', 'else if', and 'else' conditional statements. The algorithm should iterate through each score in the input array, evaluate it against the conditions sequentially, and append the resulting grade to a new array.

Handling Edge Cases:
Ensure that invalid scores (e.g., negative numbers or scores > 100) are flagged or handled appropriately depending on the constraints.

Time and Space Complexity:
- Time Complexity: O(N), where N is the number of scores, as we must evaluate each score exactly once.
- Space Complexity: O(N), because we need to allocate a new array of the same size to store the resulting grades.
"""
pdf.multi_cell(0, 10, text)
import os
os.makedirs('pdfs', exist_ok=True)
pdf.output('pdfs/grading_problem.pdf')
print("pdfs/grading_problem.pdf created successfully!")
