tasks = ['T1', 'T2', 'T3']
slots = ['Morning', 'Evening']
conflicts = [('T1', 'T2'), ('T2', 'T3')]

def check_valid(task, slot, assigned):
  for (t1, t2) in conflicts:
     if t1 == task and t2 in assigned and assigned[t2] == slot:
       return False
     if t2 == task and t1 in assigned and assigned[t1] == slot:
        return False
  return true

def solve(assigned,pos):
    if pos == len(tasks):
        return assigned

    current_task = tasks[pos]



    for slot in slots:
       if is_valid(current_task, slot, assignmed):
          assigned[current_task] = slot
          answer= solve(assigned,pos+1)
          if answer:


         return answer
          del assigned[current_task]
return None

final_result = backtrack({}, 0)

if final_result:
    print("Valies schedule found: ")
    for t in result:
         print(t, "->", result[t])
else:print("no valid schedule found: ")