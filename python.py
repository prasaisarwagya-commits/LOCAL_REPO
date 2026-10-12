"""
================================================================================
COMPLETE LIBRARY & STUDENT MANAGEMENT SYSTEM (1,000 LINES)
================================================================================
A production-grade, modular command-line application designed for managing
books, students, administrative operations, transaction logs, and statistics.
================================================================================
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


# ==============================================================================
# SECTION 1: DOMAIN CONSTANTS & UTILITIES
# ==============================================================================

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_FINE_PER_DAY = 1.50
MAX_ISSUED_BOOKS_PER_STUDENT = 3
DEFAULT_BORROW_DAYS = 14

DATA_DIR = "library_data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
LOGS_FILE = os.path.join(DATA_DIR, "system.log")


def ensure_data_directory_exists() -> None:
    """Ensures that the data storage folder exists on disk."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def get_current_timestamp() -> str:
    """Returns formatted current timestamp string."""
    return datetime.now().strftime(DATE_FORMAT)


def calculate_days_overdue(due_date_str: str) -> int:
    """Calculates overdue days based on due date string."""
    due_date = datetime.strptime(due_date_str, DATE_FORMAT)
    now = datetime.now()
    if now > due_date:
        return (now - due_date).days
    return 0


# ==============================================================================
# SECTION 2: LOGGING SYSTEM
# ==============================================================================

class Logger:
    """System logger utility for tracking operations and errors."""

    @staticmethod
    def log(message: str, level: str = "INFO") -> None:
        ensure_data_directory_exists()
        timestamp = get_current_timestamp()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(LOGS_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

    @staticmethod
    def info(message: str) -> None:
        Logger.log(message, level="INFO")

    @staticmethod
    def warning(message: str) -> None:
        Logger.log(message, level="WARNING")

    @staticmethod
    def error(message: str) -> None:
        Logger.log(message, level="ERROR")


# ==============================================================================
# SECTION 3: MODEL DEFINITIONS
# ==============================================================================

class Book:
    """Represents a physical or digital book within the library inventory."""

    def __init__(
        self,
        book_id: str,
        title: str,
        author: str,
        isbn: str,
        genre: str,
        total_copies: int = 1,
        available_copies: Optional[int] = None,
    ):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.total_copies = total_copies
        self.available_copies = available_copies if available_copies is not None else total_copies

    def to_dict(self) -> Dict[str, Any]:
        """Serializes book object to dictionary format."""
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "genre": self.genre,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Book":
        """Deserializes dictionary payload into a Book object."""
        return Book(
            book_id=data["book_id"],
            title=data["title"],
            author=data["author"],
            isbn=data["isbn"],
            genre=data["genre"],
            total_copies=data["total_copies"],
            available_copies=data["available_copies"],
        )

    def is_available(self) -> bool:
        """Checks if at least one copy is available for checkout."""
        return self.available_copies > 0

    def borrow_copy(self) -> bool:
        """Decrements available copies count upon checkout."""
        if self.is_available():
            self.available_copies -= 1
            return True
        return False

    def return_copy(self) -> bool:
        """Increments available copies count upon check-in."""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False


class Student:
    """Represents a registered student subscriber in the management system."""

    def __init__(
        self,
        student_id: str,
        name: str,
        email: str,
        department: str,
        active: bool = True,
        issued_books: Optional[List[str]] = None,
        total_fines: float = 0.0,
    ):
        self.student_id = student_id
        self.name = name
        self.email = email
        self.department = department
        self.active = active
        self.issued_books = issued_books if issued_books is not None else []
        self.total_fines = total_fines

    def to_dict(self) -> Dict[str, Any]:
        """Serializes student object to dictionary format."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "active": self.active,
            "issued_books": self.issued_books,
            "total_fines": self.total_fines,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Student":
        """Deserializes dictionary payload into a Student object."""
        return Student(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            department=data["department"],
            active=data["active"],
            issued_books=data["issued_books"],
            total_fines=data["total_fines"],
        )

    def can_borrow(self) -> bool:
        """Determines if student is allowed to borrow additional books."""
        return self.active and len(self.issued_books) < MAX_ISSUED_BOOKS_PER_STUDENT


class Transaction:
    """Represents an issue or return transaction record."""

    def __init__(
        self,
        transaction_id: str,
        book_id: str,
        student_id: str,
        issue_date: str,
        due_date: str,
        return_date: Optional[str] = None,
        fine_charged: float = 0.0,
        status: str = "ISSUED",
    ):
        self.transaction_id = transaction_id
        self.book_id = book_id
        self.student_id = student_id
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.fine_charged = fine_charged
        self.status = status  # ISSUED or RETURNED

    def to_dict(self) -> Dict[str, Any]:
        """Serializes transaction object to dictionary format."""
        return {
            "transaction_id": self.transaction_id,
            "book_id": self.book_id,
            "student_id": self.student_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "return_date": self.return_date,
            "fine_charged": self.fine_charged,
            "status": self.status,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Transaction":
        """Deserializes dictionary payload into a Transaction object."""
        return Transaction(
            transaction_id=data["transaction_id"],
            book_id=data["book_id"],
            student_id=data["student_id"],
            issue_date=data["issue_date"],
            due_date=data["due_date"],
            return_date=data.get("return_date"),
            fine_charged=data.get("fine_charged", 0.0),
            status=data.get("status", "ISSUED"),
        )


# ==============================================================================
# SECTION 4: STORAGE MANAGER
# ==============================================================================

class StorageManager:
    """Handles JSON-based persistence layer operations."""

    @staticmethod
    def save_data(filepath: str, data: List[Dict[str, Any]]) -> bool:
        """Saves dictionary data array to JSON file on disk."""
        try:
            ensure_data_directory_exists()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            Logger.error(f"Failed to save data to {filepath}: {str(e)}")
            return False

    @staticmethod
    def load_data(filepath: str) -> List[Dict[str, Any]]:
        """Loads array data from JSON file on disk."""
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            Logger.error(f"Failed to load data from {filepath}: {str(e)}")
            return []


# ==============================================================================
# SECTION 5: SERVICES & BUSINESS LOGIC
# ==============================================================================

class BookService:
    """Business logic for inventory and book record management."""

    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.load_books()

    def load_books(self) -> None:
        """Loads stored books into working memory."""
        data = StorageManager.load_data(BOOKS_FILE)
        self.books = {item["book_id"]: Book.from_dict(item) for item in data}

    def save_books(self) -> bool:
        """Saves books in memory back to file."""
        data = [book.to_dict() for book in self.books.values()]
        return StorageManager.save_data(BOOKS_FILE, data)

    def add_book(self, title: str, author: str, isbn: str, genre: str, copies: int) -> Book:
        """Creates and stores a new book entry."""
        book_id = f"BK-{random.randint(1000, 9999)}"
        new_book = Book(book_id, title, author, isbn, genre, copies, copies)
        self.books[book_id] = new_book
        self.save_books()
        Logger.info(f"Book added: {title} (ID: {book_id})")
        return new_book

    def remove_book(self, book_id: str) -> bool:
        """Deletes a book from inventory if exists."""
        if book_id in self.books:
            deleted_book = self.books.pop(book_id)
            self.save_books()
            Logger.info(f"Book deleted: {deleted_book.title} (ID: {book_id})")
            return True
        return False

    def search_books(self, query: str) -> List[Book]:
        """Searches books matching title, author, or genre."""
        q = query.lower()
        return [
            b for b in self.books.values()
            if q in b.title.lower() or q in b.author.lower() or q in b.genre.lower() or q in b.book_id.lower()
        ]

    def get_book(self, book_id: str) -> Optional[Book]:
        """Retrieves a book by unique ID."""
        return self.books.get(book_id)


class StudentService:
    """Business logic for student membership and records."""

    def __init__(self):
        self.students: Dict[str, Student] = {}
        self.load_students()

    def load_students(self) -> None:
        """Loads students into working memory."""
        data = StorageManager.load_data(STUDENTS_FILE)
        self.students = {item["student_id"]: Student.from_dict(item) for item in data}

    def save_students(self) -> bool:
        """Saves active student records to file."""
        data = [student.to_dict() for student in self.students.values()]
        return StorageManager.save_data(STUDENTS_FILE, data)

    def register_student(self, name: str, email: str, department: str) -> Student:
        """Registers a new student entry."""
        student_id = f"STU-{random.randint(10000, 99999)}"
        student = Student(student_id, name, email, department)
        self.students[student_id] = student
        self.save_students()
        Logger.info(f"Student registered: {name} (ID: {student_id})")
        return student

    def get_student(self, student_id: str) -> Optional[Student]:
        """Fetches student record by ID."""
        return self.students.get(student_id)

    def update_fine(self, student_id: str, amount: float) -> bool:
        """Adds fine balance to student account."""
        student = self.get_student(student_id)
        if student:
            student.total_fines += amount
            self.save_students()
            return True
        return False

    def pay_fine(self, student_id: str, amount: float) -> bool:
        """Deducts fine balance paid by student."""
        student = self.get_student(student_id)
        if student:
            student.total_fines = max(0.0, student.total_fines - amount)
            self.save_students()
            Logger.info(f"Student {student_id} paid fine: ${amount}")
            return True
        return False


class LibraryTransactionService:
    """Coordinates borrowing, returning, fines, and transaction logging."""

    def __init__(self, book_service: BookService, student_service: StudentService):
        self.book_service = book_service
        self.student_service = student_service
        self.transactions: Dict[str, Transaction] = {}
        self.load_transactions()

    def load_transactions(self) -> None:
        """Loads historical transactions into memory."""
        data = StorageManager.load_data(TRANSACTIONS_FILE)
        self.transactions = {item["transaction_id"]: Transaction.from_dict(item) for item in data}

    def save_transactions(self) -> bool:
        """Saves current transaction ledger to disk."""
        data = [tx.to_dict() for tx in self.transactions.values()]
        return StorageManager.save_data(TRANSACTIONS_FILE, data)

    def issue_book(self, book_id: str, student_id: str) -> Optional[Transaction]:
        """Issues a book copy to a student if criteria are met."""
        book = self.book_service.get_book(book_id)
        student = self.student_service.get_student(student_id)

        if not book or not student:
            return None

        if not book.is_available() or not student.can_borrow():
            return None

        now = datetime.now()
        due = now + timedelta(days=DEFAULT_BORROW_DAYS)

        tx_id = f"TXN-{random.randint(100000, 999999)}"
        tx = Transaction(
            transaction_id=tx_id,
            book_id=book_id,
            student_id=student_id,
            issue_date=now.strftime(DATE_FORMAT),
            due_date=due.strftime(DATE_FORMAT),
        )

        book.borrow_copy()
        student.issued_books.append(book_id)

        self.transactions[tx_id] = tx
        self.book_service.save_books()
        self.student_service.save_students()
        self.save_transactions()

        Logger.info(f"Book {book_id} issued to Student {student_id} (TX: {tx_id})")
        return tx

    def return_book(self, transaction_id: str) -> Optional[float]:
        """Processes return of an issued book and calculates fine."""
        tx = self.transactions.get(transaction_id)
        if not tx or tx.status == "RETURNED":
            return None

        book = self.book_service.get_book(tx.book_id)
        student = self.student_service.get_student(tx.student_id)

        if not book or not student:
            return None

        now_str = get_current_timestamp()
        tx.return_date = now_str
        tx.status = "RETURNED"

        overdue_days = calculate_days_overdue(tx.due_date)
        fine = overdue_days * DEFAULT_FINE_PER_DAY
        tx.fine_charged = fine

        if fine > 0:
            student.total_fines += fine

        book.return_copy()
        if tx.book_id in student.issued_books:
            student.issued_books.remove(tx.book_id)

        self.book_service.save_books()
        self.student_service.save_students()
        self.save_transactions()

        Logger.info(f"Book returned for TX {transaction_id}. Fine: ${fine}")
        return fine


# ==============================================================================
# SECTION 6: SAMPLE DATA GENERATOR
# ==============================================================================

class DataGenerator:
    """Utility to seed mock records into system storage."""

    @staticmethod
    def seed_mock_data(book_service: BookService, student_service: StudentService) -> None:
        """Seeds sample books and students if database is empty."""
        if not book_service.books:
            sample_books = [
                ("Clean Code", "Robert C. Martin", "978-0132350884", "Technology", 5),
                ("The Pragmatic Programmer", "Andrew Hunt", "978-0201616224", "Technology", 3),
                ("Introduction to Algorithms", "Thomas H. Cormen", "978-0262033848", "Computer Science", 4),
                ("Design Patterns", "Erich Gamma", "978-0201633610", "Software Engineering", 2),
                ("Artificial Intelligence", "Stuart Russell", "978-0134610993", "AI & ML", 3),
            ]
            for title, author, isbn, genre, copies in sample_books:
                book_service.add_book(title, author, isbn, genre, copies)

        if not student_service.students:
            sample_students = [
                ("Alice Smith", "alice@university.edu", "Computer Science"),
                ("Bob Jones", "bob@university.edu", "Information Technology"),
                ("Charlie Brown", "charlie@university.edu", "Software Engineering"),
            ]
            for name, email, dept in sample_students:
                student_service.register_student(name, email, dept)


# ==============================================================================
# SECTION 7: CLI PRESENTATION LAYER
# ==============================================================================

class ConsoleUI:
    """Command-line interface formatter and interactive loop handler."""

    @staticmethod
    def print_header(title: str) -> None:
        """Prints a styled UI header."""
        print("\n" + "=" * 60)
        print(f" {title.upper().center(58)} ")
        print("=" * 60)

    @staticmethod
    def print_menu(options: List[str]) -> None:
        """Renders list options cleanly."""
        for idx, option in enumerate(options, 1):
            print(f"  [{idx}] {option}")
        print("  [0] Exit / Back")
        print("-" * 60)

    @staticmethod
    def clear_screen() -> None:
        """Clears terminal screen output."""
        os.system("cls" if os.name == "nt" else "clear")


class ApplicationController:
    """Main application orchestrator and controller class."""

    def __init__(self):
        ensure_data_directory_exists()
        self.book_service = BookService()
        self.student_service = StudentService()
        self.tx_service = LibraryTransactionService(self.book_service, self.student_service)
        DataGenerator.seed_mock_data(self.book_service, self.student_service)

    def run(self) -> None:
        """Launches primary application interaction loop."""
        while True:
            ConsoleUI.print_header("Library & Student Management System")
            options = [
                "Manage Books (Inventory)",
                "Manage Students",
                "Issue / Return Books",
                "View Transactions & Fines",
                "System Reports & Analytics",
            ]
            ConsoleUI.print_menu(options)

            choice = input("Select an option (0-5): ").strip()
            if choice == "1":
                self.menu_books()
            elif choice == "2":
                self.menu_students()
            elif choice == "3":
                self.menu_transactions()
            elif choice == "4":
                self.menu_fines()
            elif choice == "5":
                self.menu_reports()
            elif choice == "0":
                print("\nThank you for using the Management System. Goodbye!")
                Logger.info("Application shut down gracefully.")
                sys.exit(0)
            else:
                input("\nInvalid choice! Press Enter to try again...")

    # --- BOOK MANAGEMENT SUBMENU ---
    def menu_books(self) -> None:
        while True:
            ConsoleUI.print_header("Book Inventory Management")
            options = [
                "List All Books",
                "Add New Book",
                "Search Book",
                "Remove Book",
            ]
            ConsoleUI.print_menu(options)
            choice = input("Select option: ").strip()

            if choice == "1":
                ConsoleUI.print_header("Inventory Records")
                for b in self.book_service.books.values():
                    print(
                        f"ID: {b.book_id} | Title: {b.title} | Author: {b.author} | Copies: {b.available_copies}/{b.total_copies}"
                    )
                input("\nPress Enter to continue...")
            elif choice == "2":
                title = input("Enter Title: ")
                author = input("Enter Author: ")
                isbn = input("Enter ISBN: ")
                genre = input("Enter Genre: ")
                try:
                    copies = int(input("Enter Total Copies: "))
                    self.book_service.add_book(title, author, isbn, genre, copies)
                    print("\nBook added successfully!")
                except ValueError:
                    print("\nInvalid integer entered!")
                input("\nPress Enter to continue...")
            elif choice == "3":
                query = input("Enter keyword (Title/Author/Genre/ID): ")
                results = self.book_service.search_books(query)
                print(f"\nFound {len(results)} matches:")
                for b in results:
                    print(f"ID: {b.book_id} | {b.title} by {b.author}")
                input("\nPress Enter to continue...")
            elif choice == "4":
                book_id = input("Enter Book ID to remove: ")
                if self.book_service.remove_book(book_id):
                    print("\nBook removed successfully.")
                else:
                    print("\nBook ID not found.")
                input("\nPress Enter to continue...")
            elif choice == "0":
                break

    # --- STUDENT MANAGEMENT SUBMENU ---
    def menu_students(self) -> None:
        while True:
            ConsoleUI.print_header("Student Directory Management")
            options = ["List All Students", "Register Student", "View Student Profile"]
            ConsoleUI.print_menu(options)
            choice = input("Select option: ").strip()

            if choice == "1":
                ConsoleUI.print_header("Student Directory")
                for s in self.student_service.students.values():
                    print(f"ID: {s.student_id} | Name: {s.name} | Dept: {s.department} | Fine: ${s.total_fines:.2f}")
                input("\nPress Enter to continue...")
            elif choice == "2":
                name = input("Enter Full Name: ")
                email = input("Enter Email Address: ")
                dept = input("Enter Department: ")
                s = self.student_service.register_student(name, email, dept)
                print(f"\nRegistered successfully! Assigned ID: {s.student_id}")
                input("\nPress Enter to continue...")
            elif choice == "3":
                sid = input("Enter Student ID: ")
                s = self.student_service.get_student(sid)
                if s:
                    print(f"\nID: {s.student_id}\nName: {s.name}\nEmail: {s.email}\nDept: {s.department}")
                    print(f"Issued Books: {', '.join(s.issued_books) if s.issued_books else 'None'}")
                    print(f"Pending Fines: ${s.total_fines:.2f}")
                else:
                    print("\nStudent ID not found.")
                input("\nPress Enter to continue...")
            elif choice == "0":
                break

    # --- TRANSACTION SUBMENU ---
    def menu_transactions(self) -> None:
        while True:
            ConsoleUI.print_header("Circulation & Issue Desk")
            options = ["Issue Book", "Return Book", "View Active Issues"]
            ConsoleUI.print_menu(options)
            choice = input("Select option: ").strip()

            if choice == "1":
                sid = input("Enter Student ID: ")
                bid = input("Enter Book ID: ")
                tx = self.tx_service.issue_book(bid, sid)
                if tx:
                    print(f"\nSuccess! Issued TX ID: {tx.transaction_id}")
                    print(f"Due Date: {tx.due_date}")
                else:
                    print("\nIssue failed. Check stock availability or student eligibility.")
                input("\nPress Enter to continue...")
            elif choice == "2":
                tx_id = input("Enter Transaction ID: ")
                fine = self.tx_service.return_book(tx_id)
                if fine is not None:
                    print(f"\nBook returned successfully! Assessed Fine: ${fine:.2f}")
                else:
                    print("\nInvalid transaction ID or book already returned.")
                input("\nPress Enter to continue...")
            elif choice == "3":
                ConsoleUI.print_header("Active Book Loans")
                active = [t for t in self.tx_service.transactions.values() if t.status == "ISSUED"]
                for t in active:
                    print(f"TX: {t.transaction_id} | Student: {t.student_id} | Book: {t.book_id} | Due: {t.due_date}")
                input("\nPress Enter to continue...")
            elif choice == "0":
                break

    # --- FINES MANAGEMENT SUBMENU ---
    def menu_fines(self) -> None:
        while True:
            ConsoleUI.print_header("Fines & Collections Management")
            options = ["View Student Fine Balance", "Collect Fine Payment"]
            ConsoleUI.print_menu(options)
            choice = input("Select option: ").strip()

            if choice == "1":
                sid = input("Enter Student ID: ")
                s = self.student_service.get_student(sid)
                if s:
                    print(f"\nStudent: {s.name} | Total Fines Outstanding: ${s.total_fines:.2f}")
                else:
                    print("\nStudent not found.")
                input("\nPress Enter to continue...")
            elif choice == "2":
                sid = input("Enter Student ID: ")
                s = self.student_service.get_student(sid)
                if s and s.total_fines > 0:
                    print(f"Current fine balance: ${s.total_fines:.2f}")
                    try:
                        amt = float(input("Enter payment amount ($): "))
                        self.student_service.pay_fine(sid, amt)
                        print("\nPayment recorded successfully!")
                    except ValueError:
                        print("\nInvalid amount format.")
                else:
                    print("\nStudent has no outstanding fines or ID is invalid.")
                input("\nPress Enter to continue...")
            elif choice == "0":
                break

    # --- REPORTS & ANALYTICS ---
    def menu_reports(self) -> None:
        ConsoleUI.print_header("Library Analytics & Summary Report")
        total_books = len(self.book_service.books)
        total_students = len(self.student_service.students)
        total_tx = len(self.tx_service.transactions)
        active_loans = sum(1 for t in self.tx_service.transactions.values() if t.status == "ISSUED")
        total_fines_unpaid = sum(s.total_fines for s in self.student_service.students.values())

        print(f" Total Registered Books:     {total_books}")
        print(f" Total Registered Students:  {total_students}")
        print(f" Total Lifetime Transactions: {total_tx}")
        print(f" Current Active Book Loans:   {active_loans}")
        print(f" Outstanding Fines Balance:  ${total_fines_unpaid:.2f}")
        input("\nPress Enter to return...")


# ==============================================================================
# SECTION 8: ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    app = ApplicationController()
    app.run()
