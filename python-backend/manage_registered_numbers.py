#!/usr/bin/env python3
"""
Script to manage registered numbers in the WhatsApp bridge database
"""

import sqlite3
import json
import sys

def create_registered_numbers_table():
    """Create the registered_numbers table if it doesn't exist"""
    conn = sqlite3.connect('store/messages.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registered_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Registered numbers table created/verified")

def add_registered_number(number):
    """Add a registered number to the database"""
    conn = sqlite3.connect('store/messages.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT OR REPLACE INTO registered_numbers (number) VALUES (?)', (number,))
        conn.commit()
        print(f"✓ Added registered number: {number}")
    except sqlite3.Error as e:
        print(f"✗ Error adding number {number}: {e}")
    finally:
        conn.close()

def remove_registered_number(number):
    """Remove a registered number from the database"""
    conn = sqlite3.connect('store/messages.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM registered_numbers WHERE number = ?', (number,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✓ Removed registered number: {number}")
        else:
            print(f"✗ Number {number} not found")
    except sqlite3.Error as e:
        print(f"✗ Error removing number {number}: {e}")
    finally:
        conn.close()

def list_registered_numbers():
    """List all registered numbers"""
    conn = sqlite3.connect('store/messages.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT number, added_at FROM registered_numbers WHERE is_active = 1 ORDER BY added_at')
        numbers = cursor.fetchall()
        
        if numbers:
            print("\n📱 Registered Numbers:")
            print("-" * 40)
            for i, (number, added_at) in enumerate(numbers, 1):
                print(f"{i}. {number} (added: {added_at})")
        else:
            print("No registered numbers found")
    except sqlite3.Error as e:
        print(f"✗ Error listing numbers: {e}")
    finally:
        conn.close()

def import_from_json(filename):
    """Import registered numbers from a JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            numbers = data.get('registered_numbers', [])
            
            for number in numbers:
                add_registered_number(str(number))
            
            print(f"✓ Imported {len(numbers)} numbers from {filename}")
    except FileNotFoundError:
        print(f"✗ File {filename} not found")
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in {filename}")

def export_to_json(filename):
    """Export registered numbers to a JSON file"""
    conn = sqlite3.connect('store/messages.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT number FROM registered_numbers WHERE is_active = 1')
        numbers = [row[0] for row in cursor.fetchall()]
        
        data = {
            "registered_numbers": numbers,
            "exported_at": "2024-01-15T10:00:00Z"
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Exported {len(numbers)} numbers to {filename}")
    except sqlite3.Error as e:
        print(f"✗ Error exporting numbers: {e}")
    finally:
        conn.close()

def show_help():
    """Show help information"""
    print("""
🔧 WhatsApp Bridge - Registered Numbers Manager

Usage:
  python manage_registered_numbers.py <command> [options]

Commands:
  add <number>           - Add a registered number
  remove <number>        - Remove a registered number
  list                   - List all registered numbers
  import <filename>      - Import numbers from JSON file
  export <filename>      - Export numbers to JSON file
  init                   - Initialize database table

Examples:
  python manage_registered_numbers.py add 919391547257
  python manage_registered_numbers.py remove 9515613538
  python manage_registered_numbers.py list
  python manage_registered_numbers.py import config.json
  python manage_registered_numbers.py export backup.json
  python manage_registered_numbers.py init
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        create_registered_numbers_table()
    
    elif command == "add" and len(sys.argv) >= 3:
        number = sys.argv[2]
        add_registered_number(number)
    
    elif command == "remove" and len(sys.argv) >= 3:
        number = sys.argv[2]
        remove_registered_number(number)
    
    elif command == "list":
        list_registered_numbers()
    
    elif command == "import" and len(sys.argv) >= 3:
        filename = sys.argv[2]
        import_from_json(filename)
    
    elif command == "export" and len(sys.argv) >= 3:
        filename = sys.argv[2]
        export_to_json(filename)
    
    else:
        show_help()

if __name__ == "__main__":
    main() 