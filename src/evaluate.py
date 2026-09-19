import os
import csv
import sys
from typing import List, Dict, Any

# Ensure stdout handles UTF-8 characters (such as currency symbols ₹) on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.decision import evaluate_ticket

DEFAULT_DATA_PATH = os.path.join("data", "tickets.csv")

def run_evaluation(data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    """
    Run evaluation benchmark on the test tickets dataset.
    Compares AI system decisions against expected actions.
    """
    if not os.path.isfile(data_path):
        print(f"Error: Dataset file not found at '{data_path}'")
        sys.exit(1)

    with open(data_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)

    total = len(test_cases)
    correct = 0
    incorrect = 0
    results = []

    print("\n" + "="*80)
    print("RUNNING AI DECISION EVALUATION BENCHMARK")
    print(f"Dataset: {data_path} | Cases: {total}")
    print("="*80)

    for i, case in enumerate(test_cases, start=1):
        ticket_id = case.get("ticket_id", str(i))
        msg = case.get("message", "")
        expected = case.get("expected_action", "").strip().upper()
        expected_src = case.get("expected_source", "").strip()

        prediction = evaluate_ticket(msg)
        pred_action = prediction.action.strip().upper()
        is_match = (pred_action == expected)

        if is_match:
            correct += 1
            status_icon = "PASS"
        else:
            incorrect += 1
            status_icon = "FAIL"

        results.append({
            "id": ticket_id,
            "message": msg,
            "expected": expected,
            "predicted": pred_action,
            "confidence": prediction.confidence,
            "sources": prediction.sources,
            "reason": prediction.reason,
            "match": is_match
        })

        print(f"[{status_icon}] Ticket #{ticket_id}")
        print(f"   Message:   {msg[:75]}..." if len(msg) > 75 else f"   Message:   {msg}")
        print(f"   Expected:  {expected}")
        print(f"   Predicted: {pred_action} (conf: {prediction.confidence:.2f})")
        print(f"   Reason:    {prediction.reason[:90]}...")
        print(f"   Sources:   {prediction.sources}")
        print("-" * 80)

    accuracy_pct = (correct / total * 100) if total > 0 else 0

    print("\n" + "="*40)
    print("EVALUATION SUMMARY REPORT")
    print("="*40)
    print(f"{total} test cases")
    print(f"Correct: {correct}")
    print(f"Incorrect: {incorrect}")
    print(f"Accuracy: {accuracy_pct:.0f}%")
    print("="*40 + "\n")

    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy_pct": accuracy_pct,
        "results": results
    }

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    run_evaluation(path)
