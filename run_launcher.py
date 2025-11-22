import sys
import os

# This file allows you to run the app by just clicking "Play" in your IDE 
# or by running 'python run_launcher.py' in your terminal.

def main():
    # 1. Check if Streamlit is installed
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        print("❌ Error: Streamlit is not installed.")
        print("   Run this command first:  python -m pip install -r requirements.txt")
        return

    # 2. Define the command (equivalent to 'streamlit run dashboard.py')
    sys.argv = ["streamlit", "run", "virgo_cup.py"]

    # 3. Run it!
    print("🚀 Launching Virgo Cup Dashboard...")
    sys.exit(stcli.main())

if __name__ == '__main__':
    main() 