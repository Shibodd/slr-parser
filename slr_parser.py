import grammar
import pprint
from enum import IntEnum

from dataclasses import dataclass

class SlrState:
  items: set[tuple[grammar.Production, int]]

  def __init__(self):
    self.items = set()
  
  def goto(self, G: grammar.Grammar, x: str) -> 'SlrState':
    """ Returns a new state which results by reading x in the current state. """

    ans = SlrState()

    for prod, idx in self.items:
      # If there is no next symbol, or the next symbol is not x
      if idx >= len(prod.body) or prod.body[idx] != x:
        continue

      ans.items.add((prod, idx + 1))

    ans.closure(G)
    return ans

  def closure(self, G: grammar.Grammar):
    """ Extends this state to its closure. """

    old_len = 0

    # Repeat until convergence
    while len(self.items) != old_len:
      old_len = len(self.items)

      for prod, idx in self.items:

        # If there is no next symbol
        if idx >= len(prod.body):
          continue
        
        next_sym = prod.body[idx]
        if next_sym not in G.nonterminals:
          continue
        
        # Add all productions of next_sym as items with idx 0
        for next_sym_prod in (x for x in G.productions if x.lhs == next_sym): # TODO: can surely do better than O(n)
          self.items.add((next_sym_prod, 0))
        
        # If we added anything to the set, the iterator is now invalid.
        # Break out of the for loop and begin again with a new iterator.
        if len(self.items) != old_len:
          break
  
  def __eq__(self, __value: object) -> bool:
    return isinstance(__value, SlrState) and __value.items == self.items

def dict_get_or_add_default(d, key, default):
  if key not in d:
    d[key] = default
  return d[key]

def list_indexof_or_add(list: list, item):
  n = len(list)
  
  for i in range(n):
    if list[i] == item:
      return i

  list.append(item)
  return n


@dataclass(frozen=True)
class SlrActionAccept:
  pass

@dataclass(frozen=True)
class SlrActionReduce:
  production: grammar.Production

@dataclass(frozen=True)
class SlrActionShift:
  state: int

class SlrParser:
  def __init__(self):
    pass

  def set_grammar(self, G: grammar.Grammar):
    G = G.get_augmented_grammar()

    G.compute_first()
    G.compute_follow()

    # Get the only production which was added by the augmented grammar
    axiom = [x for x in G.productions if x.lhs == G.start_symbol][0]

    startState = SlrState()
    startState.items.add((axiom, 0))
    startState.closure(G)

    states = [startState]
    action = {}
    goto = {}

    state_id = 0
    while state_id < len(states):
      state = states[state_id]
      state_id = state_id + 1

      for prod, idx in state.items:  
        # If there is a next symbol
        if idx < len(prod.body):
          next_sym = prod.body[idx]

          goto_state_id = list_indexof_or_add(states, state.goto(G, next_sym))

          if next_sym in G.nonterminals:
            g = dict_get_or_add_default(goto, state_id, {})
            
            if next_sym in g:
              raise Exception("Not an LR1 grammar.")
            
            g[next_sym] = goto_state_id # goto goto_state_id
          else:
            a = dict_get_or_add_default(action, state_id, {}) 
            if next_sym in a:
              raise Exception("Not an LR1 grammar.")
            
            a[next_sym] = SlrActionShift(goto_state_id) # shift goto_state_id
        else:
          pass
          #a = list_get_or_default(action, state_id, {})
        


      








  # An item is a pair (production, parseProgressIdx)


with open('gr.txt', 'r') as f:
  g = grammar.Grammar.parse(f)
  parser = SlrParser()

  parser.set_grammar(g)
  