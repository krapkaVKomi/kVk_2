filename = input()
name_add = ''
flag = True
for i in reversed(filename):
    if i == '.':
        flag = False
    if flag == True:
       name_add += i
new_name = '.'
for i in reversed(name_add):
    new_name += i

print(new_name)