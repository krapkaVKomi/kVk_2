filename = input()
name_add = ''
flag = True
for i in reversed(filename):
    if i == '.':
        flag = False
    if flag == False:
       name_add += i

print(name_add)