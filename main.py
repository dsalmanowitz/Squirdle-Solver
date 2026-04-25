from enum import Enum
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz, utils
from re import sub
from typing import Literal

class Feedback(Enum):
    DOWN = -2
    UP = -1
    GREEN = 0
    YELLOW = 1
    RED = 2
    IGNORE = 3

class Squirdle():

    def __init__(self):
        self.full_dex = pd.read_csv('dex.csv').fillna('None')
        self.full_dex.index = self.full_dex['Name']
        self.dex_dict = self.full_dex.to_dict('index')
    
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
            print('Feedback: (Example: palkia up red yellow down green)')
        else:
            selection = self.guess()['Name'] if len(self.dex) else self.guesses[-1]
            print('Answer:', selection, '\n')
            print('Would you like to play again? (y/n)')

        inp = input()
        feedback = self.parse_input(inp, game_over)
        
        if isinstance(feedback, int): # command triggered or error occurred
            self.guesses = self.guesses[:-1]
            return feedback
        self.filter_dex(*feedback)

    def parse_input(self, inp:str, game_over=False):
        args = inp.lower().split()
        # parse commands
        if len(args) < 5:
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
        elif len(args) > 5:
            name = process.extract(' '.join(args[:-5]), pd.read_csv('dex.csv')['Name'], scorer=fuzz.token_sort_ratio, limit=1, processor=self.processor)[0]
            if name[1] < 70:
                print('Unknown Pokemon:', ' '.join(args[:-5]))
                self.guesses = self.guesses[:-1]
                return -1
            name = name[0]
        else:
            name = None

        # parse feedback
        feedback = [name]
        for ix, i in enumerate(args[-5:]):
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
        s = sub(' (?:breed|form|forme|mask|family of|rider|strike style|shield|of many battles|sword|style|mode|cloak)', '', s)
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

    def filter_dex(self, name:str=None, gen:Literal[Feedback.DOWN, Feedback.UP, Feedback.GREEN]=Feedback.IGNORE, 
                   type1:Literal[Feedback.RED, Feedback.YELLOW, Feedback.GREEN]=Feedback.IGNORE, 
                   type2:Literal[Feedback.RED, Feedback.YELLOW, Feedback.GREEN]=Feedback.IGNORE, 
                   height:Literal[Feedback.DOWN, Feedback.UP, Feedback.GREEN]=Feedback.IGNORE, 
                   weight:Literal[Feedback.DOWN, Feedback.UP, Feedback.GREEN]=Feedback.IGNORE):
        '''Filters dex according to feedback from game (ie red, yellow, green, up, down)'''

        if name is not None:
            self.guesses[-1] = name
        self.prev_dex = self.dex.copy()
        values = self.dex_dict[self.guesses[-1]]
        self.dex = self.dex[self.dex['Name'] != values['Name']]
        self.filter_num_col('Generation', values, gen)
        self.filter_type_col('Type1', values, type1)
        self.filter_type_col('Type2', values, type2)
        self.filter_num_col('Height', values, height)
        self.filter_num_col('Weight', values, weight)
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
        return self.dex_dict[selection['Name']]
    
    def generate_scores(self):
        '''Calculates distance scores for each available Pokemon and returns sorted dex'''
        dex = self.dex.copy()
        for col in ['Generation', 'Height', 'Weight']:
            dex['_' + col] = dex[col] / dex[col].median()

        all_types = pd.concat([dex['Type1'], dex['Type2']])
        type_scores = all_types.value_counts(True)
        dex['type_score'] = (type_scores.loc[dex['Type1']] + type_scores.loc[dex['Type2']].values).values
        dex['type_score'] /= dex['type_score'].max()

        dist = dex[['_Generation', '_Height', '_Weight', 'type_score']].values - np.array([1, 1, 1, 1])
        dex['_distance'] = np.linalg.norm(dist, axis=1)
        dex.sort_values('_distance', inplace=True)
        return dex
    
    def print_dex(self, n:int=5):
        print(self.generate_scores()[['Generation', 'Type1', 'Type2', 'Height', 'Weight', '_distance']][:n])

if __name__ == '__main__':
    game = Squirdle()
    game.run_game()