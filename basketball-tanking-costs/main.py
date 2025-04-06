"""
main.py

This module serves as the main menu interface for various NBA data analysis tools.
Each menu option corresponds to a specific analytical function, such as market size evaluation,
free agency analysis, or SQL schema generation.

The menu operates in a loop and allows the user to select actions until they choose to exit.
"""

from MarketSize import do_market_size_option
from Paths import FILE_PATH_TO_COMPILED_DATA
from TeamRevenueView import plot_team_operating_income
from ShowHighestPlayerImpact import show_highest_player_impact
from Tables import build_sql_schemas_for_tables
from Mining import do_mining_operations
from TheProcess import plot_tanking_team_examples
from TankEffects import perform_tanking_effects_analysis
from FreeAgent import do_free_agent_calculations
from SimpleAttendanceModeling import do_attendance_modeling


def main():
    """
    Launch an interactive command-line interface for NBA data analysis.

    Presents a menu of analytical options and executes user-selected operations.
    Loops until the user chooses to exit.
    """
    while True:
        print("\nNBA Analysis Menu")
        print("1. Show Market Size")
        print("2. Show Team Operating Income Plot")
        print("3. Show Highest Player Impact")
        print("4. Show SQL Schema")
        print("5. Show Tanking Process Plots")
        print("6. Data Mining Operations")
        print("7. Tanking Effects Analysis")
        print("8. Free Agency Analysis")
        print("9. Simple Attendance Modeling")
        print("0. Exit")

        choice = input("Select an option (0–9): ").strip()

        try:
            if choice == "1":
                do_market_size_option()
            elif choice == "2":
                plot_team_operating_income()
            elif choice == "3":
                show_highest_player_impact()
            elif choice == "4":
                db_path = FILE_PATH_TO_COMPILED_DATA + "nba_data.db"
                build_sql_schemas_for_tables(db_path)
            elif choice == "5":
                plot_tanking_team_examples()
            elif choice == "6":
                do_mining_operations()
            elif choice == "7":
                perform_tanking_effects_analysis()
            elif choice == "8":
                do_free_agent_calculations()
            elif choice == "9":
                do_attendance_modeling()
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid input. Please choose a number between 0 and 9.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
