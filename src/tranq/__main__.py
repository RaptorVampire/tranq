"""Entry point for python -m tranq or the 'tranq' command."""
import argparse

def main():
    parser = argparse.ArgumentParser(description="tranq - Calm error handling for Python.")
    parser.add_argument("--version", action="version", version="tranq 0.3.0")
    parser.parse_args()
    print("tranq v0.3.0 - Calm error handling with advanced features.")
    print("Use @tranq.handle(...) or 'with tranq.retry(...):' in your code.")

if __name__ == "__main__":
    main()
