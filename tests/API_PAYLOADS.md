# Book Store API - Create Book Payloads

## Endpoint
```
POST /api/books/
```

**Method**: POST  
**Authentication**: Required (Admin/Staff only)  
**Content-Type**: `application/json` or `multipart/form-data` (for images)  
**Permissions**: IsAdminUser

---

## Required Fields
- `title` (string): Book title (max 255 chars)
- `isbn` (string): ISBN code, must be unique (max 20 chars)
- `pages` (integer): Number of pages
- `description` (string, optional): Book description
- `publication_date` (string, YYYY-MM-DD): Publication date

## Optional Fields
- `publication` (integer): Publication ID (FK)
- `authors` (array of integers): Author IDs - Creates "authored" books
- `editors` (array of integers): Editor IDs - Creates "edited" books (only if no authors)
- `categories` (array of integers): Category IDs
- `chapters` (string): JSON stringified chapters (only with editors)

---

## Payload Examples

### 1. Minimal Book (JSON)
Simple book with required fields only:

```json
{
  "title": "Introduction to Python",
  "isbn": "9788934927285",
  "pages": 320,
  "description": "A comprehensive guide to Python programming",
  "publication_date": "2024-01-15"
}
```

---

### 2. Book with Authors (JSON)
Book with one or more authors:

```json
{
  "title": "Advanced JavaScript Patterns",
  "isbn": "9781491952023",
  "pages": 256,
  "description": "Master JavaScript design patterns and best practices",
  "publication_date": "2023-06-10",
  "authors": [1, 2, 3],
  "publication": 1,
  "categories": [5, 8]
}
```

**Note**: When `authors` is provided, the book is treated as an "authored" book. Editors and chapters are not allowed.

---

### 3. Book with One Author (JSON)

```json
{
  "title": "Data Science Fundamentals",
  "isbn": "9781491934495",
  "pages": 450,
  "description": "Learn the foundations of data science with Python",
  "publication_date": "2024-03-20",
  "authors": [5],
  "publication": 2,
  "categories": [10]
}
```

---

### 4. Edited Book with Chapters and Contributors (JSON)
Complex book with editors and chapters that have chapter contributors:

```json
{
  "title": "System Design Interview",
  "isbn": "9781491954981",
  "pages": 512,
  "description": "Complete guide to preparing for system design interviews",
  "publication_date": "2023-09-12",
  "editors": [7, 8],
  "publication": 3,
  "categories": [12, 15],
  "chapters": "[{\"title\": \"Scalability Fundamentals\", \"order\": 0, \"contributors\": [4, 6]}, {\"title\": \"Database Design Patterns\", \"order\": 1, \"contributors\": [9]}]"
}
```

**Important**: 
- `chapters` must be a JSON **stringified** format (escaped quotes)
- Only used when `editors` are provided (not with authors)
- Contributors are author IDs who contribute to specific chapters

---

### 5. Book with All Fields (JSON)

```json
{
  "title": "Microservices Architecture Deep Dive",
  "isbn": "9781491954987",
  "pages": 380,
  "description": "Learn to build, deploy, and manage microservices at scale with Kubernetes and Docker",
  "publication_date": "2024-05-22",
  "authors": [10],
  "publication": 4,
  "categories": [16, 18, 20],
  "chapters": "[{\"title\": \"Introduction to Microservices\", \"order\": 0, \"contributors\": [10]}, {\"title\": \"Containerization with Docker\", \"order\": 1, \"contributors\": [11, 12]}, {\"title\": \"Orchestration with Kubernetes\", \"order\": 2, \"contributors\": [13]}]"
}
```

---

### 6. Book with Multiple Authors and Categories (JSON)

```json
{
  "title": "Machine Learning for Production",
  "isbn": "9781491954994",
  "pages": 600,
  "description": "Building and deploying ML models in production environments",
  "publication_date": "2024-02-14",
  "authors": [15, 16, 17, 18],
  "publication": 5,
  "categories": [25, 26, 27]
}
```

---

## Chapters JSON Structure Reference

When using the `chapters` field, it must be a stringified JSON array:

```javascript
// Raw JavaScript object (for reference):
[
  {
    "title": "Chapter Title",
    "order": 0,
    "contributors": [authorId1, authorId2]
  },
  {
    "title": "Another Chapter",
    "order": 1,
    "contributors": [authorId3]
  }
]

// As stringified in API payload:
"chapters": "[{\"title\": \"Chapter Title\", \"order\": 0, \"contributors\": [1, 2]}, {\"title\": \"Another Chapter\", \"order\": 1, \"contributors\": [3]}]"
```

---

## Multipart Form Data (with Images)

For file uploads, use `multipart/form-data` instead of JSON:

```
POST /api/books/

Content-Type: multipart/form-data

Fields:
  title: "Python Cookbook Edition 3"
  isbn: "9781491946580"
  pages: 608
  description: "More than 150 recipes for solving...\""
  publication_date: "2024-01-30"
  publication: 6
  categories: [5, 8]
  authors: [20]
  image_count: 2
  image_0_title: "Book Cover"
  image_0_file: (binary file)
  image_1_title: "Back Cover"
  image_1_file: (binary file)
```

**Important**: 
- `image_count`: Number of images to upload
- Image files must be named: `image_{i}_file` (where i = 0, 1, 2, ...)
- Image titles must be named: `image_{i}_title`

---

## Complete cURL Examples

### Simple Book (JSON):
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Basics",
    "isbn": "9781234567890",
    "pages": 250,
    "description": "Learn Python from scratch",
    "publication_date": "2024-03-15"
  }'
```

### Book with Authors (JSON):
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Advanced Python",
    "isbn": "9780987654321",
    "pages": 450,
    "description": "Master Python programming",
    "publication_date": "2024-04-10",
    "authors": [1, 2],
    "publication": 1,
    "categories": [3, 5]
  }'
```

### Book with Images (Form Data):
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=Web Development Guide" \
  -F "isbn=9781111111111" \
  -F "pages=500" \
  -F "description=Complete web development guide" \
  -F "publication_date=2024-05-20" \
  -F "authors=3" \
  -F "publication=2" \
  -F "image_count=1" \
  -F "image_0_title=Book Cover" \
  -F "image_0_file=@/path/to/cover.jpg"
```

### Edited Book with Chapters (JSON):
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Architecture Patterns",
    "isbn": "9781222222222",
    "pages": 380,
    "description": "Learn modern software architecture",
    "publication_date": "2024-06-15",
    "editors": [4, 5],
    "publication": 3,
    "categories": [10],
    "chapters": "[{\"title\": \"Layered Architecture\", \"order\": 0, \"contributors\": [4]}, {\"title\": \"Microservices Pattern\", \"order\": 1, \"contributors\": [5]}]"
  }'
```

---

## API Response

### Success (201 Created):
```json
{
  "id": 42,
  "title": "Python Basics",
  "description": "Learn Python from scratch",
  "isbn": "9781234567890",
  "pages": 250,
  "publication_date": "2024-03-15",
  "publication": null,
  "categories": [],
  "images": [],
  "cover_image": null,
  "is_featured": false,
  "is_book_of_the_month": false,
  "is_book_of_the_year": false,
  "formats": [],
  "participants": [],
  "chapters": []
}
```

### Error (400 Bad Request):
```json
{
  "title": ["This field may not be blank."],
  "isbn": ["This field must be unique."],
  "pages": ["A valid integer is required."]
}
```

### Error (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Error (403 Forbidden):
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Validation Rules

| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| title | ✓ | string | Max 255 chars, not blank |
| isbn | ✓ | string | Max 20 chars, must be unique |
| pages | ✓ | integer | Positive integer |
| description | ✗ | string | Can be blank |
| publication_date | ✓ | string | YYYY-MM-DD format |
| publication | ✗ | integer | Valid publication ID |
| authors | ✗ | array | IDs of valid authors (exclusive with editors) |
| editors | ✗ | array | IDs of valid authors (exclusive with authors) |
| categories | ✗ | array | IDs of valid categories |
| chapters | ✗ | string | JSON stringified, only with editors |

---

## Testing Checklist

- [ ] Test with minimal fields only
- [ ] Test with authors
- [ ] Test with editors (no authors)
- [ ] Test with chapters and chapter contributors
- [ ] Test with multiple categories
- [ ] Test with image uploads
- [ ] Test missing required field (should fail)
- [ ] Test duplicate ISBN (should fail)
- [ ] Test non-existent author ID (should fail)
- [ ] Test invalid publication_date format (should fail)
- [ ] Test invalid JSON in chapters field (should fail)
- [ ] Test both authors and editors (should fail)
- [ ] Test chapters without editors (should fail)

---

## Quick Test Script (Python)

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: Simple book
payload = {
    "title": "Test Python Book",
    "isbn": "9789999999999",
    "pages": 300,
    "description": "A test book",
    "publication_date": "2024-03-15"
}

response = requests.post(f"{BASE_URL}/books/", json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test 2: Book with authors
payload = {
    "title": "Advanced Testing",
    "isbn": "9788888888888",
    "pages": 400,
    "description": "Test with authors",
    "publication_date": "2024-04-15",
    "authors": [1, 2]
}

response = requests.post(f"{BASE_URL}/books/", json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

---

## Notes

- All timestamps are in UTC
- ISO 8601 date format required (YYYY-MM-DD)
- File uploads must be valid image files (jpg, png, gif, webp)
- Maximum image file size: typically 5MB (check Django settings)
- Author/Editor order is maintained by the `order` field (auto-incremented)
