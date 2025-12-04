import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# --- CONSOLE STYLING (Bloomberg Style) ---
BBG_WHITE = '\033[97m'
BBG_RED = '\033[91m'
BBG_GREEN = '\033[92m'
BBG_YELLOW = '\033[93m'
BBG_BLUE = '\033[94m'
BBG_CYAN = '\033[96m'  # Added for the "Cool" factor
RESET = '\033[0m'

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

def print_intro():
    # Clear screen for a fresh start (optional, works on most terminals)
    # os.system('cls' if os.name == 'nt' else 'clear') 
    # Applied CYAN specifically to the logo
    print(BBG_CYAN + ASCII_LOGO + RESET)

def print_progress_bar(iteration, total, current_task="", length=40):
    """
    Generates a professional progress bar.
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = "█" * filled_length + "-" * (length - filled_length)
    
    # \r returns cursor to start of line, allowing overwrite
    sys.stdout.write(f'\r{BBG_BLUE}|{bar}| {percent}% {RESET} {current_task:<10}')
    sys.stdout.flush()
    
    # Print New Line on Complete
    if iteration == total: 
        print()

def clean_ticker_data(df, ticker_name):
    """
    Performs data cleaning on a single ticker's DataFrame.
    Returns: (Cleaned DataFrame, outlier_count)
    """
    if df.empty:
        return df, 0

    # --- FIX FOR MULTIDIMENSIONAL KEYS ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --- 1. REMOVE BAD ROWS (Zero or Negative Prices) ---
    try:
        mask_valid_price = (df['Close'] > 0) & (df['Open'] > 0)
        df = df.loc[mask_valid_price].copy()
    except Exception:
        return pd.DataFrame(), 0 
    
    # --- 2. FORWARD/BACKWARD FILLING ---
    df = df.ffill().bfill()

    # --- 3. DETECT OUTLIERS (Statistical Approach) ---
    df['Daily_Ret'] = df['Close'].pct_change()
    
    mean_ret = df['Daily_Ret'].mean()
    std_ret = df['Daily_Ret'].std()
    
    if std_ret == 0:
        df['Z_Score'] = 0
    else:
        df['Z_Score'] = (df['Daily_Ret'] - mean_ret) / std_ret

    outlier_threshold = 4.0
    outliers = df[np.abs(df['Z_Score']) > outlier_threshold]
    outlier_count = len(outliers)
    
    df['is_outlier'] = np.abs(df['Z_Score']) > outlier_threshold

    return df, outlier_count

def get_market_data(tickers):
    """
    Downloads and processes data for the list of tickers using a progress bar.
    """
    print(BBG_WHITE + f"\n[SYSTEM] Initializing Batch Download for {len(tickers)} tickers..." + RESET)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 2)
    print(f"[SYSTEM] Date Range: {start_date.date()} -> {end_date.date()}\n")

    valid_data = []
    failed_tickers = []
    total_tickers = len(tickers)

    # --- PROGRESS LOOP ---
    for i, t in enumerate(tickers):
        # Update Progress Bar
        print_progress_bar(i + 1, total_tickers, current_task=f"[{t}]")
        
        try:
            # Download (Silence yfinance output)
            df = yf.download(t, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if df.empty:
                failed_tickers.append(t)
                continue
            
            # Clean
            df_clean, _ = clean_ticker_data(df, t)
            
            if not df_clean.empty:
                df_clean['Ticker'] = t
                valid_data.append(df_clean)
            else:
                failed_tickers.append(t)

        except Exception:
            failed_tickers.append(t)

    print("\n") # Spacing after progress bar

    if valid_data:
        master_df = pd.concat(valid_data)
        cols = ['Ticker'] + [c for c in master_df.columns if c != 'Ticker']
        master_df = master_df[cols]
        
        # --- SUMMARY SECTION ---
        print(BBG_WHITE + "="*60)
        print(f"PIPELINE SUMMARY | SUCCESS: {len(valid_data)} | FAILED: {len(failed_tickers)}")
        print("="*60 + RESET)

        # 2. Daily Returns Analysis (Last available day)
        latest_snapshot = master_df.groupby('Ticker')['Daily_Ret'].last()
        
        # Top Gainers (Descending)
        top_gainers = latest_snapshot.sort_values(ascending=False).head(10)
        
        # Top Losers (Ascending - biggest negative numbers first)
        top_losers = latest_snapshot.sort_values(ascending=True).head(10)

        # --- PRINT TABLES ---
        
        # Print Gainers
        print(f"\n{BBG_GREEN}TOP 10 GAINERS (Last 1 Day){RESET}")
        print("-" * 45)
        print(f"{'TICKER':<10} | {'RETURN (%)':<15}")
        print("-" * 45)
        for ticker, ret in top_gainers.items():
            print(f"{ticker:<10} | {ret*100:>.2f}%")

        # Print Losers
        print(f"\n{BBG_RED}TOP 10 LOSERS (Last 1 Day){RESET}")
        print("-" * 45)
        print(f"{'TICKER':<10} | {'RETURN (%)':<15}")
        print("-" * 45)
        for ticker, ret in top_losers.items():
            print(f"{ticker:<10} | {ret*100:>.2f}%")

        if failed_tickers:
            print(f"\n{BBG_RED}Failed to process: {', '.join(failed_tickers)}{RESET}")

        print(BBG_WHITE + "="*60 + RESET + "\n")
        return master_df
    else:
        print(BBG_RED + "CRITICAL ERROR: No valid data could be downloaded." + RESET)
        return None

# --- YOUR PROVIDED LOADER LOGIC ---
def load_and_scan(csv_filename):
    print_intro()
    print(f"{BBG_WHITE}System ready. Loading targets from: {csv_filename}{RESET}\n")

    # Ask User for Output Preference
    output_mode = None
    while True:
        print(f"{BBG_BLUE}[?] Select Output Mode:{RESET}")
        print("    1. Display results on Screen")
        print("    2. Export results to CSV")
        choice = input(f"{BBG_BLUE}    > {RESET}").strip()
        
        if choice == '1':
            output_mode = 'screen'
            break
        elif choice == '2':
            output_mode = 'csv'
            break
        else:
            print(BBG_RED + "    Invalid selection." + RESET)

    print(f"\n{BBG_WHITE}Parsing file structure...{RESET}")
    
    # --- LOAD STRATEGY ---
    load_strategies = [('utf-8', 4), ('cp1252', 4), ('utf-8', 0), ('cp1252', 0)]
    tickers_df = None

    for i, (encoding, header) in enumerate(load_strategies):
        try:
            tickers_df = pd.read_csv(csv_filename, encoding=encoding, header=header)
            if not tickers_df.empty: break 
        except Exception: pass

    if tickers_df is None:
        print(BBG_RED + f"ERROR: Failed to read '{csv_filename}'." + RESET)
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
    except Exception:
        print(BBG_RED + f"ERROR: Could not parse ticker column." + RESET)
        return

    # Ticker cleaning
    tickers = [t.replace('.', '-').strip() for t in tickers]
    tickers = [t for t in tickers if t and str(t).lower() != 'nan']
    
    if tickers:
        results_df = get_market_data(tickers)
        
        if results_df is not None:
            if output_mode == 'screen':
                print(f"{BBG_WHITE}DATA SNAPSHOT (First 10 Rows){RESET}")
                print(results_df.head(10)) 
                print(f"\nTotal Records: {len(results_df)}")
            
            elif output_mode == 'csv':
                output_file = "cleaned_market_data.csv"
                results_df.to_csv(output_file)
                print(f"{BBG_GREEN}✓ Export Successful: {output_file}{RESET}")
                print(f"Total Records: {len(results_df)}")
    else:
        print(BBG_RED + "No valid tickers found in file." + RESET)

# --- ENTRY POINT ---
if __name__ == "__main__":
    test_file = "sp500.csv"
    if not os.path.exists(test_file):
        with open(test_file, "w") as f:
            f.write("Ticker,Name\nAAPL,Apple\nMSFT,Microsoft\nBAD_TICKER,Fake Co\nGOOG,Google")

    file_input = input("Enter CSV filename (default: sp500.csv): ").strip()
    
    if not file_input:
        file_input = test_file
    elif not file_input.lower().endswith('.csv'):
        file_input += '.csv'
        
    load_and_scan(file_input)
