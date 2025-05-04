"""
Project Name: Star Power
File: main.py

Provides a simple command-line interface for key tasks:
1. Rebuild all data files
2. Perform regression analysis
3. Perform survival classification
"""
from analysis.survival_classifier import survival_classifier_main
from processing.star_power import starpower_main


def show_menu():
    print("\n=== Star Power Project Menu ===")
    print("1. Rebuild All Data Files")
    print("2. Perform Regression Analysis")
    print("3. Perform Survival Classifier")
    print("0. Exit")

def main():
    while True:
        show_menu()
        choice = input("Enter your choice (0–3): ").strip()

        if choice == '1':
            print("\n[Running] Rebuilding data files...\n")
            force_starpower_rebuild()

        elif choice == '2':
            print("\n[Running] Regression analysis...\n")
            starpower_main()

        elif choice == '3':
            print("\n[Running] Survival classifier...\n")
            survival_classifier_main()

        elif choice == '0':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 0, 1, 2, or 3.")

if __name__ == "__main__":
    main()
