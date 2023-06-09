import grammar

from my_data_utils import dict2d_get_or_none, dict2d_sync_value, list_indexof_or_add

from tokenizer import tokenize
from dataclasses import dataclass

def production_remove_eps(prod: grammar.Production):
  return grammar.Production(prod.lhs, tuple((x for x in prod.body if x != grammar.EPS)))

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
          self.items.add((production_remove_eps(next_sym_prod), 0))
        
        # If we added anything to the set, the iterator is now invalid.
        # Break out of the for loop and begin again with a new iterator.
        if len(self.items) != old_len:
          break
  
  def __eq__(self, __value: object) -> bool:
    return isinstance(__value, SlrState) and __value.items == self.items


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

class SlrParseException (Exception):
  pass

class SlrParser:
  def __init__(self):
    self.states_sym = {}
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
          self.states_sym[goto_state_id] = next_sym

          if next_sym in G.nonterminals:            
            dict2d_sync_value(self.goto, state_id, next_sym, goto_state_id)

          elif next_sym != grammar.EPS:
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
    tokenizer = tokenize(x)
    def tokenizer_next():
      try:
        return next(tokenizer)
      except StopIteration:
        raise SlrParseException("EOF reached.")

    stack = [0]
    token = tokenizer_next()
    
    # stops on parser accept or on SlrParseError
    while True:
      action = dict2d_get_or_none(self.action, stack[-1], token)
      
      print(f"Token: {token}")
      print(f"Stack: {stack} ({self.states_sym.get(stack[-1], None)})")
      print(f"Action: {action}\n")

      if action is None:
        raise SlrParseException(f"Unexpected symbol {token}.")
      
      if isinstance(action, SlrActionShift):
        stack.append(action.state)
        token = tokenizer_next()

      elif isinstance(action, SlrActionReduce):
        # pop action.body_len states from stack
        if action.body_len > 0:
          stack = stack[:-action.body_len]

        goto = dict2d_get_or_none(self.goto, stack[-1], action.nonterminal)
        if goto is None:
          raise SlrParseException(f"Unexpected symbol {token}.")

        stack.append(goto)

      elif isinstance(action, SlrActionAccept):
        return
      
      else:
        assert False, f"Bruh {action}"


with open('grammars/expr.txt', 'r') as f:
  g = grammar.Grammar.parse(f)
  parser = SlrParser()

  parser.set_grammar(g)

  parser.parse("(123 + 4) + 50 * 2")