# Book API - Quick Reference

## Endpoint
```
POST /api/books/
```

**Requires**: JWT Token (Admin user)

---

## Quick Payloads

### 1️⃣ **Minimal Book**
```json
{
  "title": "Book Title",
  "isbn": "9781234567890",
  "pages": 300,
  "publication_date": "2024-03-15"
}
```

### 2️⃣ **Book with Author**
```json
{
  "title": "Book Title",
  "isbn": "9781234567890",
  "pages": 300,
  "publication_date": "2024-03-15",
  "authors": [1],
  "publication": 1,
  "categories": [1]
}
```

### 3️⃣ **Book with Multiple Authors**
```json
{
  "title": "Book Title",
  "isbn": "9781234567890",
  "pages": 300,
  "publication_date": "2024-03-15",
  "authors": [1, 2, 3],
  "publication": 1,
  "categories": [1, 2]
}
```

### 4️⃣ **Edited Book with Chapters**
```json
{
  "title": "Book Title",
  "isbn": "9781234567890",
  "pages": 300,
  "publication_date": "2024-03-15",
  "editors": [1, 2],
  "publication": 1,
  "categories": [1],
  "chapters": "[{\"title\": \"Chapter 1\", \"order\": 0, \"contributors\": [1, 2]}]"
}
```

---

## Field Requirements

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `title` | ✓ | string | Max 255 chars |
| `isbn` | ✓ | string | Must be unique, max 20 chars |
| `pages` | ✓ | integer | Positive number |
| `publication_date` | ✓ | string | Format: YYYY-MM-DD |
| `description` | ✗ | string | Optional |
| `publication` | ✗ | integer | Publication ID |
| `authors` | ✗ | array | Author IDs (mutually exclusive with `editors`) |
| `editors` | ✗ | array | Editor IDs (mutually exclusive with `authors`) |
| `categories` | ✗ | array | Category IDs |
| `chapters` | ✗ | string | JSON stringified (only with `editors`) |

---

## Authentication
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...payload...}'
```

---

## Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Missing required field | Check all required fields are present |
| 400 | ISBN must be unique | Use a different ISBN |
| 400 | Invalid author ID | Verify author exists (get /api/admin/authors/) |
| 401 | No credentials provided | Add Authorization header |
| 403 | No permission | User must be admin |

---

## Testing

**Postman**: Import `postman_collection.json`

**Python**:
```bash
python test_create_book.py "your_jwt_token"
```

**cURL**:
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","isbn":"123","pages":100,"publication_date":"2024-01-01"}'
```

---

## Tips

✓ Always use `YYYY-MM-DD` format for dates  
✓ ISBN must be unique across database  
✓ Use EITHER `authors` OR `editors`, not both  
✓ Chapters are only allowed with editors  
✓ For chapters, stringify JSON: `"chapters": "[...]"`  
✓ Author/Editor/Category IDs must exist in database  

---

**Full documentation**: See `API_PAYLOADS.md`  
**Test suite**: Use `test_create_book.py`  
**Postman collection**: Import `postman_collection.json`
