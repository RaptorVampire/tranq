"""Entry point for python -m tranq."""
import argparse


def main():
    parser = argparse.ArgumentParser(description="tranq - Calm error handling for Python.")
    parser.add_argument("--version", action="version", version="tranq 1.0.0")
    parser.parse_args()
    print("tranq v1.0.0 - Calm error handling with advanced resilience features.")
    print("Use @tranq.handle(...) or 'with tranq.retry(...):' in your code.")


if __name__ == "__main__":
    main()
