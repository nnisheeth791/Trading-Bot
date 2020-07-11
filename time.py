
import time
import numpy as np

def fibonacci(n):
    if n <= 1:
        return n
    else:
        return (fibonacci(n - 1) + fibonacci(n - 2))
    
def main():
    num = np.random.randint(1, 25)
    print("%dth fibonacci numer is: %d"%(num, fibonacci(num)))
    


starttime = time.time()
timeout = time.time() + 60*2
while time.time() <= timeout:
    try:
        main()
        time.sleep(5 - ((time.time() - starttime) % 5.0))
    except KeyboardInterrupt:
        print('\n\nKeyboard Exception received. Exiting')
        exit()
        

    
    
    
