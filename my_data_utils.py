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
