import os
from fpdf import FPDF
from rag_service import rag_service

problems = [
    {
        "id": "q5",
        "title": "Two Sum",
        "description": "Given an array of integers 'nums' and an integer 'target', return indices of the two numbers such that they add up to 'target'.",
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\nExactly one valid answer exists.",
        "difficulty": "Easy",
        "expected_complexity": "O(N) using Hash Map, or O(N log N) with sorting and two pointers",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "This problem teaches how to trade space for time complexity using a Hash Map (or dictionary). You iterate through the array, storing the required complement (target - current element) in the Hash Map. For each element, check if it exists in the Hash Map to find the match instantly."
    },
    {
        "id": "q6",
        "title": "Maximum Subarray",
        "description": "Given an integer array 'nums', find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
        "constraints": "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
        "difficulty": "Medium",
        "expected_complexity": "O(N) time and O(1) space using Kadane's Algorithm",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "Kadane's Algorithm allows solving this in linear time. The idea is to maintain a 'current_sum' and a 'max_sum'. While iterating, 'current_sum' either adds the current element to the existing subarray or starts a new subarray at the current element (whichever is larger)."
    },
    {
        "id": "q7",
        "title": "Palindrome Vector Check",
        "description": "Given an array of characters (or integers), determine if it reads the same forwards and backwards.",
        "constraints": "1 <= vector.length <= 10^5",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(1) space",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "Use the Two-Pointer technique. Place one pointer at the start (index 0) and one at the end (index N-1). Move them towards the center, checking if elements match at each step. If a mismatch is found, it's not a palindrome."
    },
    {
        "id": "q8",
        "title": "Remove Duplicates from Sorted Vector",
        "description": "Given a sorted array of integers, remove the duplicates in-place such that each unique element appears only once. The relative order of the elements should be kept the same.",
        "constraints": "1 <= nums.length <= 3 * 10^4\nArray is sorted in non-decreasing order.",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(1) space",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "Since the array is sorted, duplicates will be adjacent. Use a slow pointer and a fast pointer. The fast pointer traverses the array looking for new unique elements, and the slow pointer writes them down, overwriting adjacent duplicates."
    },
    {
        "id": "q9",
        "title": "Missing Number",
        "description": "Given an array containing n distinct numbers in the range [0, n], return the only number in the range that is missing from the array.",
        "constraints": "n == nums.length\n1 <= n <= 10^4\n0 <= nums[i] <= n",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(1) space",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "The sum of the first N integers is given by the formula (N * (N + 1)) / 2. To find the missing number, simply calculate the expected sum and subtract the sum of all elements currently present in the array."
    },
    {
        "id": "q10",
        "title": "Move Zeroes",
        "description": "Given an integer array 'nums', move all 0's to the end of it while maintaining the relative order of the non-zero elements. Must be done in-place.",
        "constraints": "1 <= nums.length <= 10^4\n-2^31 <= nums[i] <= 2^31 - 1",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(1) space",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "Use a two-pointer approach similar to partition in Quicksort. Keep a pointer that tracks the position where the next non-zero element should be placed. Traverse the array and whenever a non-zero element is found, swap it to the tracker position."
    },
    {
        "id": "q11",
        "title": "Best Time to Buy and Sell Stock",
        "description": "You are given an array 'prices' where prices[i] is the price of a given stock on the i-th day. You want to maximize your profit by choosing a single day to buy and a different day in the future to sell. Return the maximum profit.",
        "constraints": "1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(1) space",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "Track the minimum price seen so far as you iterate through the array. For each price, calculate the potential profit if sold on that day (current price - min price). Update the global maximum profit."
    },
    {
        "id": "q12",
        "title": "Product of Array Except Self",
        "description": "Given an integer array 'nums', return an array 'answer' such that answer[i] is equal to the product of all the elements of nums except nums[i]. The product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer. You must write an algorithm that runs in O(N) time and without using the division operation.",
        "constraints": "2 <= nums.length <= 10^5\n-30 <= nums[i] <= 30",
        "difficulty": "Medium",
        "expected_complexity": "O(N) time and O(1) auxiliary space (excluding output array)",
        "time_limit": 1000,
        "memory_limit": 256,
        "theory": "Use two passes. In the first pass (left-to-right), calculate the prefix product for each element. In the second pass (right-to-left), calculate the suffix product and multiply it immediately with the prefix product to form the final answer."
    },
    {
        "id": "q13",
        "title": "Contains Duplicate",
        "description": "Given an integer array 'nums', return true if any value appears at least twice in the array, and return false if every element is distinct.",
        "constraints": "1 <= nums.length <= 10^5\n-10^9 <= nums[i] <= 10^9",
        "difficulty": "Easy",
        "expected_complexity": "O(N) time and O(N) space using HashSet",
        "time_limit": 1000,
        "memory_limit": 128,
        "theory": "While sorting the array takes O(N log N) time, utilizing a Hash Set provides an optimal O(N) time constraint. Iterate the array and attempt to add elements to the set. If an element is already in the set, a duplicate exists."
    },
    {
        "id": "q14",
        "title": "Merge Intervals",
        "description": "Given an array of 'intervals' where intervals[i] = [start_i, end_i], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
        "constraints": "1 <= intervals.length <= 10^4\nintervals[i].length == 2\n0 <= start_i <= end_i <= 10^4",
        "difficulty": "Medium",
        "expected_complexity": "O(N log N) time and O(N) space",
        "time_limit": 2000,
        "memory_limit": 256,
        "theory": "First, sort the intervals in ascending order based on their starting points. Create a list to hold the merged intervals. Iterate through sorted intervals; if the current interval overlaps with the last added one, update the end of the last interval. Otherwise, add the current one to the list."
    }
]

class ProblemPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Algorithm Problem Documentation', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

import os
os.makedirs('pdfs', exist_ok=True)

def generate_and_ingest_problems(problems_list):
    for p in problems_list:
        pdf_filename = f"pdfs/problem_{p['id']}.pdf"
        pdf = ProblemPDF()
        pdf.add_page()
        pdf.set_font('helvetica', '', 12)
        
        text = f"Title: {p['title']}\n"
        text += f"ID: {p['id']}\n"
        text += f"Difficulty: {p['difficulty']}\n\n"
        text += f"Problem Definition:\n{p['description']}\n\n"
        text += f"Constraints:\n{p['constraints']}\n\n"
        text += f"Expected Complexity:\n{p['expected_complexity']}\n\n"
        text += f"Theory and Solution Concept:\n{p['theory']}\n"
        
        pdf.multi_cell(0, 10, text)
        pdf.output(pdf_filename)
        print(f"[{p['id']}] PDF generated: {pdf_filename}")
        
        # Ingest directly to ChromaDB
        rag_service.ingest_pdf(pdf_filename)
        print(f"[{p['id']}] PDF ingested to Vector DB.")

if __name__ == "__main__":
    generate_and_ingest_problems(problems)
    print("All 10 problems generated and ingested!")
