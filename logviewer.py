#CLI for the logs created in benchmarking

import os
import json
import pandas as pd
import numpy as np
from rich import print



class Viewer():
    

    def __init__(self):
        
        dirPath = os.getcwd() + '\\logs\\'
        logs = []

        for file in os.listdir(dirPath):
            if file.endswith('.json'):
                logs.append(json.load(open(dirPath + file, 'r')))

        self.logs = pd.DataFrame(logs)

    
    def display(self, model = None, prompt = None):

        logs = []

        for index, row in self.logs.iterrows():
            
            match (model, prompt):
                case (None, None):
                    logs.append(row)

                case (model, None):
                    if row.model == model:
                        logs.append(row)

                case (None, prompt):
                    if row.prompt == prompt:
                        logs.append(row)

                case (model, prompt):
                    if (row.model, row.prompt) == (model, prompt):
                        logs.append(row)

        logs = pd.DataFrame(logs)

        print(logs)

        run = True
        while run:

            print('''
                Enter one of the below options (just the number) to view more:
                  1: View prompts by average duration and token cost
                  2: View models by average duration and token cost
                  3: View model-prompt pairs by average duration and token cost
                  4: Select model-prompt pair to see responses/reasoning
                  0: Exit program
            ''')
            response = input('Enter choice here: ')

            match response:
                case '1':
                    print(logs.groupby('prompt').mean(numeric_only=True))

                    input('Press enter to continue...')

                case '2':
                    print(logs.groupby('model').mean(numeric_only=True))

                    input('Press enter to continue...')

                case '3':
                    print(logs.groupby(['model', 'prompt']).mean(numeric_only=True))

                    input('Press enter to continue...')

                case '4':

                    pairs = logs.groupby(['model', 'prompt'])
                    indexedPairs = []

                    print('Select one of the following pairs by entering its index number')
                    i = 0

                    for pair in pairs:
                        indexedPairs.append(pair)
                        print(f'    {i+1}: [bold blue]{pair[0][0]}[/bold blue], [bold]{pair[0][1]}[/bold]')
                        i += 1

                    select = input('Enter selection here: ')

                    try: 
                        selectedPair = indexedPairs[int(select)-1]
                        print(selectedPair[1][['response', 'thinking']])
                        
                        selectedResponse = input('Enter the index of the response and thinking process that you would like to view: ')

                        row = selectedPair[1].iloc[int(selectedResponse)]

                        print(row, sep='\n\n')

                        print(f'Thinking: \n\n{row['thinking']}\n\nResponse: \n\n{row['response']}')

                        input('Press enter to continue...')

                    except:
                        print('\nInvalid selection\n\n')

                    

                    

                case '0':
                    print('Goodbye!')
                    run = False

                case _:
                    print('\nInvalid response\n\n')


    def run(self, model = 'qwen3:8b'):

        self.display(model = model)




v = Viewer()
v.run()