# Squirdle Solver

A Python script to help solve Squirdle puzzles

## Getting Started

### Dependencies

* Python
* pandas
* numpy

### Installing

* Download this repository to a location of your choosing
* Install required libraries if necessary
```
pip install -r requirements.txt
```
### Executing program
* To start, simply navigate to the directory with these files and run the program
* Each iteration, the program will output to terminal its best guess at the answer along with how many possible options are remaining
* After each suggestion, the program expects the user to provide the feedback given by Squirdle.
  * Feedback format: (pokemon) gen t1 t2 height weight
  * Example: Swanna up red yellow down down
  * Note: If user inputted the program's suggested guess, the pokemon can be omitted (based on example: up red yellow down down)
 
Commands include:
* `quit` forces the program to end
* `restart` forces the program to start a new game and guess from the beginning
* `undo` undoes the previous guess
* `list n` lists the n most likely Pokemon remaining
