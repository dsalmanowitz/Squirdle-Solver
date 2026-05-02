import pandas as pd
from main import *

class Simulation(Squirdle):
    def __init__(self, game_mode:GameMode=GameMode.CLASSIC):
        super().__init__(game_mode)
    
    def run_game(self, target):
        self.target = self.full_dex.loc[self.full_dex['Name'] == target].iloc[0]
        self.dex = self.full_dex.copy()
        self.guesses = []

        self.running = True
        while self.running:
            self.iterate()
        return self.guesses

    def iterate(self):
        selection = self.guess()
        if selection['Name'] == self.target['Name']:
            self.running = False
            return 0
        feedback = self.calculate_feedback(selection)
        self.filter_dex(feedback)

    def calculate_feedback(self, vals):
        feedback = [None]
        for col in list(self.full_dex)[1:]:
            feedback.append(self.calculate_single_feedback(vals, col))
        return feedback

    def calculate_single_feedback(self, vals, col):
        return self.calculate_type_feedback(vals, col) if 'Type' in col else self.calculate_num_feedback(vals, col)

    def calculate_num_feedback(self, vals, col):
        if self.target[col] < vals[col]:
            return Feedback.DOWN
        elif self.target[col] > vals[col]:
            return Feedback.UP
        elif self.target[col] == vals[col]:
            return Feedback.GREEN
    
    def calculate_type_feedback(self, vals, col):
        if self.target[col] == vals[col]:
            return Feedback.GREEN
        elif vals[col] != self.target['Type1'] and vals[col] != self.target['Type2']:
            return Feedback.RED
        else:
            return Feedback.YELLOW

if __name__ == '__main__':
    mode = GameMode.CLASSIC
    s = Simulation(mode)
    results = pd.DataFrame(columns=['Name', 'Num', 'Guesses'])
    for name in s.full_dex['Name']:
        guesses = s.run_game(name)
        results.loc[len(results)] = [name, len(guesses), '; '.join(guesses)]
        results.to_csv('sim_classic.csv' if mode == GameMode.CLASSIC else 'sim_stats.csv', index=False)

    print('Avg:', results['Num'].mean())
    print('Med:', results['Num'].median())
    print('Max:', results['Num'].max())

    # Classic Results: Avg 3.63, Med 4, Max 6
    # Stats Results: Avg 3.06, Med 3, Max 7