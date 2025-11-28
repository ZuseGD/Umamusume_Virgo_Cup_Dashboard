# data_manager.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from virgo_utils import load_data, parse_uma_details

class DataLoaderStrategy(ABC):
    """Abstract Base Class for loading match data"""
    @abstractmethod
    def load_matches(self, config):
        pass

    @abstractmethod
    def load_ocr(self, config):
        pass

class PrelimsLoader(DataLoaderStrategy):
    """Handles the standard Round 1 & 2 Data (Existing Logic)"""
    def load_matches(self, config):
        # Re-use your existing sturdy loader from virgo_utils
        df, team_df = load_data(config['sheet_url'])
        return df, team_df

    def load_ocr(self, config):
        # Load standard prelims parquet
        return pd.read_parquet(config['parquet_file'])

class FinalsLoader(DataLoaderStrategy):
    """Handles the Finals Data (New Wide Format)"""
    def load_matches(self, config):
        csv_path = config.get('finals_csv')
        if not csv_path: return pd.DataFrame(), pd.DataFrame()
        
        raw_df = pd.read_csv(csv_path)
        
        # 1. Normalize Columns
        # Finals CSV is 'Wide' (Uma 1, Uma 2, Uma 3 in one row). 
        # We must melt it to 'Long' format to match the dashboard structure.
        
        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown'))
            group = str(row.get('CM Group', 'Unknown'))
            result = str(row.get('Finals race result', 'Unknown'))
            
            # Did they win? (1st Place)
            is_win = 1 if result == '1st' else 0
            
            # Loop through the 3 slots
            for i in range(1, 4):
                uma_name = row.get(f'Own Team - Uma {i}')
                style = row.get(f'Own team - Uma {i} - Running Style')
                
                if pd.notna(uma_name):
                    processed_rows.append({
                        'Clean_IGN': ign,
                        'Clean_Group': group,
                        'Clean_Uma': parse_uma_details(pd.Series([uma_name]))[0], # Normalize name
                        'Clean_Style': style,
                        'Finals_Result': result,
                        'Calculated_WinRate': is_win * 100, # In finals, 1st = 100% WR context
                        'Clean_Races': 1,
                        'Clean_Wins': is_win
                    })
                    
        df = pd.DataFrame(processed_rows)
        
        # Create Team DF (Group by Player)
        team_df = df.groupby(['Clean_IGN', 'Clean_Group', 'Finals_Result']).agg({
            'Clean_Uma': list,
            'Clean_Style': list,
            'Calculated_WinRate': 'max' # If anyone won, the team won
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(sorted([str(i) for i in x])))
        
        return df, team_df

    def load_ocr(self, config):
        return pd.read_parquet(config['finals_parquet'])

# Factory to get the right loader
def get_data_loader(mode: str) -> DataLoaderStrategy:
    if mode == "Finals":
        return FinalsLoader()
    return PrelimsLoader()