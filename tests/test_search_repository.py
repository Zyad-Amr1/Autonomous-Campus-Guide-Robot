import sqlite3

from database.repositories.search_repository import (
    normalize_search_text,
    retrieve_from_database,
)


def _create_search_db(db_path):
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE faculties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                building TEXT,
                dean_name TEXT
            );

            CREATE TABLE professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                title TEXT,
                email TEXT,
                phone TEXT,
                office_hours TEXT,
                bio TEXT
            );

            CREATE TABLE rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT,
                room_number TEXT,
                building TEXT,
                floor INTEGER,
                category TEXT,
                description TEXT
            );

            CREATE TABLE faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                keywords TEXT,
                category TEXT
            );
            """
        )
        connection.execute(
            """
            INSERT INTO faculties (name, description, building, dean_name)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Faculty of Engineering",
                "Engineering programs and robotics labs.",
                "Main Building",
                "Dr. Hany",
            ),
        )
        connection.execute(
            """
            INSERT INTO professors (full_name, title, email, phone, office_hours, bio)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Dr. Mona Samir",
                "Professor of Robotics",
                "mona@ecu.edu",
                "12345",
                "Sunday 10:00",
                "Researches autonomous navigation.",
            ),
        )
        connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Main Cafeteria",
                "C01",
                "Student Center",
                1,
                "Food",
                "Campus dining and cafeteria services.",
            ),
        )
        connection.execute(
            """
            INSERT INTO rooms (room_name, room_number, building, floor, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Design Studio",
                "D101",
                "Building D",
                1,
                "Studio",
                "Design classroom and student project space.",
            ),
        )
        connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            (
                "How do I apply for admission?",
                "Submit your admission documents online.",
                "admission apply documents",
                "Admissions",
            ),
        )
        connection.execute(
            """
            INSERT INTO faq (question, answer, keywords, category)
            VALUES (?, ?, ?, ?)
            """,
            (
                "What is the default admin login?",
                "Admins should use their assigned credentials.",
                "admin login password",
                "Administration",
            ),
        )
        connection.commit()
    finally:
        connection.close()


def test_professor_query_returns_professor_match(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("professors", db_path)

    assert results
    assert results[0]["source"] == "database"
    assert results[0]["source_table"] == "professors"
    assert results[0]["title"] == "Dr. Mona Samir | Professor of Robotics"


def test_room_cafeteria_query_returns_room_match(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("cafeteria", db_path)

    assert results[0]["source_table"] == "rooms"
    assert "Main Cafeteria" in results[0]["title"]


def test_faculty_query_returns_faculty_match(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("faculties", db_path)

    assert results[0]["source_table"] == "faculties"
    assert results[0]["title"] == "Faculty of Engineering"


def test_faq_query_returns_faq_match(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("admission documents", db_path)

    assert results[0]["source_table"] == "faq"
    assert results[0]["title"] == "How do I apply for admission?"


def test_zero_match_query_returns_empty_list(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    assert retrieve_from_database("zzzzzzzzzz", db_path) == []


def test_missing_table_does_not_crash(tmp_path):
    db_path = tmp_path / "partial.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                title TEXT,
                email TEXT,
                phone TEXT,
                office_hours TEXT,
                bio TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO professors (full_name, title, email, phone, office_hours, bio)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Dr. Kareem Ali",
                "Professor",
                "kareem@ecu.edu",
                None,
                None,
                "Teaches AI.",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    results = retrieve_from_database("professor", db_path)

    assert len(results) == 1
    assert results[0]["source_table"] == "professors"


def test_results_are_sorted_by_score_descending(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("robotics engineering", db_path)

    scores = [result["score"] for result in results]
    assert scores == sorted(scores, reverse=True)


def test_limit_parameter_works(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("engineering professor cafeteria faq", db_path, limit=2)

    assert len(results) == 2


def test_normalize_search_text_handles_room_code_variants():
    assert normalize_search_text(" D101 ") == "d101"
    assert normalize_search_text("D 101") == "d101"
    assert normalize_search_text("d-101") == "d101"
    assert normalize_search_text("d_101") == "d101"
    assert normalize_search_text(None) == ""


def test_lowercase_room_code_matches_uppercase_d101(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("d101", db_path)

    assert results[0]["source_table"] == "rooms"
    assert "D101" in results[0]["title"]


def test_spaced_room_code_matches_d101(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("D 101", db_path)

    assert results[0]["source_table"] == "rooms"
    assert "D101" in results[0]["title"]


def test_hyphenated_room_code_matches_d101(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("d-101", db_path)

    assert results[0]["source_table"] == "rooms"
    assert "D101" in results[0]["title"]


def test_room_code_matching_is_case_insensitive(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    lower_results = retrieve_from_database("d101", db_path)
    upper_results = retrieve_from_database("D101", db_path)

    assert lower_results[0]["title"] == upper_results[0]["title"]


def test_typo_profesors_still_matches_professors(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("profesors", db_path)

    assert results[0]["source_table"] == "professors"


def test_typo_cafetria_still_matches_cafeteria(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("cafetria", db_path)

    assert results[0]["source_table"] == "rooms"
    assert "Cafeteria" in results[0]["title"]


def test_room_code_query_does_not_return_unrelated_faq_as_top_result(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("what is d101", db_path)

    assert results
    assert results[0]["source_table"] == "rooms"
    assert "D101" in results[0]["title"]
    assert results[0]["title"] != "What is the default admin login?"


def test_arabic_query_does_not_crash(tmp_path):
    db_path = tmp_path / "search.db"
    _create_search_db(db_path)

    results = retrieve_from_database("أين القاعة d101؟", db_path)

    assert isinstance(results, list)
