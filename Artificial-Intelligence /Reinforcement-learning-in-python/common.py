import numpy as np
import matplotlib.pyplot as plt

"""Environment"""
class Grid: 
  def __init__(self, width, height, start):
    self.width = width
    self.height = height
    self.i = start[0] # start is a tuple of 2 integers
    self.j = start[1]
    
  def set(self, rewards, actions):
    """actions enumerate all possible actions that can take you to new state.
       actions should be a dict of: (i, j): A (row, col): list of possible actions
       rewards should be a dict of: (i, j): r (row, col): reward
    """
    self.rewards = rewards
    self.actions = actions
    
  def set_state(self, s):
    """Useful for various algorithms we will use. For example, iterative policy evaluation
    requires looping through all the states, and then doing an action to get to the next
    state. In order to know what the next state is, we have to put the agent into that 
    state, do the action, and then determine the next state. We do not automatically have
    a master list of state transitions, we must figure them out by playing the game."""
    self.i = s[0]
    self.j = s[1]
    
  def current_state(self):
    "Returns current (i,j) position of agent."
    return (self.i, self.j)
  
  def is_terminal(self, s):
    """Returns true if s is terminal state, false if not. Easy way to check this is to see
    if the state is in the action dictionary. If you can do an action from the state, then
    you can transition to a different state, and hence your state is not terminal."""
    return s not in self.actions
  
  def move(self, action):
    """Checks if action is in actions dictionary. If not, we are not able to do this move,
    so we simply stay in same position."""
    if action in self.actions[(self.i, self.j)]:
      if action == 'U':
        self.i -= 1
      elif action == 'D':
        self.i += 1
      elif action == 'R':
        self.j += 1
      elif action == 'L':
        self.j -= 1
    # Return reward (if any, default is 0)
    return self.rewards.get((self.i, self.j), 0)
  
  def undo_move(self, action):
    """Pass in the action you just took, and the environment will undo it. 
    Ex -> Just went up, it will move you back down."""
    if action == 'U':
      self.i += 1
    elif action == 'D':
      self.i -= 1
    elif action == 'R':
      self.j -= 1
    elif action == 'L':
      self.j += 1
    # Raise an exception if we arrive somewhere we shouldn't be -> Should never happen
    assert(self.current_state() in self.all_states())
    
  def game_over(self):
    "Returns true if game over, false otherwise. Only need to check if in terminal state."
    return (self.i, self.j) not in self.actions
  
  def all_states(self):
    """We can calculate all of the states simply by enumerating all of the states from 
    which we can take an action (which don't include terminal states), and all of the 
    states that return a reward (which do include terminal states). Since there may be
    some of the same states in both actions and rewards, we cast it to a set. This also
    makes the data structure O(1) for search."""
    return set(self.actions.keys()) | set(self.rewards.keys())
  
def standard_grid():
  """Returns standard grid. This is a grid that has the structure shown in section 4.
  All of the actions are defined such that we can move within the grid, but never off
  of it. We also cannot walk into the wall, nor out of the terminal state. Upper left
  is defined to be (0,0). We define rewards for arriving at each state. The grid looks
  like:
      .  .  .  1
      .  x  . -1
      s  .  .  .
  * x means you can't go there
  * s means start position
  * number means reward at that state
  """
  g = Grid(3, 4, (2, 0))
  rewards = {(0, 3): 1, (1, 3): -1}
  actions = {
    (0, 0): ('D', 'R'),
    (0, 1): ('L', 'R'),
    (0, 2): ('L', 'D', 'R'),
    (1, 0): ('U', 'D'),
    (1, 2): ('U', 'D', 'R'),
    (2, 0): ('U', 'R'),
    (2, 1): ('L', 'R'),
    (2, 2): ('L', 'R', 'U'),
    (2, 3): ('L', 'U'),
  }
  g.set(rewards, actions)
  return g

def negative_grid(step_cost=-0.1):
  """Here we want to penalize each move. This is done to prevent a robot from moving 
  randomly to solve the maze. If you only gave it a reward for solving the maze, then it
  would never learn anything beyond a random strategy. We know that we can incentivize
  the robot to solve the maze more efficiently by giving it a negative reward for each
  step taken. That is what we are doing here-incentivizing the robot to solve the maze 
  efficiently, rather than moving randomly until it reaches the goal."""
  g = standard_grid()
  g.rewards.update({
    (0, 0): step_cost,
    (0, 1): step_cost,
    (0, 2): step_cost,
    (1, 0): step_cost,
    (1, 2): step_cost,
    (2, 0): step_cost,
    (2, 1): step_cost,
    (2, 2): step_cost,
    (2, 3): step_cost,
  })
  return g

"""Functions to help us visualize policies and values."""
def print_values(V, g): 
  """Takes in values dictionary and grid, draws grid, and in each position it prints
  the value. """
  for i in range(g.width):
    print("---------------------------")
    for j in range(g.height):
      v = V.get((i,j), 0)
      if v >= 0:
        print(" %.2f|" % v, end="")
      else:
        print("%.2f|" % v, end="") # -ve sign takes up an extra space
    print("")
    
def print_policy(P, g):
  """Takes in policy and grid, draws grid, and in each position it prints
  the action from the policy. Note, this will only work for deterministic policies, 
  since we can't print more than 1 thing per location."""
  for i in range(g.width):
    print("---------------------------")
    for j in range(g.height):
      a = P.get((i, j), ' ')
      print("  %s  |" % a, end="")
    print("")