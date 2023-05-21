import grammar

def tokenize(x: str):
  for c in x:
    if not c.isspace():
      yield c

  yield grammar.END_MARKER