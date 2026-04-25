from main import *

class Simulation(Squirdle):
    def __init__(self):
        super().__init__()
    
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
        self.filter_dex(*feedback)

    def calculate_feedback(self, vals):
        feedback = [None,
            self.calculate_num_feedback(vals, 'Generation'),
            self.calculate_type_feedback(vals, 'Type1'),
            self.calculate_type_feedback(vals, 'Type2'),
            self.calculate_num_feedback(vals, 'Height'),
            self.calculate_num_feedback(vals, 'Weight')
        ]
        return feedback

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
    s = Simulation()
    results = pd.DataFrame(columns=['Name', 'Num', 'Guesses'])
    for name in s.full_dex['Name']:
        guesses = s.run_game(name)
        results.loc[len(results)] = [name, len(guesses), '; '.join(guesses)]
        results.to_csv('sim_results.csv', index=False)

    print('Avg:', results['Num'].mean())
    print('Med:', results['Num'].median())
    print('Max:', results['Num'].max())

    # Simulation Results: Avg 3.63, Med 4, Max 6