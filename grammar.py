import typing
import copy
from dataclasses import dataclass


EPS = 'eps'
END_MARKER = '$'

@dataclass(frozen = True)
class Production:
  lhs: str
  body: tuple[str]

class Grammar:
  start_symbol: str
  productions: list[Production]
  nonterminals: set[str]
  first: dict[str, set]
  follow: dict[str, set]

  def __init__(self):
    self.start_symbol = None
    self.productions = []
    self.nonterminals = set()
    self.first = {}
    self.follow = {}

  def parse(lines: typing.Iterable[str]):
    ans = Grammar()

    for line in lines:
      line = line.strip()
      if len(line) <= 0:
        continue
      
      ans.parse_single_production(line)

    return ans
  
  def parse_single_production(self, line):
    lhs, rhs = line.split('->', 1)
    lhs = lhs.strip()

    if self.start_symbol is None:
      self.start_symbol = lhs

    body = [x for x in map(str.strip, rhs.split(' ')) if len(x) > 0]

    self.productions.append(Production(lhs, tuple(body)))
    self.nonterminals.add(lhs)
  
  def compute_production_first(self, production_body):
    first = set()

    for sym in production_body:
      if sym in self.nonterminals:
        sym_first = self.first[sym]
        first.update(sym_first)
        if EPS not in sym_first:
          break
      else:
        first.add(sym)
        if sym != EPS:
          break

    return first

  def compute_first(self):
    self.first = {
      nonterminal: set()
      for nonterminal in self.nonterminals
    }

    change = True
    while change:
      change = False
      for prod in self.productions:
        lhs_first = self.first[prod.lhs]
        old_len = len(lhs_first)
        
        lhs_first.update(self.compute_production_first(prod.body))

        change = change or len(lhs_first) != old_len
  
  def compute_follow(self):
    self.follow = {
      nonterminal: set()
      for nonterminal in self.nonterminals
    }

    self.follow[self.start_symbol].add(END_MARKER)

    change = True
    while change:
      change = False
      for prod in self.productions:
        # B -> aAb => Follow(A) contains First(b)
        for i in range(len(prod.body) - 1):
          sym = prod.body[i]
          if sym not in self.nonterminals:
            continue

          sym_follow = self.follow[sym]

          next_sym = prod.body[i + 1]

          old_len = len(sym_follow)

          if next_sym in self.nonterminals:
            sym_follow.update(self.first[next_sym])
            if EPS in sym_follow:
              sym_follow.remove(EPS)

          elif next_sym != EPS:
            sym_follow.add(next_sym)
          
          change = change or len(sym_follow) != old_len

        # B -> aA or B -> aAb where eps in First(b) => Follow(A) contains Follow(B)
        for i in reversed(range(len(prod.body))):
          sym = prod.body[i]

          if sym in self.nonterminals:
            sym_follow = self.follow[sym]
            old_len = len(sym_follow)
            
            sym_follow.update(self.follow[prod.lhs])

            change = change or len(sym_follow) != old_len
          elif sym != EPS:
            break

  def get_augmented_grammar(self) -> 'Grammar':
    """ Returns a new grammar, formed by augmenting this grammar. """

    if self.start_symbol == None:
      raise Exception("Cannot augment a grammar which has no start symbol")

    # This crap generates a new nonterminal of the form S'*
    aug_start = "S"
    while aug_start in self.nonterminals:
      aug_start = aug_start + "'"

    g = Grammar()
    g.productions = self.productions
    g.start_symbol = self.start_symbol
    g.nonterminals = self.nonterminals
    
    g.parse_single_production(f"{aug_start} -> {g.start_symbol}")
    g.start_symbol = aug_start
    return g