
from sympy import primerange

n = int(input())
prime = list(primerange(1, n+1))
STDOUT = prime[n]
print(STDOUT)