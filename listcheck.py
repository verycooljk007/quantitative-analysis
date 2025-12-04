import pandas as pd
import yfinance as yf
from colorama import init, Fore, Style
import sys
import os

# Initialize Colorama for the Bloomberg aesthetic
init(autoreset=True)

# --- CONFIGURATION ---
BBG_GREEN = Fore.GREEN + Style.BRIGHT
BBG_WHITE = Fore.WHITE + Style.BRIGHT
BBG_RED = Fore.RED + Style.BRIGHT
BBG_RESET = Style.RESET_ALL
FILE_NAME = 'sp500.csv'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_market_data(tickers):
    clear_screen()
    print(BBG_GREEN + "=" * 80)
    print(BBG_GREEN + f"||  MARKET SCANNER: CLOSING DATA                                    ||")
    print(BBG_GREEN + "=" * 80)
    
    # Table Header
    # Formatted to fit Ticker, Name, Price, and Date
    header = f"{'TICKER':<8} | {'STOCK NAME':<25} | {'CLOSE PRICE':<12} | {'DATE':<12}"
    print(BBG_WHITE + header)
    print(BBG_GREEN + "-" * 80)

    success_count = 0
    total_scanned = len(tickers)

    for ticker in tickers:
        try:
            # 1. Initialize Ticker
            stock = yf.Ticker(ticker)
            
            # 2. Get Recent History (1 day) for Closing Price & Date
            hist = stock.history(period="1d")
            
            if hist.empty:
                raise ValueError("No history")

            # Extract Data
            last_close = hist['Close'].iloc[-1]
            last_date = hist.index[-1].strftime('%Y-%m-%d')
            
            # 3. Get Stock Name (Handle missing info gracefully)
            # Note: accessing .info can be slow, we try to get shortName or use Ticker as fallback
            try:
                stock_name = stock.info.get('shortName', stock.info.get('longName', ticker))
            except:
                stock_name = ticker # Fallback if API fails
            
            # Truncate name if it's too long for the table
            if len(stock_name) > 23:
                stock_name = stock_name[:20] + "..."

            # 4. Print Row
            price_fmt = f"${last_close:,.2f}"
            print(f"{BBG_GREEN}{ticker:<8} {BBG_WHITE}| {stock_name:<25} | {price_fmt:<12} | {last_date:<12}")
            
            success_count += 1

        except Exception as e:
            # Error Row
            print(f"{BBG_RED}{ticker:<8} {BBG_WHITE}| {'N/A (Error)':<25} | {'---':<12} | {'---':<12}")

    print(BBG_GREEN + "=" * 80)
    print(BBG_WHITE + "SCAN COMPLETE.")
    print(BBG_GREEN + f"Total Tickers Scanned: {total_scanned}")
    print(BBG_GREEN + f"Successfully Retrieved: {success_count}")
    print(BBG_GREEN + "=" * 80)

def load_and_scan(csv_filename):
    print(BBG_WHITE + "Analyzing file structure...")
    
    # --- YOUR PROVIDED ROBUST LOADING STRATEGY ---
    load_strategies = [
        ('utf-8', 4),  # 1. Common fix for files with metadata (5th line is header)
        ('cp1252', 4), # 2. Fix for encoding + metadata
        ('utf-8', 0),  # 3. Original default header
        ('cp1252', 0), # 4. Original default + encoding fix
    ]

    tickers_df = None
    last_error = None

    for i, (encoding, header) in enumerate(load_strategies):
        try:
            # Silent retry logic, only print if we fail later
            tickers_df = pd.read_csv(csv_filename, encoding=encoding, header=header)
            break # Success!

        except Exception as e:
            last_error = e

    if tickers_df is None:
        print(BBG_RED + f"ERROR: Failed to read '{csv_filename}'. Last error: {last_error}")
        return

    # Clean columns and extract tickers
    tickers_df.columns = tickers_df.columns.astype(str).str.strip() 
    possible_cols = ['Symbol', 'Ticker', 'symbol', 'ticker']
    
    # Try to find a valid column, default to first column if not found
    ticker_col = next((c for c in possible_cols if c in tickers_df.columns), tickers_df.columns[0])

    try:
        # If the column detection defaulted to 0 but the dataframe is empty or weird
        if ticker_col not in tickers_df.columns:
            # Fallback to simple integer indexing if column names are messy
             tickers = tickers_df.iloc[:, 0].astype(str).tolist()
        else:
            tickers = tickers_df[ticker_col].astype(str).tolist()
    except Exception as e:
        print(BBG_RED + f"ERROR: Could not parse ticker column. {e}")
        return

    # Ticker cleaning (yfinance compatibility)
    tickers = [t.replace('.', '-').strip() for t in tickers]

    # --- FIX: Filter out single hyphens, empty strings, and non-alphanumeric tickers ---
    def is_valid_ticker(t):
        if not t: return False  # Empty string
        if len(t) == 1 and not t.isalpha(): return False # Single non-letter character
        if t.isdigit() or t.isspace(): return False # Numeric or just whitespace
        if "nan" in t.lower(): return False # catch numpy NaNs converted to string
        return True

    tickers = [t for t in tickers if is_valid_ticker(t)]
    
    # --- END OF YOUR LOADING STRATEGY ---

    # Trigger the market scan with the clean list
    if tickers:
        get_market_data(tickers)
    else:
        print(BBG_RED + "No valid tickers found in file.")

# --- EXECUTION ---
if __name__ == "__main__":
    if os.path.exists(FILE_NAME):
        load_and_scan(FILE_NAME)
    else:
        print(BBG_RED + f"File '{FILE_NAME}' not found.")
        # Create dummy for testing if needed
        with open(FILE_NAME, 'w') as f:
            f.write("Symbol\nAAPL\nMSFT\nNVDA")
        print(BBG_WHITE + f"Created sample '{FILE_NAME}'. Run again.")
