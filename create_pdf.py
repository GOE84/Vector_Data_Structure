from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Vector Problem: Reverse a Vector', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()
pdf.set_font('Arial', '', 12)
text = """
Problem Definition:
Given a vector (dynamic array) of integers, write a function or algorithm to reverse the order of its elements in-place.

Concept and Theory:
Reversing an array involves swapping the first element with the last element, the second element with the second-to-last element, and so on until you reach the middle of the array. This is an efficient O(N) operation where N is the total number of elements in the vector.

Two-Pointer Approach:
The optimal way to reverse a vector in-place is to use two pointers (or indices):
1. 'start' pointing to the 0-th index.
2. 'end' pointing to the (N-1)-th index.
While start < end, swap vector[start] and vector[end], then increment start and decrement end.

Time and Space Complexity:
- Time Complexity: O(N), as we iterate through half the array.
- Space Complexity: O(1), since we perform the swap in-place without using extra memory.
"""
pdf.multi_cell(0, 10, text)
pdf.output('vector_q3_reverse.pdf')
print("PDF created successfully!")
