# From: http://www.boduch.ca/2009/02/python-cpu-usage.html

import time

class CPUsage:
   def __init__(self, interval=0.1, percentage=True):
       self.interval=interval
       self.percentage=percentage
       self.result=self.compute()
      
   def get_time(self):
       stat_file=file("/proc/stat", "r")
       time_list=stat_file.readline().split(" ")[2:6]
       stat_file.close()
       for i in range(len(time_list))  :
           time_list[i]=int(time_list[i])
       return time_list
  
   def delta_time(self):
       x=self.get_time()
       time.sleep(self.interval)
       y=self.get_time()
       for i in range(len(x)):
           y[i]-=x[i]
       return y   

   def compute(self):
       t=self.delta_time()
       if self.percentage:
           result=100-(t[len(t)-1]*100.00/sum(t))
       else:
           result=sum(t)
       return result
  
   def __repr__(self):
       return str(self.result)
  
if __name__ == "__main__":
   print CPUsage()
