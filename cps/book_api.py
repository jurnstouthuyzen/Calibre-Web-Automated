# -*- coding: utf-8 -*-
# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2025 Calibre-Web contributors
# Copyright (C) 2024-2025 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""
Book Information API v2
REST API for accessing book information, reading progress, and statistics from Calibre database
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from . import config, logger, db, calibre_db, ub
from .usermanagement import user_login_required
from .cw_login import current_user

book_api = Blueprint("book_api", __name__, url_prefix="/api/v2")
log = logger.create()


def serialize_book(book, include_details=False):
    """
    Serialize a Calibre book object to JSON-compatible dictionary

    Args:
        book: db.Books object
        include_details: If True, include full metadata (authors, tags, etc.)

    Returns:
        Dictionary with book information
    """
    if not book:
        return None

    basic_info = {
        "id": book.id,
        "title": book.title,
        "sort": book.sort,
        "timestamp": book.timestamp.isoformat() if book.timestamp else None,
        "pubdate": book.pubdate.isoformat() if book.pubdate else None,
        "path": book.path,
        "has_cover": book.has_cover,
        "uuid": book.uuid,
        "isbn": book.isbn,
    }

    if include_details:
        basic_info.update({
            "authors": [{"id": a.id, "name": a.name, "sort": a.sort} for a in book.authors] if book.authors else [],
            "tags": [{"id": t.id, "name": t.name} for t in book.tags] if book.tags else [],
            "series": {
                "id": book.series[0].id,
                "name": book.series[0].name,
                "index": book.series_index
            } if book.series else None,
            "ratings": [{"id": r.id, "rating": r.rating} for r in book.ratings] if book.ratings else [],
            "languages": [{"id": l.id, "lang_code": l.lang_code} for l in book.languages] if book.languages else [],
            "publishers": [{"id": p.id, "name": p.name} for p in book.publishers] if book.publishers else [],
            "comments": book.comments[0].text if book.comments else None,
            "formats": [{"id": d.id, "format": d.format, "uncompressed_size": d.uncompressed_size} for d in book.data] if book.data else [],
        })

    return basic_info


def serialize_reading_state(read_book):
    """
    Serialize ReadBook and associated KoboReadingState to JSON

    Args:
        read_book: ub.ReadBook object

    Returns:
        Dictionary with reading state information
    """
    if not read_book:
        return None

    reading_state = {
        "book_id": read_book.book_id,
        "user_id": read_book.user_id,
        "read_status": read_book.read_status,
        "read_status_name": get_read_status_name(read_book.read_status),
        "last_modified": read_book.last_modified.isoformat() if read_book.last_modified else None,
        "last_time_started_reading": read_book.last_time_started_reading.isoformat() if read_book.last_time_started_reading else None,
        "times_started_reading": read_book.times_started_reading,
        "progress": None,
        "statistics": None,
    }

    # Add Kobo reading state if available
    if read_book.kobo_reading_state:
        kobo_state = read_book.kobo_reading_state

        # Add progress from bookmark
        if kobo_state.current_bookmark:
            bookmark = kobo_state.current_bookmark
            reading_state["progress"] = {
                "progress_percent": bookmark.progress_percent,
                "content_source_progress_percent": bookmark.content_source_progress_percent,
                "location_value": bookmark.location_value,
                "location_type": bookmark.location_type,
                "location_source": bookmark.location_source,
                "last_modified": bookmark.last_modified.isoformat() if bookmark.last_modified else None,
            }

        # Add statistics
        if kobo_state.statistics:
            stats = kobo_state.statistics
            reading_state["statistics"] = {
                "remaining_time_minutes": stats.remaining_time_minutes,
                "spent_reading_minutes": stats.spent_reading_minutes,
                "last_modified": stats.last_modified.isoformat() if stats.last_modified else None,
            }

    return reading_state


def get_read_status_name(status_code):
    """Convert read status code to human-readable name"""
    status_map = {
        ub.ReadBook.STATUS_UNREAD: "unread",
        ub.ReadBook.STATUS_FINISHED: "finished",
        ub.ReadBook.STATUS_IN_PROGRESS: "in_progress",
    }
    return status_map.get(status_code, "unknown")


# ==================== BOOK LISTING ENDPOINTS ====================

@book_api.route("/books", methods=["GET"])
@user_login_required
def get_books():
    """
    Get list of all books accessible to the current user

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        sort (str): Sort field (title, timestamp, pubdate)
        order (str): Sort order (asc, desc)

    Returns:
        JSON with books list and pagination info
    """
    try:
        # Get pagination parameters
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        sort_field = request.args.get("sort", "timestamp")
        sort_order = request.args.get("order", "desc")

        # Calculate offset
        offset = (page - 1) * per_page

        # Build query
        query = calibre_db.session.query(db.Books)

        # Apply sorting
        sort_column = getattr(db.Books, sort_field, db.Books.timestamp)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Get total count
        total = query.count()

        # Apply pagination
        books = query.limit(per_page).offset(offset).all()

        # Serialize books
        books_data = [serialize_book(book) for book in books]

        return jsonify({
            "books": books_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            }
        }), 200

    except Exception as e:
        log.error(f"Error getting books: {e}")
        return jsonify({"error": "Failed to retrieve books"}), 500


@book_api.route("/books/read", methods=["GET"])
@user_login_required
def get_read_books():
    """
    Get list of books marked as read/finished by the current user

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        JSON with read books and their metadata
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        offset = (page - 1) * per_page

        # Query read books for current user
        read_books_query = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.user_id == current_user.id,
            ub.ReadBook.read_status == ub.ReadBook.STATUS_FINISHED
        ).order_by(ub.ReadBook.last_modified.desc())

        total = read_books_query.count()
        read_books = read_books_query.limit(per_page).offset(offset).all()

        # Fetch book details from Calibre database
        result = []
        for read_book in read_books:
            book = calibre_db.get_book(read_book.book_id)
            if book:
                book_data = serialize_book(book, include_details=True)
                book_data["reading_state"] = serialize_reading_state(read_book)
                result.append(book_data)

        return jsonify({
            "books": result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            }
        }), 200

    except Exception as e:
        log.error(f"Error getting read books: {e}")
        return jsonify({"error": "Failed to retrieve read books"}), 500


@book_api.route("/books/reading", methods=["GET"])
@user_login_required
def get_reading_books():
    """
    Get list of books currently being read (in progress) by the current user

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        JSON with currently reading books, progress, and statistics
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        offset = (page - 1) * per_page

        # Query books currently being read
        reading_books_query = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.user_id == current_user.id,
            ub.ReadBook.read_status == ub.ReadBook.STATUS_IN_PROGRESS
        ).order_by(ub.ReadBook.last_modified.desc())

        total = reading_books_query.count()
        reading_books = reading_books_query.limit(per_page).offset(offset).all()

        # Fetch book details
        result = []
        for read_book in reading_books:
            book = calibre_db.get_book(read_book.book_id)
            if book:
                book_data = serialize_book(book, include_details=True)
                book_data["reading_state"] = serialize_reading_state(read_book)
                result.append(book_data)

        return jsonify({
            "books": result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            }
        }), 200

    except Exception as e:
        log.error(f"Error getting reading books: {e}")
        return jsonify({"error": "Failed to retrieve reading books"}), 500


# ==================== INDIVIDUAL BOOK ENDPOINTS ====================

@book_api.route("/books/<int:book_id>", methods=["GET"])
@user_login_required
def get_book(book_id):
    """
    Get detailed information about a specific book

    Args:
        book_id: Calibre book ID

    Returns:
        JSON with complete book metadata
    """
    try:
        book = calibre_db.get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404

        book_data = serialize_book(book, include_details=True)

        # Add reading state if available
        read_book = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.book_id == book_id,
            ub.ReadBook.user_id == current_user.id
        ).first()

        if read_book:
            book_data["reading_state"] = serialize_reading_state(read_book)
        else:
            book_data["reading_state"] = None

        return jsonify(book_data), 200

    except Exception as e:
        log.error(f"Error getting book {book_id}: {e}")
        return jsonify({"error": "Failed to retrieve book"}), 500


@book_api.route("/books/<int:book_id>/reading-state", methods=["GET"])
@user_login_required
def get_book_reading_state(book_id):
    """
    Get reading state for a specific book and current user

    Args:
        book_id: Calibre book ID

    Returns:
        JSON with reading status, progress, and statistics
    """
    try:
        read_book = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.book_id == book_id,
            ub.ReadBook.user_id == current_user.id
        ).first()

        if not read_book:
            return jsonify({"error": "No reading state found for this book"}), 404

        return jsonify(serialize_reading_state(read_book)), 200

    except Exception as e:
        log.error(f"Error getting reading state for book {book_id}: {e}")
        return jsonify({"error": "Failed to retrieve reading state"}), 500


@book_api.route("/books/<int:book_id>/progress", methods=["GET"])
@user_login_required
def get_book_progress(book_id):
    """
    Get reading progress for a specific book

    Args:
        book_id: Calibre book ID

    Returns:
        JSON with progress percentage and location
    """
    try:
        read_book = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.book_id == book_id,
            ub.ReadBook.user_id == current_user.id
        ).first()

        if not read_book or not read_book.kobo_reading_state:
            return jsonify({"error": "No progress information found"}), 404

        kobo_state = read_book.kobo_reading_state

        if not kobo_state.current_bookmark:
            return jsonify({"error": "No bookmark/progress found"}), 404

        bookmark = kobo_state.current_bookmark

        return jsonify({
            "book_id": book_id,
            "progress_percent": bookmark.progress_percent,
            "content_source_progress_percent": bookmark.content_source_progress_percent,
            "location_value": bookmark.location_value,
            "location_type": bookmark.location_type,
            "location_source": bookmark.location_source,
            "last_modified": bookmark.last_modified.isoformat() if bookmark.last_modified else None,
        }), 200

    except Exception as e:
        log.error(f"Error getting progress for book {book_id}: {e}")
        return jsonify({"error": "Failed to retrieve progress"}), 500


# ==================== STATISTICS ENDPOINTS ====================

@book_api.route("/books/<int:book_id>/statistics", methods=["GET"])
@user_login_required
def get_book_statistics(book_id):
    """
    Get KoboStatistics (reading time, remaining time) for a specific book

    Args:
        book_id: Calibre book ID

    Returns:
        JSON with reading time statistics
    """
    try:
        read_book = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.book_id == book_id,
            ub.ReadBook.user_id == current_user.id
        ).first()

        if not read_book or not read_book.kobo_reading_state:
            return jsonify({"error": "No reading state found"}), 404

        kobo_state = read_book.kobo_reading_state

        if not kobo_state.statistics:
            return jsonify({"error": "No statistics found"}), 404

        stats = kobo_state.statistics

        return jsonify({
            "book_id": book_id,
            "remaining_time_minutes": stats.remaining_time_minutes,
            "spent_reading_minutes": stats.spent_reading_minutes,
            "remaining_time_hours": round(stats.remaining_time_minutes / 60, 2) if stats.remaining_time_minutes else None,
            "spent_reading_hours": round(stats.spent_reading_minutes / 60, 2) if stats.spent_reading_minutes else None,
            "last_modified": stats.last_modified.isoformat() if stats.last_modified else None,
        }), 200

    except Exception as e:
        log.error(f"Error getting statistics for book {book_id}: {e}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500


@book_api.route("/statistics/summary", methods=["GET"])
@user_login_required
def get_statistics_summary():
    """
    Get summary of reading statistics for all books for the current user

    Returns:
        JSON with aggregated reading statistics
    """
    try:
        # Get all reading states for current user
        reading_states = ub.session.query(ub.ReadBook).filter(
            ub.ReadBook.user_id == current_user.id
        ).all()

        total_books_read = sum(1 for rb in reading_states if rb.read_status == ub.ReadBook.STATUS_FINISHED)
        total_books_reading = sum(1 for rb in reading_states if rb.read_status == ub.ReadBook.STATUS_IN_PROGRESS)
        total_books_unread = sum(1 for rb in reading_states if rb.read_status == ub.ReadBook.STATUS_UNREAD)

        # Calculate total reading time
        total_reading_minutes = 0
        total_remaining_minutes = 0
        books_with_stats = 0

        for read_book in reading_states:
            if read_book.kobo_reading_state and read_book.kobo_reading_state.statistics:
                stats = read_book.kobo_reading_state.statistics
                if stats.spent_reading_minutes:
                    total_reading_minutes += stats.spent_reading_minutes
                if stats.remaining_time_minutes:
                    total_remaining_minutes += stats.remaining_time_minutes
                books_with_stats += 1

        return jsonify({
            "total_books_tracked": len(reading_states),
            "books_finished": total_books_read,
            "books_in_progress": total_books_reading,
            "books_unread": total_books_unread,
            "total_reading_minutes": total_reading_minutes,
            "total_reading_hours": round(total_reading_minutes / 60, 2),
            "total_remaining_minutes": total_remaining_minutes,
            "total_remaining_hours": round(total_remaining_minutes / 60, 2),
            "books_with_statistics": books_with_stats,
        }), 200

    except Exception as e:
        log.error(f"Error getting statistics summary: {e}")
        return jsonify({"error": "Failed to retrieve statistics summary"}), 500


# ==================== BOOKMARK ENDPOINTS ====================

@book_api.route("/books/<int:book_id>/bookmarks", methods=["GET"])
@user_login_required
def get_book_bookmarks(book_id):
    """
    Get bookmarks for a specific book and current user

    Args:
        book_id: Calibre book ID

    Returns:
        JSON with list of bookmarks
    """
    try:
        bookmarks = ub.session.query(ub.Bookmark).filter(
            ub.Bookmark.book_id == book_id,
            ub.Bookmark.user_id == current_user.id
        ).all()

        bookmarks_data = [
            {
                "id": bookmark.id,
                "book_id": bookmark.book_id,
                "format": bookmark.format,
                "bookmark_key": bookmark.bookmark_key,
            }
            for bookmark in bookmarks
        ]

        return jsonify({
            "book_id": book_id,
            "bookmarks": bookmarks_data,
            "count": len(bookmarks_data),
        }), 200

    except Exception as e:
        log.error(f"Error getting bookmarks for book {book_id}: {e}")
        return jsonify({"error": "Failed to retrieve bookmarks"}), 500


@book_api.route("/bookmarks", methods=["GET"])
@user_login_required
def get_all_bookmarks():
    """
    Get all bookmarks for the current user across all books

    Returns:
        JSON with list of all bookmarks
    """
    try:
        bookmarks = ub.session.query(ub.Bookmark).filter(
            ub.Bookmark.user_id == current_user.id
        ).all()

        bookmarks_data = []
        for bookmark in bookmarks:
            # Get book info
            book = calibre_db.get_book(bookmark.book_id)
            bookmark_info = {
                "id": bookmark.id,
                "book_id": bookmark.book_id,
                "book_title": book.title if book else "Unknown",
                "format": bookmark.format,
                "bookmark_key": bookmark.bookmark_key,
            }
            bookmarks_data.append(bookmark_info)

        return jsonify({
            "bookmarks": bookmarks_data,
            "count": len(bookmarks_data),
        }), 200

    except Exception as e:
        log.error(f"Error getting all bookmarks: {e}")
        return jsonify({"error": "Failed to retrieve bookmarks"}), 500


# ==================== HEALTH CHECK ====================

@book_api.route("/health", methods=["GET"])
def health_check():
    """
    API health check endpoint

    Returns:
        JSON with API status
    """
    return jsonify({
        "status": "ok",
        "api_version": "v2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200
