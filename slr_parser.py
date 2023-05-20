import grammar
import pprint
from enum import IntEnum

import tokenizer
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

def dict2d_sync_value(d: dict, d_key1, d_key2, value):
  if d_key1 not in d:
    d[d_key1] = {}
  
  if d_key2 in d[d_key1]:
    if d[d_key1][d_key2] != value:
      raise KeyError("The key already exists with a different value.")
  else:
    d[d_key1][d_key2] = value # shift goto_state_id

def dict2d_get_or_none(d: dict, d_key1, d_key2):
  ans = d.get(d_key1, None)
  return ans.get(d_key2, None) if ans is not None else None

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
  nonterminal: str
  body_len: int

@dataclass(frozen=True)
class SlrActionShift:
  state: int

class SlrParser:
  def __init__(self):
    self.action = {}
    self.goto = {}

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
    self.action = {}
    self.goto = {}

    state_id = 0
    while state_id < len(states):
      state = states[state_id]

      for prod, idx in state.items:
        # If there is a next symbol
        if idx < len(prod.body):
          next_sym = prod.body[idx]

          goto_state_id = list_indexof_or_add(states, state.goto(G, next_sym))

          if next_sym in G.nonterminals:            
            dict2d_sync_value(self.goto, state_id, next_sym, goto_state_id)
          else:
            dict2d_sync_value(self.action, state_id, next_sym, SlrActionShift(goto_state_id))
        
        # Otherwise, there is no next symbol.
        else:
          if prod == axiom:
            dict2d_sync_value(self.action, state_id, grammar.END_MARKER, SlrActionAccept())
          else:
            for sym in G.follow[prod.lhs]:
              dict2d_sync_value(self.action, state_id, sym, SlrActionReduce(prod.lhs, len(prod.body)))

      state_id = state_id + 1

  def parse(self, x):
    stack = [0]
    for token in tokenizer.tokenize(x):
      action = dict2d_get_or_none(self.action, stack[-1], token)
      
      print(action)

      if action is None:
        raise Exception("Parse error.")
      
      if isinstance(action, SlrActionShift):
        stack.append(action.state)

      elif isinstance(action, SlrActionReduce):
        # pop action.body_len states from stack
        stack = stack[:-action.body_len]

        goto = dict2d_get_or_none(self.goto, stack[-1], action.nonterminal)
        if goto is None:
          raise Exception("Parse error.")

        stack.append(goto)

      elif isinstance(action, SlrActionAccept):
        return
      else:
        assert False, f"Bruh {action}"

      

with open('gr.txt', 'r') as f:
  g = grammar.Grammar.parse(f)
  parser = SlrParser()

  parser.set_grammar(g)
  
  pprint.pprint(parser.action)
  pprint.pprint(parser.goto)

  parser.parse("aaaabbbb")