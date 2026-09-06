# backend/test_lakshmi.py
from agents.lakshmi import ask_lakshmi

if __name__ == "__main__":
    result = ask_lakshmi("My credit score is low, what should I do?")
    print("\n--- Lakshmi's response ---")
    print(result["reply"])
    print("\n--- Context used ---")
    print(result["context_used"])