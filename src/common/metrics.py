def main():
    FN = int(input("Enter FN: "))
    FP = int(input("Enter FP: "))
    TP = int(input("Enter TP: "))
    TN = int(input("Enter TN: "))

    precision = TP / (TP + FP) if (TP + FP) != 0 else 0.0
    recall    = TP / (TP + FN) if (TP + FN) != 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) != 0 else 0.0
    accuracy  = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) != 0 else 0.0

    print(
        f"Precision: {precision:.4f}\n"
        f"Recall:    {recall:.4f}\n"
        f"F1:        {f1:.4f}\n"
        f"Accuracy:  {accuracy:.4f}"
    )

if __name__ == "__main__":
    main()