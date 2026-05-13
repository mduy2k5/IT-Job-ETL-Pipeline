from .base_transformer import BaseTransformer
from datetime import datetime, timedelta
import pandas as pd

class WebATransformer(BaseTransformer):
    def clean(self):
        self.df['salary'] = self.df['salary'].str.replace('USD', '').str.strip()
        return self.df

    def normalize(self):
        self.df['source'] = 'weba'
        return self.df
    
    @staticmethod
    def level_split(df):
        def split_level(value):
            # Kiểm tra xem đã là list hay chưa (trước tiên để tránh pd.isna() trên list)
            if isinstance(value, list):
                return value
            
            # Nếu là None hoặc NaN
            if pd.isna(value):
                return None
            
            # Nếu là string thì split
            parts = [p.strip() for p in str(value).split(',')]
            return parts
        
        df['level'] = df['level'].apply(split_level)
        return df
    
    @staticmethod
    def city_province_split(df):
        def split_location(value):
            if pd.isna(value):
                return pd.Series([pd.NA, pd.NA])
            
            parts = value.split(',')
            city = ''
            province = ''
            if len(parts) == 1:
                city = parts[0].strip()
            elif len(parts) == 2:
                city = parts[1].strip()
                province = parts[0].strip()
            else:
                city = parts[len(parts)-1].strip()
                province = parts[0].strip()
            return pd.Series([city, province])
        
        df[['city', 'province']] = df['location'].apply(split_location)
        return df

    def set_day(self):
        def convert_posted_at(value):
            if pd.isna(value):
                return pd.NaT
            
            value = str(value).strip().lower()
            
            # Xử lý "hour ago" / "hours ago" (English)
            if 'hour' in value or 'hours' in value:
                hours = int(value.split()[0])
                return (datetime.now() - timedelta(hours=hours)).date()
            
            # Xử lý "day ago" / "days ago" (English)
            elif 'day'  in value or 'days' in value:
                days = int(value.split()[0])
                return (datetime.now() - timedelta(days=days)).date()
            elif 'minute' in value or 'minutes' in value:
                minutes = int(value.split()[0])
                return (datetime.now() - timedelta(minutes=minutes)).date()
            elif 'just now' in value:
                return datetime.now().date()
            elif 'week' in value or 'weeks' in value:
                weeks = int(value.split()[0])
                return (datetime.now() - timedelta(weeks=weeks)).date()
            

            # Nếu không nhận dạng định dạng, trả về NaT
            return pd.NaT
        
        self.df['posted_at'] = self.df['posted_at'].apply(convert_posted_at)
        return self.df
    
    def get_date_from_timestamp(self, timestamp_col='timestamp'):
        def convert_timestamp(value):
            if pd.isna(value):
                return pd.NaT
            
            try:
                # Nếu là số (Unix timestamp - seconds)
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value).date()
                
                # Nếu là string, cố gắng convert
                value_str = str(value).strip()
                
                # Thử Unix timestamp (seconds)
                try:
                    timestamp = float(value_str)
                    return datetime.fromtimestamp(timestamp).date()
                except ValueError:
                    pass
                
                # Thử parse datetime string (ISO format)
                try:
                    return pd.to_datetime(value_str).date()
                except:
                    pass
                
            except Exception:
                pass
            
            return pd.NaT
        
        if timestamp_col in self.df.columns:
            self.df['posted_at'] = self.df[timestamp_col].apply(convert_timestamp)
        
        return self.df