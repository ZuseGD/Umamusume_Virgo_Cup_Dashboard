# data_manager.py
import pandas as pd
import streamlit as st
from abc import ABC, abstractmethod
from virgo_utils import load_data as legacy_load_data, parse_uma_details, clean_currency_numeric

class DataLoader(ABC):
    """Abstract Base Class for Data Loading Strategies"""
    
    @abstractmethod
    def load_matches(self, config):
        """Returns (match_df, team_df)"""
        pass

    @abstractmethod
    def load_ocr(self, config):
        """Returns ocr_df"""
        pass

    def normalize_ign(self, series):
        """Standardizer for linking OCR to CSV"""
        return series.astype(str).str.lower().str.strip()

class PrelimsLoader(DataLoader):
    """Strategy for Round 1 & 2 (Long Format CSV)"""
    
    def load_matches(self, config):
        # Use existing utility for backward compatibility
        return legacy_load_data(config['sheet_url'])

    def load_ocr(self, config):
        fp = config.get('parquet_file')
        if not fp: return pd.DataFrame()
        df = pd.read_parquet(fp)
        # Normalize for linking
        if 'ign' in df.columns:
            df['Match_IGN'] = self.normalize_ign(df['ign'])
        return df

class FinalsLoader(DataLoader):
    """Strategy for Finals (Wide Format CSV)"""
    
    def load_matches(self, config):
        csv_path = config.get('finals_csv')
        if not csv_path: 
            return pd.DataFrame(), pd.DataFrame()
        
        try:
            raw_df = pd.read_csv(csv_path)
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
        
        # 1. MELT DATA (Wide -> Long)
        # We transform the "Uma 1, Uma 2, Uma 3" columns into a single "Clean_Uma" column
        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown')).strip()
            group = str(row.get('CM Group', 'Unknown'))
            result = str(row.get('Finals race result', 'Unknown'))
            money_str = str(row.get('Total Spent (USD)', '0'))
            
            # Determine Win Logic (1st place = Win)
            is_win = 1 if result == '1st' else 0
            
            # Loop through the 3 Uma slots
            for i in range(1, 4):
                uma_name = row.get(f'Own Team - Uma {i}')
                style = row.get(f'Own team - Uma {i} - Running Style')
                
                if pd.notna(uma_name) and str(uma_name).strip() != "":
                    processed_rows.append({
                        'Clean_IGN': ign,
                        'Match_IGN': ign.lower().strip(), # Pre-compute for joining
                        'Clean_Group': group,
                        'Clean_Uma': parse_uma_details(pd.Series([uma_name]))[0],
                        'Clean_Style': style,
                        'Round': 'Finals',
                        'Day': 'Finals',
                        'Calculated_WinRate': is_win * 100, # Context: Did this team win?
                        'Clean_Races': 1,
                        'Clean_Wins': is_win,
                        'Original_Spent': money_str,
                        'Sort_Money': 0.0 # Placeholder
                    })
                    
        df = pd.DataFrame(processed_rows)
        if df.empty: return df, pd.DataFrame()

        # Clean Money
        df['Sort_Money'] = clean_currency_numeric(df['Original_Spent'])
        df['Display_IGN'] = df['Clean_IGN'] # No anonymization needed for finals usually

        # 2. CREATE TEAM DF (Group by Player)
        # Summarize the trio for the "Teams" tab
        team_df = df.groupby(['Clean_IGN', 'Clean_Group', 'Round', 'Original_Spent', 'Sort_Money']).agg({
            'Clean_Uma': lambda x: sorted(list(x)),
            'Clean_Style': lambda x: list(x),
            'Calculated_WinRate': 'max', # If any horse won, the player won
            'Clean_Races': 'max',
            'Clean_Wins': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
        
        # Filter for valid full teams
        team_df = team_df[team_df['Uma_Count'] == 3]

        return df, team_df

    def load_ocr(self, config):
        fp = config.get('finals_parquet')
        if not fp: return pd.DataFrame()
        
        df = pd.read_parquet(fp)
        
        # Normalize IGN for linking
        if 'ign' in df.columns:
            df['Match_IGN'] = self.normalize_ign(df['ign'])
            
        return df

@st.cache_data(ttl=600)
def get_data(mode, config):
    """Factory Method to get data based on mode"""
    if mode == "Finals":
        loader = FinalsLoader()
    else:
        loader = PrelimsLoader()
        
    matches, teams = loader.load_matches(config)
    ocr = loader.load_ocr(config)
    
    return matches, teams, ocr