import csv
import random
import logging
import os

logger = logging.getLogger(__name__)

class QuoteManager:
    def __init__(self, csv_path=None):
        self.quotes = []
        self.current_index = -1
        self.csv_path = None
        if csv_path:
            self.load_quotes(csv_path)

    def load_quotes(self, csv_path):
        """Loads quotes from a CSV file. Assumes one quote per line, optionally with an author separated by a semicolon (;)."""
        logger.info(f"Attempting to load quotes from: {csv_path}")
        loaded_quotes = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';') # Use semicolon as delimiter
                for row in reader:
                    if not row: # Skip empty rows
                        continue
                    quote_text = row[0].strip()
                    author = row[1].strip() if len(row) > 1 else "Unknown"
                    if quote_text: # Ensure quote text is not empty
                        loaded_quotes.append({"quote": quote_text, "author": author})

            # Only update if loading was successful
            self.quotes = loaded_quotes
            self.csv_path = csv_path # Store the successfully loaded path
            logger.info(f"Successfully loaded {len(self.quotes)} quotes from {csv_path}")
            self.shuffle_quotes() # Shuffle after loading
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            # Provide default quotes or handle error appropriately
            self.quotes = [{"quote": f"Error: Quote file '{os.path.basename(csv_path)}' not found.", "author": "System"},
                           {"quote": "Please check the path in settings.", "author": "System"}]
            self.csv_path = None # Indicate no valid path loaded
            # Raise the error so the caller (handle_settings_applied) knows it failed
            raise
        except Exception as e:
            logger.error(f"Error loading quotes from {csv_path}: {e}", exc_info=True)
            self.quotes = [{"quote": f"Error loading quotes: {e}", "author": "System"}]
            self.csv_path = None # Indicate no valid path loaded
            # Raise the error
            raise

        if not self.quotes:
            logger.warning(f"CSV file '{csv_path}' loaded successfully but contained no valid quotes.")
            self.quotes = [{"quote": "No valid quotes found in the file.", "author": "System"}]
            # Keep self.csv_path as the loaded path, even if empty

        self.current_index = -1 # Reset index

    def shuffle_quotes(self):
        """Shuffles the loaded quotes randomly."""
        if self.quotes:
            random.shuffle(self.quotes)
            self.current_index = -1 # Reset index after shuffle
        logger.info("Shuffled quotes.")

    def get_next_quote(self):
        """Returns the next quote in the list, cycling back to the start."""
        if not self.quotes:
            return {"quote": "No quotes available.", "author": ""}

        self.current_index += 1
        if self.current_index >= len(self.quotes):
            self.current_index = 0 # Cycle back to the beginning
            # Optionally reshuffle every cycle:
            # self.shuffle_quotes()
            # self.current_index = 0

        return self.quotes[self.current_index]

    def get_prev_quote(self):
        """Returns the previous quote in the list, cycling back to the end."""
        if not self.quotes:
            return {"quote": "No quotes available.", "author": ""}
            
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.quotes) - 1  # Cycle back to the end
            
        return self.quotes[self.current_index]

    def add_quote(self, quote, author):
        """Appends a new quote to the CSV file and the in-memory list."""
        if not self.csv_path or not os.path.exists(os.path.dirname(self.csv_path)):
            logger.error(f"Cannot add quote. CSV path is not set or directory does not exist: {self.csv_path}")
            raise ValueError("Cannot add quote: Valid quote file path is not configured or accessible.")

        logger.info(f"Adding quote to {self.csv_path}: \"{quote}\" - {author}")
        try:
            # Append to the CSV file
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow([quote, author])

            # Add to the in-memory list
            new_quote_entry = {"quote": quote, "author": author}
            self.quotes.append(new_quote_entry)
            logger.info("Quote added successfully.")

        except IOError as e:
            logger.error(f"Failed to write quote to CSV file {self.csv_path}: {e}", exc_info=True)
            raise IOError(f"Failed to save the new quote to the file: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding quote: {e}", exc_info=True)
            raise

# Example Usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Create a dummy quotes.csv for testing
    try:
        with open("quotes.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["The only way to do great work is to love what you do.", "Steve Jobs"])
            writer.writerow(["Strive not to be a success, but rather to be of value.", "Albert Einstein"])
            writer.writerow(["The mind is everything. What you think you become."]) # Quote without author
            writer.writerow(["Your time is limited, don't waste it living someone else's life."]) # Another quote without author
            writer.writerow([]) # Empty row
            writer.writerow(["   Leading and trailing spaces quote   ", "  Test Author  "])
    except Exception as e:
        print(f"Error creating dummy csv: {e}")

    manager = QuoteManager("quotes.csv")
    if manager.quotes:
        print("Loaded quotes:")
        # for q in manager.quotes:
        #     print(f"- \"{q['quote']}\" by {q['author']}")

        print("\nGetting next quotes:")
        for _ in range(len(manager.quotes) + 2): # Cycle through + 2 more
             next_q = manager.get_next_quote()
             print(f"Next: \"{next_q['quote']}\" by {next_q['author']}")

        manager.shuffle_quotes()
        print("\nGetting next quotes after shuffle:")
        for _ in range(len(manager.quotes)):
             next_q = manager.get_next_quote()
             print(f"Next: \"{next_q['quote']}\" by {next_q['author']}")
    else:
        print("No quotes were loaded.")

    # Test file not found
    print("\nTesting non-existent file:")
    try:
        manager_nf = QuoteManager("non_existent.csv")
        print(f"Next: {manager_nf.get_next_quote()}")
    except FileNotFoundError:
        print("Caught FileNotFoundError as expected.")
        # Access the error quotes set within load_quotes
        if hasattr(manager_nf, 'quotes'): # Check if manager object exists
             print(f"Error quote: {manager_nf.get_next_quote()}")

    # Test empty file
    try:
        open("empty.csv", 'w').close()
        print("\nTesting empty file:")
        manager_empty = QuoteManager("empty.csv")
        print(f"Next: {manager_empty.get_next_quote()}")
    except Exception as e:
        print(f"Error creating/testing empty csv: {e}")