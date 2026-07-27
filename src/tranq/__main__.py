"""Entry point for python -m tranq or the 'tranq' command."""
import argparse

def main():
    parser = argparse.ArgumentParser(description="tranq - Calm error handling for Python.")
    parser.add_argument("--version", action="version", version="tranq 0.2.1")
    parser.parse_args()
    version="tranq 0.2.7"
    print("tranq v0.2.7 - Calm error handling with advanced features.")
    print("Use @tranq.handle(...) or 'with tranq.retry(...):' in your code.")

if __name__ == "__main__":
    main()
