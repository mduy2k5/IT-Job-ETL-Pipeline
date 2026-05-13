from .base_transformer import BaseTransformer

class WebBTransformer(BaseTransformer):

    def clean(self):
        self.df['salary'] = self.df['salary'].str.replace('₫', '').str.strip()
        return self.df

    def normalize(self):
        self.df['source'] = 'webb'
        return self.df