
import time
import numpy as np

starttime = time.time()
timeout = time.time() + 60*2
while time.time() <= timeout:
    try:
        main()
        time.sleep(5 - ((time.time() - starttime) % 5.0))
    except KeyboardInterrupt:
        print('\n\nKeyboard Exception received. Exiting')
        exit()
        

    
    
    
