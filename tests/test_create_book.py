#!/usr/bin/env python3
"""
XOffencer Book Store - Create Book API Test Script
Tests various scenarios for creating books via the API
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/books/"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class BookAPITester:
    def __init__(self, jwt_token: str):
        self.jwt_token = jwt_token
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        self.test_results = []

    def log_test(self, name: str, status: str, message: str = "", response_code: int = None):
        """Log test results"""
        self.test_results.append({
            "name": name,
            "status": status,
            "message": message,
            "response_code": response_code
        })
        
        if status == "PASS":
            print(f"{Colors.GREEN}✓ PASS{Colors.END}: {name}")
        elif status == "FAIL":
            print(f"{Colors.RED}✗ FAIL{Colors.END}: {name}")
        else:
            print(f"{Colors.YELLOW}⚠ {status}{Colors.END}: {name}")
        
        if message:
            print(f"  → {message}")
        if response_code:
            print(f"  → Response Code: {response_code}")

    def test_minimal_book(self) -> Optional[Dict[str, Any]]:
        """Test 1: Create minimal book with required fields only"""
        payload = {
            "title": "Test: Introduction to Python",
            "isbn": f"978TEST{1000000 + hash('test1') % 1000000}",
            "pages": 320,
            "description": "A comprehensive guide to Python programming",
            "publication_date": "2024-01-15"
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 201:
                self.log_test(
                    "Minimal Book Creation",
                    "PASS",
                    f"Created book with ID: {response.json().get('id')}",
                    response.status_code
                )
                return response.json()
            else:
                self.log_test(
                    "Minimal Book Creation",
                    "FAIL",
                    response.json().get('errors', response.text),
                    response.status_code
                )
                return None
        except Exception as e:
            self.log_test("Minimal Book Creation", "ERROR", str(e))
            return None

    def test_book_with_single_author(self) -> Optional[Dict[str, Any]]:
        """Test 2: Create book with single author"""
        payload = {
            "title": "Test: Data Science Fundamentals",
            "isbn": f"978TEST{2000000 + hash('test2') % 1000000}",
            "pages": 450,
            "description": "Learn the foundations of data science",
            "publication_date": "2024-03-20",
            "authors": [1],  # Author ID 1
            "publication": 1,
            "categories": [1]
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 201:
                self.log_test(
                    "Book with Single Author",
                    "PASS",
                    f"Created book with author",
                    response.status_code
                )
                return response.json()
            else:
                self.log_test(
                    "Book with Single Author",
                    "FAIL",
                    response.json().get('errors', response.text),
                    response.status_code
                )
                return None
        except Exception as e:
            self.log_test("Book with Single Author", "ERROR", str(e))
            return None

    def test_book_with_multiple_authors(self) -> Optional[Dict[str, Any]]:
        """Test 3: Create book with multiple authors"""
        payload = {
            "title": "Test: Advanced JavaScript Patterns",
            "isbn": f"978TEST{3000000 + hash('test3') % 1000000}",
            "pages": 256,
            "description": "Master JavaScript design patterns",
            "publication_date": "2023-06-10",
            "authors": [1, 2],  # Multiple author IDs
            "publication": 1,
            "categories": [2, 5]
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 201:
                self.log_test(
                    "Book with Multiple Authors",
                    "PASS",
                    f"Created book with {len(payload['authors'])} authors",
                    response.status_code
                )
                return response.json()
            else:
                self.log_test(
                    "Book with Multiple Authors",
                    "FAIL",
                    response.json().get('errors', response.text),
                    response.status_code
                )
                return None
        except Exception as e:
            self.log_test("Book with Multiple Authors", "ERROR", str(e))
            return None

    def test_book_with_chapters(self) -> Optional[Dict[str, Any]]:
        """Test 4: Create edited book with chapters"""
        payload = {
            "title": "Test: System Design Interview",
            "isbn": f"978TEST{4000000 + hash('test4') % 1000000}",
            "pages": 512,
            "description": "Complete guide to system design interviews",
            "publication_date": "2023-09-12",
            "editors": [4, 5],  # Editor IDs
            "publication": 2,
            "categories": [3, 6],
            "chapters": '[{"title": "Scalability Fundamentals", "order": 0, "contributors": [4, 6]}, {"title": "Database Patterns", "order": 1, "contributors": [5]}]'
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 201:
                self.log_test(
                    "Book with Chapters",
                    "PASS",
                    f"Created edited book with chapters",
                    response.status_code
                )
                return response.json()
            else:
                self.log_test(
                    "Book with Chapters",
                    "FAIL",
                    response.json().get('errors', response.text),
                    response.status_code
                )
                return None
        except Exception as e:
            self.log_test("Book with Chapters", "ERROR", str(e))
            return None

    def test_missing_required_field(self) -> bool:
        """Test 5: Validation - Missing required field"""
        payload = {
            "title": "Test: Missing ISBN",
            "pages": 250,
            "description": "This should fail",
            "publication_date": "2024-03-15"
            # Missing 'isbn'
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 400:
                self.log_test(
                    "Validation: Missing Required Field",
                    "PASS",
                    "Correctly rejected missing ISBN",
                    response.status_code
                )
                return True
            else:
                self.log_test(
                    "Validation: Missing Required Field",
                    "FAIL",
                    f"Expected 400, got {response.status_code}",
                    response.status_code
                )
                return False
        except Exception as e:
            self.log_test("Validation: Missing Required Field", "ERROR", str(e))
            return False

    def test_duplicate_isbn(self) -> bool:
        """Test 6: Validation - Duplicate ISBN"""
        # First, create a book
        payload1 = {
            "title": "Test: Original Book",
            "isbn": "978DUPLICATE123456",
            "pages": 300,
            "description": "Original",
            "publication_date": "2024-03-15"
        }
        
        try:
            response1 = requests.post(API_ENDPOINT, json=payload1, headers=self.headers)
            if response1.status_code != 201:
                self.log_test("Validation: Duplicate ISBN", "SKIP", "Could not create first book")
                return None
            
            # Now try to create another book with same ISBN
            payload2 = {
                "title": "Test: Different Title",
                "isbn": "978DUPLICATE123456",
                "pages": 350,
                "description": "Duplicate ISBN",
                "publication_date": "2024-03-20"
            }
            
            response2 = requests.post(API_ENDPOINT, json=payload2, headers=self.headers)
            if response2.status_code == 400:
                self.log_test(
                    "Validation: Duplicate ISBN",
                    "PASS",
                    "Correctly rejected duplicate ISBN",
                    response2.status_code
                )
                return True
            else:
                self.log_test(
                    "Validation: Duplicate ISBN",
                    "FAIL",
                    f"Expected 400, got {response2.status_code}",
                    response2.status_code
                )
                return False
        except Exception as e:
            self.log_test("Validation: Duplicate ISBN", "ERROR", str(e))
            return False

    def test_invalid_author_id(self) -> bool:
        """Test 7: Validation - Invalid author ID"""
        payload = {
            "title": "Test: Invalid Author",
            "isbn": f"978TEST{7000000 + hash('test7') % 1000000}",
            "pages": 300,
            "description": "With non-existent author",
            "publication_date": "2024-03-25",
            "authors": [99999]  # Non-existent author
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 400:
                self.log_test(
                    "Validation: Invalid Author ID",
                    "PASS",
                    "Correctly rejected invalid author ID",
                    response.status_code
                )
                return True
            else:
                self.log_test(
                    "Validation: Invalid Author ID",
                    "FAIL",
                    f"Expected 400, got {response.status_code}",
                    response.status_code
                )
                return False
        except Exception as e:
            self.log_test("Validation: Invalid Author ID", "ERROR", str(e))
            return False

    def test_invalid_date_format(self) -> bool:
        """Test 8: Validation - Invalid date format"""
        payload = {
            "title": "Test: Invalid Date",
            "isbn": f"978TEST{8000000 + hash('test8') % 1000000}",
            "pages": 300,
            "description": "With invalid date",
            "publication_date": "01-15-2024"  # Invalid format (should be YYYY-MM-DD)
        }
        
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
            if response.status_code == 400:
                self.log_test(
                    "Validation: Invalid Date Format",
                    "PASS",
                    "Correctly rejected invalid date format",
                    response.status_code
                )
                return True
            else:
                self.log_test(
                    "Validation: Invalid Date Format",
                    "FAIL",
                    f"Expected 400, got {response.status_code}",
                    response.status_code
                )
                return False
        except Exception as e:
            self.log_test("Validation: Invalid Date Format", "ERROR", str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BLUE}{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}{Colors.END}")
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"{Colors.YELLOW}Errors: {errors}{Colors.END}")
        print(f"Skipped: {skipped}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

    def run_all_tests(self):
        """Run all tests"""
        print(f"{Colors.BLUE}Starting Book API Tests...{Colors.END}\n")
        
        # Functionality tests
        print(f"{Colors.YELLOW}--- Functionality Tests ---{Colors.END}")
        self.test_minimal_book()
        self.test_book_with_single_author()
        self.test_book_with_multiple_authors()
        self.test_book_with_chapters()
        
        # Validation tests
        print(f"\n{Colors.YELLOW}--- Validation Tests ---{Colors.END}")
        self.test_missing_required_field()
        self.test_duplicate_isbn()
        self.test_invalid_author_id()
        self.test_invalid_date_format()
        
        self.print_summary()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python test_create_book.py <jwt_token> [base_url]")
        print("\nExample:")
        print("  python test_create_book.py 'eyJ0eXAiOiJKV1QiLCJhbGc...'")
        print("  python test_create_book.py 'eyJ0eXAiOiJKV1QiLCJhbGc...' http://localhost:8000")
        sys.exit(1)
    
    jwt_token = sys.argv[1]
    
    if len(sys.argv) >= 3:
        BaseURL = sys.argv[2]
    
    print(f"{Colors.BLUE}XOffencer Book Store - API Test Suite{Colors.END}")
    print(f"Endpoint: {API_ENDPOINT}\n")
    
    tester = BookAPITester(jwt_token)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
