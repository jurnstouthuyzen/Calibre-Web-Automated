# API Testing & Deployment Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Testing the API](#testing-the-api)
3. [Deployment](#deployment)
4. [Integration Examples](#integration-examples)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Calibre-Web Automated running (locally or on server)
- User account with login credentials
- `curl` or similar HTTP client for testing
- (Optional) Kobo device or Kobo sync setup for full statistics testing

### Installation

The API is automatically available once you:

1. Pull the latest code with the API changes
2. Restart Calibre-Web Automated

No additional dependencies or configuration required.

---

## Testing the API

### 1. Get Your Session Cookie

First, log in to Calibre-Web through your browser, then extract the session cookie.

#### Chrome/Firefox DevTools Method:
1. Log in to Calibre-Web
2. Press F12 to open DevTools
3. Go to "Application" (Chrome) or "Storage" (Firefox) tab
4. Click "Cookies" → Select your Calibre-Web URL
5. Find the cookie named `session` (or with your COOKIE_PREFIX)
6. Copy the cookie value

#### Using curl (easier for command line):

```bash
# Login and save cookies
curl -c cookies.txt -X POST "http://localhost:8083/login" \
  -d "username=admin&password=admin123&submit=Sign+in&next=%2F"

# Use cookies for API requests
curl -b cookies.txt "http://localhost:8083/api/v2/health"
```

---

### 2. Basic API Tests

#### Test 1: Health Check (No Auth Required)

```bash
curl -X GET "http://localhost:8083/api/v2/health"
```

Expected response:
```json
{
  "status": "ok",
  "api_version": "v2",
  "timestamp": "2025-12-12T10:30:00+00:00"
}
```

#### Test 2: Get All Books

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books?page=1&per_page=5"
```

#### Test 3: Get Read Books

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/read"
```

#### Test 4: Get Currently Reading Books

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/reading"
```

#### Test 5: Get Specific Book Details

```bash
# Replace 1 with an actual book ID from your library
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/1"
```

#### Test 6: Get Book Reading State

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/1/reading-state"
```

#### Test 7: Get Book Progress

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/1/progress"
```

#### Test 8: Get Book Statistics

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/1/statistics"
```

#### Test 9: Get Statistics Summary

```bash
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/statistics/summary"
```

#### Test 10: Get Bookmarks

```bash
# All bookmarks
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/bookmarks"

# Book-specific bookmarks
curl -b cookies.txt -X GET "http://localhost:8083/api/v2/books/1/bookmarks"
```

---

### 3. Testing with Python

Create a test script `test_api.py`:

```python
#!/usr/bin/env python3
import requests
import json

# Configuration
BASE_URL = "http://localhost:8083"
USERNAME = "admin"
PASSWORD = "admin123"

# Create session
session = requests.Session()

# Login
login_data = {
    "username": USERNAME,
    "password": PASSWORD,
    "submit": "Sign in",
    "next": "/"
}
response = session.post(f"{BASE_URL}/login", data=login_data)

if response.status_code == 200:
    print("✓ Login successful")
else:
    print(f"✗ Login failed: {response.status_code}")
    exit(1)

# Test health endpoint
response = session.get(f"{BASE_URL}/api/v2/health")
print(f"\n1. Health Check: {response.json()}")

# Test books endpoint
response = session.get(f"{BASE_URL}/api/v2/books?per_page=5")
if response.status_code == 200:
    data = response.json()
    print(f"\n2. Books (found {data['pagination']['total']} total):")
    for book in data['books'][:3]:
        print(f"   - {book['title']} (ID: {book['id']})")
else:
    print(f"✗ Failed to get books: {response.status_code}")

# Test read books
response = session.get(f"{BASE_URL}/api/v2/books/read")
if response.status_code == 200:
    data = response.json()
    print(f"\n3. Read Books: {data['pagination']['total']} books finished")
else:
    print(f"✗ Failed to get read books: {response.status_code}")

# Test currently reading
response = session.get(f"{BASE_URL}/api/v2/books/reading")
if response.status_code == 200:
    data = response.json()
    print(f"\n4. Currently Reading: {data['pagination']['total']} books in progress")
    for book in data['books']:
        progress = book['reading_state'].get('progress')
        if progress:
            print(f"   - {book['title']}: {progress['progress_percent']}%")
else:
    print(f"✗ Failed to get reading books: {response.status_code}")

# Test statistics summary
response = session.get(f"{BASE_URL}/api/v2/statistics/summary")
if response.status_code == 200:
    data = response.json()
    print(f"\n5. Statistics Summary:")
    print(f"   - Books finished: {data['books_finished']}")
    print(f"   - Books in progress: {data['books_in_progress']}")
    print(f"   - Total reading time: {data['total_reading_hours']} hours")
else:
    print(f"✗ Failed to get statistics: {response.status_code}")

# Test bookmarks
response = session.get(f"{BASE_URL}/api/v2/bookmarks")
if response.status_code == 200:
    data = response.json()
    print(f"\n6. Bookmarks: {data['count']} total bookmarks")
else:
    print(f"✗ Failed to get bookmarks: {response.status_code}")

print("\n✓ All tests completed!")
```

Run the test:
```bash
python3 test_api.py
```

---

### 4. Testing with Postman

1. Import the following Postman collection:

**Collection JSON:**
```json
{
  "info": {
    "name": "Calibre-Web Book API v2",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8083"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v2/health"
      }
    },
    {
      "name": "Get All Books",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/api/v2/books?page=1&per_page=10",
          "query": [
            {"key": "page", "value": "1"},
            {"key": "per_page", "value": "10"}
          ]
        }
      }
    },
    {
      "name": "Get Read Books",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v2/books/read"
      }
    },
    {
      "name": "Get Currently Reading",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v2/books/reading"
      }
    },
    {
      "name": "Get Book by ID",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v2/books/1"
      }
    },
    {
      "name": "Get Statistics Summary",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v2/statistics/summary"
      }
    }
  ]
}
```

2. After importing, use Postman's cookie manager to add your session cookie

---

## Deployment

### Docker Deployment

If you're using Docker, the API is automatically available. Just rebuild and restart:

```bash
# Pull latest changes
git pull origin claude/calibre-book-api-01LJMJ4o6dikvwYpnyZcXw94

# Rebuild Docker container
docker-compose down
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Standard Deployment

```bash
# Pull latest changes
git pull origin claude/calibre-book-api-01LJMJ4o6dikvwYpnyZcXw94

# Restart Calibre-Web
# (method depends on your setup)

# If using systemd:
sudo systemctl restart calibre-web

# If running manually:
# Stop the current process and restart
python3 cps.py
```

### Reverse Proxy Configuration

#### Nginx

If using Nginx as a reverse proxy, ensure API endpoints are passed through:

```nginx
location /api/ {
    proxy_pass http://localhost:8083;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### Apache

```apache
ProxyPass /api/ http://localhost:8083/api/
ProxyPassReverse /api/ http://localhost:8083/api/
```

---

## Integration Examples

### JavaScript/TypeScript (Frontend)

```javascript
// API client example
class CalibreAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || window.location.origin;
  }

  async getBooks(page = 1, perPage = 20) {
    const response = await fetch(
      `${this.baseUrl}/api/v2/books?page=${page}&per_page=${perPage}`,
      { credentials: 'include' }
    );
    return response.json();
  }

  async getCurrentlyReading() {
    const response = await fetch(
      `${this.baseUrl}/api/v2/books/reading`,
      { credentials: 'include' }
    );
    return response.json();
  }

  async getBookDetails(bookId) {
    const response = await fetch(
      `${this.baseUrl}/api/v2/books/${bookId}`,
      { credentials: 'include' }
    );
    return response.json();
  }

  async getStatisticsSummary() {
    const response = await fetch(
      `${this.baseUrl}/api/v2/statistics/summary`,
      { credentials: 'include' }
    );
    return response.json();
  }
}

// Usage
const api = new CalibreAPI();
const reading = await api.getCurrentlyReading();
console.log(`Currently reading ${reading.books.length} books`);
```

### Home Assistant Integration

```yaml
# configuration.yaml
rest:
  - resource: "http://your-calibre-server:8083/api/v2/statistics/summary"
    headers:
      Cookie: "session=YOUR_SESSION_COOKIE"
    sensor:
      - name: "Books Finished"
        value_template: "{{ value_json.books_finished }}"
      - name: "Books Reading"
        value_template: "{{ value_json.books_in_progress }}"
      - name: "Total Reading Hours"
        value_template: "{{ value_json.total_reading_hours }}"
        unit_of_measurement: "hours"
```

### Node.js Backend

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8083/api/v2',
  withCredentials: true,
  headers: {
    'Cookie': 'session=YOUR_SESSION_COOKIE'
  }
});

async function getReadingProgress() {
  const { data } = await api.get('/books/reading');
  return data.books.map(book => ({
    title: book.title,
    progress: book.reading_state?.progress?.progress_percent || 0
  }));
}
```

---

## Troubleshooting

### Issue: "404 Not Found" on all API endpoints

**Solution:**
- Ensure Calibre-Web has been restarted after pulling the changes
- Check that the blueprint is registered in `main.py`
- Verify the API file exists at `cps/book_api.py`

### Issue: "401 Unauthorized" or redirects to login

**Solution:**
- Ensure you're logged in and using valid session cookie
- Check cookie expiration
- Verify CSRF protection isn't blocking requests
- For programmatic access, use the login endpoint first

### Issue: "No reading state found" or "No statistics found"

**Solution:**
- These features require Kobo sync or reading activity
- Mark books as read through the web interface to create reading state
- Use a Kobo device to generate progress/statistics data
- Alternatively, manually create reading state by interacting with books in the UI

### Issue: Empty progress/statistics fields

**Solution:**
- Progress and statistics are populated by Kobo device sync
- If not using Kobo devices, these fields will be `null`
- Consider using the `/reading-state` endpoint which includes basic read status

### Issue: CORS errors in browser

**Solution:**
- CORS may need configuration for cross-origin requests
- For same-origin requests (same domain), use `credentials: 'include'`
- For development, consider using a reverse proxy or browser extension

### Issue: Large response times with big libraries

**Solution:**
- Use pagination (`per_page` parameter)
- Reduce `per_page` value for faster responses
- Consider caching responses in your application
- Use specific endpoints instead of bulk queries

---

## Performance Tips

1. **Use pagination**: Always limit results with `page` and `per_page` parameters
2. **Cache responses**: For data that doesn't change frequently
3. **Batch requests**: Get multiple books at once rather than individual requests
4. **Use specific endpoints**: Use `/books/reading` instead of filtering `/books`
5. **Monitor logs**: Check Calibre-Web logs for errors or slow queries

---

## Security Considerations

1. **Session Management**: Session cookies should be kept secure
2. **HTTPS**: Always use HTTPS in production
3. **Authentication**: API respects Calibre-Web user permissions
4. **Rate Limiting**: Consider implementing rate limiting for public APIs
5. **Access Control**: Users can only access their own reading data

---

## Next Steps

- Integrate the API into your preferred application
- Create dashboards for reading statistics
- Build mobile apps using the API
- Automate reading tracking and reporting
- Sync data to other services

For issues or feature requests, please open an issue on the GitHub repository.
