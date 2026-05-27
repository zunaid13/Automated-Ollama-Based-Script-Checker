def is_valid(task, slot, assignmnet, conflicts):
    for (t1, t2) in conflicts:
        if t1 == task and t2 in assignmnet[t2] == slot:
            return False
        if t2 == task and t1 in assignmnet and assignmnet[t1] == slot:
            return False
        return True
    

def backtract(task, slots, conflicts, assignmnet, index):
    if index == len(task):
        return assignmnet
    
    task = task[index]

    for slot in slots:
        if is_valid(task, slot, assignmnet, conflicts):
            assignmnet[task] = slot

            result = backtract(task, slots, conflicts, assignmnet, index+1)

            if result:
                return result
            

            del assignmnet[task]

        return None
    

if __name__ == "__main__":
    print('=== Task scheduling (Backtracking) ===')
    n = int(input('Number of tasks: '))
    tasks = []
    for _ in range(n):
        tasks.append(input('Task name: '))

    m = int(input('Number of slots: '))
    slots =  []
    for _ in range(m):
        slots.append(input('Task name: '))

    c = int(input('Number of conflicts: '))
    conflicts = []
    for _ in range(c):
        t1 = input('Task1')
        t2 = input('Task2')
        conflicts.append((t1, t2))

    result = backtract(tasks, slots, conflicts, {}, 0)

    if result:
        print('Assignmnet found')
        for t in result:
            print(f"{t}-> {result[t]}")
        else:
            print('No Assignmnet found')


    
