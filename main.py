from enum import Enum
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz, utils
from re import sub
from typing import Literal, List

class Feedback(Enum):
    DOWN = -2
    UP = -1
    GREEN = 0
    YELLOW = 1
    RED = 2
    IGNORE = 3

class GameMode(Enum):
    CLASSIC = 0
    STATS = 1

class Squirdle():

    def __init__(self, game_mode:GameMode=GameMode.CLASSIC):
        self.game_mode = game_mode
        file = 'stats.csv' if game_mode == GameMode.STATS else 'dex.csv'
        self.full_dex = pd.read_csv(file).fillna('None')
        self.full_dex.index = self.full_dex['Name']
        self.n_args = 5 + (self.game_mode == GameMode.STATS)
    
    def run_game(self):
        self.dex = self.full_dex.copy()
        self.prev_dex = None
        self.guesses = []

        self.running = True
        while self.running:
            code = self.iterate()
        if code == 1:
            print('Restarting...')
            self.run_game()
        else:
            print('Exiting...')

    def iterate(self):
        print('- - - - - - - - - -')
        if (len(self.guesses)):
            print('Previous Guesses:', ', '.join(self.guesses))
        game_over = len(self.dex) <= 1
        if not game_over:
            selection = self.guess()['Name']
            print('Pokemon Remaining:', len(self.dex))
            print('Best Guess:', selection, '\n')
            example = 'palkia up red yellow down green' if self.game_mode == GameMode.CLASSIC else 'palkia down up up down down green'
            print('Feedback: (Example:', example + ')')
        else:
            selection = self.guess()['Name'] if len(self.dex) else self.guesses[-1]
            print('Answer:', selection, '\n')
            print('Would you like to play again? (y/n)')

        inp = input()
        feedback = self.parse_input(inp, game_over)
        
        if isinstance(feedback, int): # command triggered or error occurred
            self.guesses = self.guesses[:-1]
            return feedback
        self.filter_dex(feedback)

    def parse_input(self, inp:str, game_over=False):
        args = inp.lower().split()
        # parse commands
        if len(args) < self.n_args:
            if args[0] == 'undo':
                self.undo()
            elif args[0] in ['quit', 'stop'] or (args[0] in ['n', 'no'] and game_over):
                self.running = False
            elif args[0] in ['reset', 'restart', 'start'] or (args[0] in ['y', 'yes'] and game_over):
                self.running = False
                return 1
            elif args[0] == 'list':
                self.print_dex(args[1] if len(args) == 2 else 5)
            else:
                print('Unknown Command:', inp)
                return -1
            return 0
        
        # parse name
        elif len(args) > self.n_args:
            name = process.extract(' '.join(args[:-self.n_args]), self.full_dex['Name'], scorer=fuzz.token_sort_ratio, limit=1, processor=self.processor)[0]
            if name[1] < 70:
                print('Unknown Pokemon:', ' '.join(args[:-self.n_args]))
                self.guesses = self.guesses[:-1]
                return -1
            name = name[0]
        else:
            name = None

        # parse feedback
        feedback = [name]
        for i in args[-self.n_args:]:
            if i in ['', '-']:
                feedback.append(Feedback.IGNORE)
            elif i in ['up', 'u', 'high', 'higher', 'above', 'great', 'greater']:
                feedback.append(Feedback.UP)
            elif i in ['down', 'd', 'low', 'lower', 'below', 'less']:
                feedback.append(Feedback.DOWN)
            elif i in ['g', 'green', 'correct', 'right', 'yes', 'good']:
                feedback.append(Feedback.GREEN)
            elif i in ['y', 'yellow', 'other']:
                feedback.append(Feedback.YELLOW)
            elif i in ['r', 'red', 'no', 'wrong', 'incorrect']:
                feedback.append(Feedback.RED)
            else:
                print('Unknown Input:', inp)
                return -1
        return feedback
    
    def processor(self, s: str) -> str:
        s = s.lower()
        if 'nidoran' in s:
            if '♀' in s or s == 'nidoranf':
                s += ' female'
            elif '♂' in s or s == 'nidoranm':
                s += ' male'
        s = sub(' (?:breed|form|forme|mask|family of|rider|strike style|shield|of many battles|sword|style|mode|cloak|face|size|mode)', '', s)
        return utils.default_process(s)

    def undo(self):
        if self.prev_dex is not None:
            self.dex = self.prev_dex
            self.prev_dex = None
            self.guesses = self.guesses[:-1]
            print('Operation Successful')
        else:
            print('Operation Failed: No Previous Saved State')
        return self.prev_dex is not None

    def filter_dex(self, feedback=List[str|Feedback]):
        '''Filters dex according to feedback from game (ie red, yellow, green, up, down)'''
        name = feedback[0]
        feedback = feedback[1:]
        if name is not None:
            self.guesses[-1] = name
        self.prev_dex = self.dex.copy()
        values = self.full_dex.loc[self.guesses[-1]]
        self.dex = self.dex[self.dex['Name'] != values['Name']]

        for col, val in zip(list(self.full_dex)[1:], feedback):
            if 'Type' in col:
                self.filter_type_col(col, values, val)
            else:
                self.filter_num_col(col, values, val)
        return len(self.dex)

    def filter_num_col(self, col:str, vals:dict, feedback:Literal[Feedback.DOWN, Feedback.UP, Feedback.GREEN]):
        val = vals[col]
        if feedback == Feedback.DOWN:
            self.dex = self.dex[self.dex[col] < val]
        elif feedback == Feedback.UP:
            self.dex = self.dex[self.dex[col] > val]
        elif feedback == Feedback.GREEN:
            self.dex = self.dex[self.dex[col] == val]

    def filter_type_col(self, col:str, vals:dict, feedback:Literal[Feedback.RED, Feedback.YELLOW, Feedback.GREEN]):
        val = vals[col]
        if feedback == Feedback.RED:
            self.dex = self.dex[(self.dex['Type1'] != val) & (self.dex['Type2'] != val)]
        elif feedback == Feedback.YELLOW and col == 'Type1':
            self.dex = self.dex[self.dex['Type2'] == val]
        elif feedback == Feedback.YELLOW and col == 'Type2':
            self.dex = self.dex[self.dex['Type1'] == val]
        elif feedback == Feedback.GREEN:
            self.dex = self.dex[self.dex[col] == val]

    def guess(self):
        '''Determines optimal guess based on remaining Pokemon in dex'''

        scores = self.generate_scores()
        selection = scores.iloc[0]
        self.guesses.append(selection['Name'])
        return self.full_dex.loc[selection['Name']]
    
    def generate_scores(self):
        '''Calculates distance scores for each available Pokemon and returns sorted dex'''
        dex = self.dex.copy()

        cols = []
        for col in [col for col in list(self.full_dex)[1:] if 'Type' not in col]:
            dex['_' + col] = dex[col] / dex[col].median()
            cols.append('_' + col)
        
        if self.game_mode == GameMode.CLASSIC:
            all_types = pd.concat([dex['Type1'], dex['Type2']])
            type_scores = all_types.value_counts(True)
            dex['type_score'] = (type_scores.loc[dex['Type1']] + type_scores.loc[dex['Type2']].values).values
            dex['type_score'] /= dex['type_score'].max()
            cols.append('type_score')

        dist = dex[cols].values - np.ones(len(cols))
        dex['_distance'] = np.linalg.norm(dist, axis=1)
        dex.sort_values('_distance', inplace=True)
        return dex
    
    def print_dex(self, n:int=5):
        print(self.generate_scores()[[*list(self.full_dex)[1:], '_distance']][:n])

if __name__ == '__main__':
    game = Squirdle()
    game.run_game()