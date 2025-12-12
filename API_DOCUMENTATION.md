# Book Information API v2 Documentation

## Overview

The Book Information API v2 provides RESTful endpoints for accessing book metadata, reading progress, statistics, and bookmarks from your Calibre library. All endpoints require authentication and return JSON responses.

**Base URL:** `/api/v2`

## Authentication

All endpoints (except `/health`) require user authentication. Authentication is handled through the existing Calibre-Web session/login system. Users must be logged in to access the API.

## Endpoints

### Health Check

#### `GET /api/v2/health`

Check API status and availability. No authentication required.

**Response:**
```json
{
  "status": "ok",
  "api_version": "v2",
  "timestamp": "2025-12-12T10:30:00+00:00"
}
```

---

### Book Listing

#### `GET /api/v2/books`

Get a paginated list of all books accessible to the current user.

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `per_page` (int, optional): Items per page (default: 20, max: 100)
- `sort` (string, optional): Sort field - `title`, `timestamp`, `pubdate` (default: `timestamp`)
- `order` (string, optional): Sort order - `asc`, `desc` (default: `desc`)

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books?page=1&per_page=10&sort=title&order=asc" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "books": [
    {
      "id": 1,
      "title": "Example Book",
      "sort": "Example Book",
      "timestamp": "2025-01-01T12:00:00",
      "pubdate": "2024-12-01T00:00:00",
      "path": "Example Author/Example Book (1)",
      "has_cover": 1,
      "uuid": "abc123...",
      "isbn": "978-1234567890"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "pages": 10
  }
}
```

---

#### `GET /api/v2/books/read`

Get books marked as finished/read by the current user.

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `per_page` (int, optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/read?page=1&per_page=20" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "books": [
    {
      "id": 5,
      "title": "Finished Book",
      "authors": [{"id": 1, "name": "Author Name", "sort": "Name, Author"}],
      "tags": [{"id": 3, "name": "Fiction"}],
      "series": {"id": 2, "name": "Series Name", "index": 1.0},
      "ratings": [{"id": 1, "rating": 5}],
      "languages": [{"id": 1, "lang_code": "eng"}],
      "publishers": [{"id": 1, "name": "Publisher Name"}],
      "comments": "Book description...",
      "formats": [{"id": 1, "format": "EPUB", "uncompressed_size": 1024000}],
      "reading_state": {
        "book_id": 5,
        "user_id": 1,
        "read_status": 1,
        "read_status_name": "finished",
        "last_modified": "2025-12-10T14:30:00+00:00",
        "last_time_started_reading": "2025-12-01T08:00:00+00:00",
        "times_started_reading": 3,
        "progress": null,
        "statistics": {
          "remaining_time_minutes": 0,
          "spent_reading_minutes": 240,
          "last_modified": "2025-12-10T14:30:00+00:00"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15,
    "pages": 1
  }
}
```

---

#### `GET /api/v2/books/reading`

Get books currently being read (in progress) by the current user.

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `per_page` (int, optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/reading" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "books": [
    {
      "id": 10,
      "title": "Currently Reading Book",
      "authors": [{"id": 2, "name": "Another Author", "sort": "Author, Another"}],
      "reading_state": {
        "book_id": 10,
        "user_id": 1,
        "read_status": 2,
        "read_status_name": "in_progress",
        "last_modified": "2025-12-12T09:00:00+00:00",
        "last_time_started_reading": "2025-12-11T19:00:00+00:00",
        "times_started_reading": 1,
        "progress": {
          "progress_percent": 45.5,
          "content_source_progress_percent": 45.5,
          "location_value": "chapter-5",
          "location_type": "chapter",
          "location_source": "kobo",
          "last_modified": "2025-12-12T09:00:00+00:00"
        },
        "statistics": {
          "remaining_time_minutes": 180,
          "spent_reading_minutes": 120,
          "last_modified": "2025-12-12T09:00:00+00:00"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "pages": 1
  }
}
```

---

### Individual Book Information

#### `GET /api/v2/books/<book_id>`

Get detailed information about a specific book.

**Path Parameters:**
- `book_id` (int): Calibre book ID

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/10" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "id": 10,
  "title": "Book Title",
  "sort": "Book Title",
  "timestamp": "2025-01-15T10:00:00",
  "pubdate": "2024-11-01T00:00:00",
  "path": "Author Name/Book Title (10)",
  "has_cover": 1,
  "uuid": "def456...",
  "isbn": "978-0987654321",
  "authors": [{"id": 2, "name": "Author Name", "sort": "Name, Author"}],
  "tags": [{"id": 1, "name": "Science Fiction"}, {"id": 5, "name": "Adventure"}],
  "series": {"id": 3, "name": "Epic Series", "index": 2.0},
  "ratings": [{"id": 2, "rating": 4}],
  "languages": [{"id": 1, "lang_code": "eng"}],
  "publishers": [{"id": 2, "name": "Great Publisher"}],
  "comments": "An amazing book about...",
  "formats": [
    {"id": 15, "format": "EPUB", "uncompressed_size": 2048000},
    {"id": 16, "format": "PDF", "uncompressed_size": 5120000}
  ],
  "reading_state": {
    "book_id": 10,
    "user_id": 1,
    "read_status": 2,
    "read_status_name": "in_progress",
    "last_modified": "2025-12-12T09:00:00+00:00",
    "progress": {...},
    "statistics": {...}
  }
}
```

---

### Reading State & Progress

#### `GET /api/v2/books/<book_id>/reading-state`

Get the complete reading state for a specific book.

**Path Parameters:**
- `book_id` (int): Calibre book ID

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/10/reading-state" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "book_id": 10,
  "user_id": 1,
  "read_status": 2,
  "read_status_name": "in_progress",
  "last_modified": "2025-12-12T09:00:00+00:00",
  "last_time_started_reading": "2025-12-11T19:00:00+00:00",
  "times_started_reading": 1,
  "progress": {
    "progress_percent": 45.5,
    "content_source_progress_percent": 45.5,
    "location_value": "chapter-5",
    "location_type": "chapter",
    "location_source": "kobo",
    "last_modified": "2025-12-12T09:00:00+00:00"
  },
  "statistics": {
    "remaining_time_minutes": 180,
    "spent_reading_minutes": 120,
    "last_modified": "2025-12-12T09:00:00+00:00"
  }
}
```

---

#### `GET /api/v2/books/<book_id>/progress`

Get reading progress (percentage and location) for a specific book.

**Path Parameters:**
- `book_id` (int): Calibre book ID

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/10/progress" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "book_id": 10,
  "progress_percent": 45.5,
  "content_source_progress_percent": 45.5,
  "location_value": "chapter-5",
  "location_type": "chapter",
  "location_source": "kobo",
  "last_modified": "2025-12-12T09:00:00+00:00"
}
```

---

### Statistics

#### `GET /api/v2/books/<book_id>/statistics`

Get KoboStatistics (reading time, remaining time) for a specific book.

**Path Parameters:**
- `book_id` (int): Calibre book ID

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/10/statistics" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "book_id": 10,
  "remaining_time_minutes": 180,
  "spent_reading_minutes": 120,
  "remaining_time_hours": 3.0,
  "spent_reading_hours": 2.0,
  "last_modified": "2025-12-12T09:00:00+00:00"
}
```

---

#### `GET /api/v2/statistics/summary`

Get aggregated reading statistics for all books for the current user.

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/statistics/summary" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "total_books_tracked": 50,
  "books_finished": 35,
  "books_in_progress": 5,
  "books_unread": 10,
  "total_reading_minutes": 14400,
  "total_reading_hours": 240.0,
  "total_remaining_minutes": 900,
  "total_remaining_hours": 15.0,
  "books_with_statistics": 40
}
```

---

### Bookmarks

#### `GET /api/v2/books/<book_id>/bookmarks`

Get bookmarks for a specific book.

**Path Parameters:**
- `book_id` (int): Calibre book ID

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/books/10/bookmarks" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "book_id": 10,
  "bookmarks": [
    {
      "id": 1,
      "book_id": 10,
      "format": "EPUB",
      "bookmark_key": "chapter-3-page-45"
    },
    {
      "id": 2,
      "book_id": 10,
      "format": "EPUB",
      "bookmark_key": "chapter-7-page-120"
    }
  ],
  "count": 2
}
```

---

#### `GET /api/v2/bookmarks`

Get all bookmarks for the current user across all books.

**Example Request:**
```bash
curl -X GET "http://localhost:8083/api/v2/bookmarks" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "bookmarks": [
    {
      "id": 1,
      "book_id": 10,
      "book_title": "Currently Reading Book",
      "format": "EPUB",
      "bookmark_key": "chapter-3-page-45"
    },
    {
      "id": 3,
      "book_id": 15,
      "book_title": "Another Book",
      "format": "PDF",
      "bookmark_key": "page-78"
    }
  ],
  "count": 2
}
```

---

## Read Status Codes

The `read_status` field uses the following codes:

- `0` - Unread (`"unread"`)
- `1` - Finished/Read (`"finished"`)
- `2` - In Progress (`"in_progress"`)

The API returns both the numeric code (`read_status`) and human-readable name (`read_status_name`).

---

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

**404 Not Found:**
```json
{
  "error": "Book not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to retrieve books"
}
```

**401 Unauthorized:**
Returns redirect to login page or appropriate authentication error.

---

## Rate Limiting

The API currently does not have specific rate limits beyond the existing Calibre-Web rate limiting configuration. However, clients should implement reasonable request throttling to avoid overloading the server.

---

## Notes

1. **KoboStatistics Data**: Reading statistics (time spent, remaining time) are only available for books that have been synced with Kobo devices or have Kobo reading state. Books without Kobo sync will not have `progress` or `statistics` fields.

2. **Progress Tracking**: Progress percentage and location are tracked through Kobo device synchronization. If you're not using a Kobo device, this data may not be available.

3. **Timestamps**: All timestamps are returned in ISO 8601 format with UTC timezone.

4. **Pagination**: For large libraries, always use pagination parameters to limit response size and improve performance.

5. **Authentication**: The API uses the same authentication system as the main Calibre-Web application. You must be logged in with a valid session cookie.
