import pandas as pd
import yfinance as yf
import sys
import os
import time

# --- INITIALIZATION & IMPORT HANDLING ---
try:
    from colorama import init, Fore, Style
    # 'convert=True' is crucial for colors to work on standard Windows Command Prompt
    init(autoreset=True, convert=True)
except ImportError:
    # Fallback if colorama is missing: Define dummy classes so code runs without color
    print("NOTE: 'colorama' not installed. Output will be monochrome.")
    
    class DummyColor:
        def __getattr__(self, name): return ""
    
    init = lambda *args, **kwargs: None
    Fore = DummyColor()
    Style = DummyColor()

# --- CONFIGURATION ---
BBG_GREEN = Fore.GREEN + Style.BRIGHT
BBG_WHITE = Fore.WHITE + Style.BRIGHT
BBG_RED = Fore.RED + Style.BRIGHT
BBG_CYAN = Fore.CYAN + Style.BRIGHT
BBG_RESET = Style.RESET_ALL
FILE_NAME = 'sp500.csv'

# Specific ASCII Art requested
ASCII_LOGO = r"""
⠀⠀⠀⣠⠞⢠⠖⠉⠉⠉⢭⣭⣀⡉⣍⠉⠉⠒⠭⣑⠤⡀⠀⠀⠀⠀
⠀⠀⡞⠁⡰⠳⢦⣼⣿⡿⣿⣿⣿⣿⣿⣿⣶⣤⡀⠈⠓⣌⢢⡀⠀⠀
⠀⣸⠁⣰⣵⣾⣿⣿⡿⠹⣿⣿⢿⣟⣿⣿⣿⣿⣿⣦⡀⠈⢣⠱⡀⠀
⠀⢯⢠⣿⠟⣿⣿⣿⡇⠀⣿⠛⣷⢙⣻⢌⣻⠟⣿⣿⣿⣆⠀⢧⢳⠀
⠀⠘⡞⢡⣼⣿⣿⣯⣧⠀⠘⠆⢨⠋⢠⡤⢘⣆⢻⣿⣿⣿⠇⢸⠀⡇
⠀⠀⢱⡼⢟⣿⣿⣿⠋⢑⣄⠀⠈⠢⠤⠔⣺⣏⠀⣿⣿⡏⠀⡼⠀⡇
⠀⠀⠁⠘⢺⣿⣿⣿⣦⣈⣽⠀⠀⢀⡤⠊⢡⣾⠀⠸⣿⢃⡴⠁⡜⠁
⠀⠀⠀⠀⠀⠻⠙⠟⣿⡀⢨⠭⠊⡡⠔⠀⢠⠃⡜⣿⡋⣁⡠⠊⠀⠀
⠀⠀⠀⠀⡰⠉⢓⠀⠈⠳⢌⡳⢄⣀⠤⠒⢁⠞⡼⠙⡄⠀⠀⠀⠀⠀
⠀⠀⣀⠤⣣⣄⢸⠀⠀⠀⠀⠉⠑⠒⠤⢲⣥⠼⣤⣤⣱⡀⠀⠀⠀⠀
⣠⠊⠁⠀⠀⠈⣞⣆⠀⠀⠀⠀⠀⠀⣴⠏⠀⠀⠀⠙⢿⣿⣧⡀⠀⠀
⠄⠈⠉⠉⠙⢦⢻⠚⣄⠀⠀⠀⠀⣼⠃⠀⠀⠀⠀⠀⢸⣿⣿⣧⠀⠀
                   cooljk007
"""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_intro():
    clear_screen()
    # Print the ASCII art in Cyan
    print(BBG_CYAN + ASCII_LOGO)
    print(BBG_GREEN + "=" * 80)
    print(BBG_GREEN + f"||  MARKET SCANNER: INITIALIZING                                              ||")
    print(BBG_GREEN + "=" * 80)
    time.sleep(1) # Brief pause to admire the art

def get_market_data(tickers):
    # Table Header
    # Expanded 'STOCK NAME' slightly to fit longer error messages
    header = f"{'TICKER':<8} | {'STOCK NAME':<30} | {'CLOSE PRICE ($)':<12} | {'DATE':<12}"
    print(BBG_WHITE + header)
    print(BBG_GREEN + "-" * 85)

    success_count = 0
    total_scanned = len(tickers)

    for ticker in tickers:
        try:
            # 1. Initialize Ticker
            stock = yf.Ticker(ticker)
            
            # 2. Get Recent History (1 day)
            # Removed 'progress=False' to fix compatibility with older yfinance versions
            hist = stock.history(period="1d")
            
            if hist.empty:
                raise ValueError("No history found")

            # Extract Data
            last_close = hist['Close'].iloc[-1]
            last_date = hist.index[-1].strftime('%Y-%m-%d')
            
            # 3. Get Stock Name
            try:
                # Try fetching fast info first
                stock_name = stock.info.get('shortName', stock.info.get('longName', ticker))
            except:
                stock_name = ticker 
            
            # Truncate name if it's too long
            if len(stock_name) > 28:
                stock_name = stock_name[:25] + "..."

            # 4. Print Row
            price_fmt = f"${last_close:,.2f}"
            print(f"{BBG_GREEN}{ticker:<8} {BBG_WHITE}| {stock_name:<30} | {price_fmt:<12} | {last_date:<12}")
            
            success_count += 1

        except Exception as e:
            # Error Row - Shows the actual error message
            error_msg = str(e) if str(e) else "N/A (Error)"
            # Increased truncation limit to help debug
            if len(error_msg) > 28:
                error_msg = error_msg[:25] + "..."
            
            print(f"{BBG_RED}{ticker:<8} {BBG_WHITE}| {error_msg:<30} | {'---':<12} | {'---':<12}")

    print(BBG_GREEN + "=" * 80)
    print(BBG_WHITE + "SCAN COMPLETE.")
    print(BBG_GREEN + f"Total Tickers Scanned: {total_scanned}")
    print(BBG_GREEN + f"Successfully Retrieved: {success_count}")
    print(BBG_GREEN + "=" * 80)

def load_and_scan(csv_filename):
    print_intro()
    print(BBG_WHITE + "Analyzing file structure...")
    
    # --- LOAD STRATEGY ---
    load_strategies = [
        ('utf-8', 4),  
        ('cp1252', 4), 
        ('utf-8', 0),  
        ('cp1252', 0), 
    ]

    tickers_df = None
    last_error = None

    for i, (encoding, header) in enumerate(load_strategies):
        try:
            tickers_df = pd.read_csv(csv_filename, encoding=encoding, header=header)
            break 
        except Exception as e:
            last_error = e

    if tickers_df is None:
        print(BBG_RED + f"ERROR: Failed to read '{csv_filename}'. Last error: {last_error}")
        return

    # Clean columns
    tickers_df.columns = tickers_df.columns.astype(str).str.strip() 
    possible_cols = ['Symbol', 'Ticker', 'symbol', 'ticker']
    
    ticker_col = next((c for c in possible_cols if c in tickers_df.columns), tickers_df.columns[0])

    try:
        if ticker_col not in tickers_df.columns:
             tickers = tickers_df.iloc[:, 0].astype(str).tolist()
        else:
            tickers = tickers_df[ticker_col].astype(str).tolist()
    except Exception as e:
        print(BBG_RED + f"ERROR: Could not parse ticker column. {e}")
        return

    # Ticker cleaning
    tickers = [t.replace('.', '-').strip() for t in tickers]

    def is_valid_ticker(t):
        # Relaxed filtering so bad tickers show up as errors in the table
        if not t: return False
        if str(t).lower() == 'nan': return False
        if str(t).strip() == '': return False
        return True

    tickers = [t for t in tickers if is_valid_ticker(t)]
    
    # Trigger scan
    if tickers:
        get_market_data(tickers)
    else:
        print(BBG_RED + "No valid tickers found in file.")

# --- EXECUTION ---
if __name__ == "__main__":
    # Check if we are running in a known dummy file scenario
    if not os.path.exists(FILE_NAME):
        # Create dummy for testing
        with open(FILE_NAME, 'w') as f:
            f.write("Symbol\nAAPL\nMSFT\nNVDA")
            
    if os.path.exists(FILE_NAME):
        load_and_scan(FILE_NAME)
    else:
        print(BBG_RED + f"File '{FILE_NAME}' not found.")
