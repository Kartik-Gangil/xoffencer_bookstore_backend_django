# XOffencer Book Store - API Test Suite

This folder contains all the test files and documentation for the Book Creation API endpoint.

---

## 📁 Files in This Folder

### 1. **API_PAYLOADS.md** 
Complete API documentation with detailed payload examples.
- 6 payload examples (minimal → complex)
- Chapters JSON structure explanation
- Image upload (multipart/form-data) instructions
- 4 cURL examples
- API response examples
- Validation rules & constraints
- Testing checklist

**Use this for**: Understanding API in detail

---

### 2. **QUICK_REFERENCE.md**
One-page quick reference cheat sheet.
- 4 quick payload templates
- Field requirements table
- Common errors & solutions
- Quick testing commands

**Use this for**: Quick lookups while testing

---

### 3. **postman_collection.json**
Postman collection with 10 pre-built requests.
- ✓ 6 working requests (different scenarios)
- ✗ 4 validation test requests

**Setup**:
1. Open Postman
2. Click **Import** → Select this file
3. Set variables:
   - `base_url`: http://localhost:8000
   - `jwt_token`: Your JWT token
4. Run requests

---

### 4. **test_create_book.py**
Python test script for automated API testing.

**Features**:
- 8 comprehensive tests (functionality + validation)
- Color-coded output
- Test summary with success rate
- Error reporting

**Requirements**:
```bash
pip install requests
```

**Usage**:
```bash
python test_create_book.py "your_jwt_token"
```

**Output example**:
```
✓ PASS: Minimal Book Creation
  → Created book with ID: 42
  → Response Code: 201

✗ FAIL: Validation: Duplicate ISBN
  → Expected 400, got 500
  → Response Code: 500

============================================================
TEST SUMMARY
============================================================
Total Tests: 8
Passed: 7
Failed: 1
...
Success Rate: 87.5%
```

---

## 🚀 Quick Start

### Option 1: Postman (GUI)
1. Import `postman_collection.json`
2. Set `jwt_token` variable
3. Run any request

### Option 2: Python Script
```bash
python test_create_book.py "eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Option 3: cURL
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Book","isbn":"123","pages":100,"publication_date":"2024-01-01"}'
```

---

## 📝 Test Scenarios

### Functionality Tests
1. **Minimal Book** - Required fields only
2. **Single Author** - With 1 author
3. **Multiple Authors** - With 3+ authors
4. **Edited Book with Chapters** - Complex structure

### Validation Tests
5. **Missing Required Field** - Should reject (400)
6. **Duplicate ISBN** - Should reject (400)
7. **Invalid Author ID** - Should reject (400)
8. **Invalid Date Format** - Should reject (400)

---

## 📋 API Endpoint

**POST** `/api/books/`

**Required Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Required Fields**:
- `title` (string, max 255)
- `isbn` (string, unique, max 20)
- `pages` (integer)
- `publication_date` (YYYY-MM-DD)

**Optional Fields**:
- `description` (string)
- `publication` (int - publication ID)
- `authors` (array of author IDs)
- `editors` (array of editor IDs)
- `categories` (array of category IDs)
- `chapters` (JSON stringified - only with editors)

---

## ⚠️ Important Rules

✓ Use EITHER `authors` OR `editors`, NOT both  
✓ Chapters only with editors  
✓ ISBN must be unique  
✓ Date format: YYYY-MM-DD  
✓ All author/editor IDs must exist  

---

## 🔍 Debugging Tips

### Invalid Author ID Error
**Problem**: "Invalid author ID"
**Solution**: 
```bash
# Check available authors
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/admin/authors/
```

### Duplicate ISBN Error
**Problem**: "ISBN already exists"
**Solution**: Use a unique ISBN in your payload

### JWT Token Expired
**Problem**: "Authentication credentials invalid"
**Solution**: Get a fresh JWT token from `/api/auth/login/`

### 500 Internal Server Error
**Check**:
1. Database connection
2. Invalid relationship IDs
3. Database constraints
4. Server logs: `django runserver`

---

## 📊 Expected Responses

### Success (201 Created)
```json
{
  "id": 42,
  "title": "Python Basics",
  "isbn": "9781234567890",
  "pages": 250,
  "description": "Learn Python from scratch",
  "publication_date": "2024-03-15",
  ...
}
```

### Bad Request (400)
```json
{
  "field_name": ["Error message"]
}
```

### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Forbidden (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 🛠️ Customizing Tests

### Python Script Modifications

**Change base URL**:
```python
BASE_URL = "https://api.example.com"
API_ENDPOINT = f"{BASE_URL}/api/books/"
```

**Add more tests**:
```python
def test_custom_scenario(self):
    payload = { ... }
    response = requests.post(API_ENDPOINT, json=payload, headers=self.headers)
    # Your assertions
```

**Change author IDs**:
```python
"authors": [10, 11]  # Use real author IDs from your database
```

---

## ✅ Testing Checklist

- [ ] Can create minimal book
- [ ] Can create book with authors
- [ ] Can create edited book with chapters
- [ ] Can upload book images
- [ ] Rejects missing required fields
- [ ] Rejects duplicate ISBN
- [ ] Rejects invalid author IDs
- [ ] Rejects both authors and editors together
- [ ] Returns correct 201 status code
- [ ] Response includes book ID

---

## 📚 Additional Resources

- **Full API Docs**: See `API_PAYLOADS.md`
- **Codebase Index**: See `../CODEBASE_INDEX.md`
- **Backend Code**: See `../books/views.py` (BookViewSet)
- **Models**: See `../books/models.py` (Book model)
- **Serializers**: See `../books/serializers.py` (BookWriteSerializer)

---

## 🐛 Reporting Issues

If tests fail:

1. **Check JWT token** - Is it valid and not expired?
2. **Check author IDs** - Do they exist in database?
3. **Check database** - Is it running and connected?
4. **Check server** - Is Django dev server running?
5. **Check logs** - Look at terminal output for errors

---

## 📞 Support

For issues with:
- **API functionality** → See `API_PAYLOADS.md`
- **Test script** → Check error messages in terminal
- **Postman** → Import collection again, check variables
- **Django errors** → Check `python manage.py runserver` output

---

**Last Updated**: March 3, 2026  
**Test Coverage**: 8 scenarios (4 positive + 4 negative)  
**Status**: Production Ready ✅
