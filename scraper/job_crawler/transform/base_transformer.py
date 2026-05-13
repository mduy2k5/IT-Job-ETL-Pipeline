import pandas as pd

class BaseTransformer:

    def __init__(self, df):
        self.df = df

    def clean(self):
        return self.df

    def normalize(self):
        return self.df
    def set_day(self):
        return self.df

    def run(self):
        self.df = self.clean()
        self.df = self.normalize()
        self.df = self.set_day()
        return self.df