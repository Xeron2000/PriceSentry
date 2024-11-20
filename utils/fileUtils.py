import os


def loadSymbolsFromFile(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]
