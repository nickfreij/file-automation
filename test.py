import sys
from difflib import SequenceMatcher
#print(f"{sys.executable}")

s = SequenceMatcher(None, "jiunlbo fruit", "fruityncacacbsfbsaacabcssaacas.jpg")
tester = s.ratio()
print(f'yo{tester}')

y = 'fruit'
x = '.jpg'

if y in x:
    print('hi shithole')