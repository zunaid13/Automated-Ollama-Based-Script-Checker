def valid(task,solt,ass,con):
    for(t1,t2) in con :
        if t2== task and t2 in ass and ass [t2]==solt:
            return False
        if t2== task and t1 in ass and ass [t1]==solt:
            return False
        return True
    
    def backtrak (task,solt,con,ass={}):
        if len(ass)== len(t):
            return ass
        t = [t for t in task if t not in ass][0]

        for solt in solt :
            if is_valid(task,solt,ass,con):
                ass[task]=solt
                result =  backtrak (task,solt,con,ass)
                if result:
                    return result
                del ass[tasks]

                return None
            
tasks = ['T1,'T2,'T3']
solts = ['Morning,'Evening']
con = [('T1,''T2,'),
       ('T2,'T3')
       ]

result =backtrak(task,solt,con)
 if result:
print("ass Found")
for t in result:
    print(task,"->",result[task])
   
else:
    print("ass Found")



