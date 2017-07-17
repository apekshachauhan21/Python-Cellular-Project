import numpy as np
from random import randrange, uniform,getrandbits,randint,seed
import math
import time

#start timer
start=time.time()

#initializes 4000000 shadowing values and translates that into 2*2 Matrix.
shadow_value=np.random.normal(0,2,4000000).reshape((2000,2000))


#function returns the shadow value depending on the location of the User. 
def shadow_value_computation(x,y):
    x1=str(int(x))
    y1=str(int(y))
    x_new=int(x1[:len(x1)-1]+'0')
    y_new=int(y1[:len(y1)-1]+'0')
    x=x_new+10000
    y=y_new+10000
    x_index=x/10
    y_index=y/10
    shadow=shadow_value[int(x_index)][int(y_index)]
    return shadow                 

#Base Station Parameter
BS_Height_m = 50
BS_Maximum_Transmitter_Power_watt=15.85
BS_Maximum_Transmitter_Power_dBm = 42
BS_Line_Connector_Losses_dbm=2.1
BS_Antenna_Gain_dB=12.1
BS_Carrier_frequency=1900
BS_x=0
BS_y=0
BS_radius_operation=10
EIRP = 52

#CDMA System and Equipment properties
CD_Carrier_BW=1.25
CD_BitRate = 12.5
Processor_Gain_dB=20
Noise_Level_dbm=-110
Required_SINR_dB=6
Minimum_Pilot_RSL_dbm=-107
Number_Traffic_Channel=56

#User Properties
U_Call_Arrival_Rate=6
U_Avg_Call_Duration=1
Total_available_Users=1000
User_wants_to_calls=['Yes','No'] # Depending on the probability either of the two values will picked from the list
call_prob = [1/600,599/600] #Users Probability for calling: 1/600 and not calling 599/600


#EIRP Parameters:
Cd=20
Ci=15
Number_of_Channels_in_use=0
EIRP_current=EIRP

# the function calculates the increment or decrement value for the pilot EIRP depending on what is the current value and the Number of channels in Use
def cal_EIRP_admission_control(EIRP_pilot,Cd,Ci,Number_of_Channels_in_use):
    if(Number_of_Channels_in_use>Cd):
        if(EIRP_pilot>=30.5):
            return -0.5
        else:
            return 0
    if(Number_of_Channels_in_use<Ci):
        if(EIRP_pilot<=51.5):
            return 0.5
        else:
            return 0
    else:
        return 0

#returns the distance of the User from the Base station
def BS_distance_calculation(x,y):
    
    distance = np.sqrt((x-BS_x)*(x-BS_x)+(y-BS_y)*(y-BS_y))
    return distance/1000

#returns the Path loss based on Cost231 for small cities 
def path_loss_calculation(distance):
    
    value=44.9-6.55*np.log10(BS_Height_m)
    PL = 46.3+(33.9*np.log10(BS_Carrier_frequency))-(13.82*np.log10(BS_Height_m))+value*np.log10(distance)
    return PL

#returns the call duration value for a user. Based on exponential distribution
def call_duration_cal():
    
    call_duration=np.random.exponential(U_Avg_Call_Duration)
    return int(60*call_duration)

#returns the RSL for a User to determine if the User can decode the pilot channel to start a call and also to determine SINR value
def RSL_Calculation(EIRP_channel,distance,shadow_value):
    
    path_loss = path_loss_calculation(distance)
    fading = np.random.rayleigh()
    fading_db=20*np.log10(fading)
    RSL = EIRP_channel - path_loss + shadow_value+fading_db
    return RSL

#returns the SINR value for a User at every second when the User is on call to see if the user can maintain the call before the call duration drops to 
def SINR_cal(distance,shadow,Number_active_users,EIRP_channel):

    RSL=RSL_Calculation(EIRP_channel,distance,shadow)
    Signal_level=RSL+Processor_Gain_dB
    if(Number_active_users<2):
        Inteference_linear=0
    else:
        Inteference_level_db=RSL+10*np.log10(Number_active_users-1)
        Inteference_linear=np.power(10,(Inteference_level_db/10))
    Noise_linear =np.power(10,(Noise_Level_dbm/10))
    total_disturbance = Inteference_linear+Noise_linear
    SINR = Signal_level - 10*np.log10(total_disturbance)
    return SINR




##active users
Number_active_users=0 # at the beginning there are no active users
active_user=[] #list maintaining the active users 

##call attempt users
call_attempt=[] #list maintaining the users attempting to make a call


##statistics
Number_call_attempts_no_retry=0
Number_call_attempts_with_retry=0
Number_calls_dropped_SINR=0
Number_calls_blocked_RSL=0
Number_calls_blocked_Channel_Capacity=0
Number_success_calls=0
Number_calls_in_progress=0
Number_failed_calls=0
Current_cell_radius=0

## initialized values 
Total_compute_time=0 #counter for maintaining the  iterations 
n=1 # for printing report
radius = 10000 # cell radius

#the simlation starts 
while(Total_compute_time<=7200):

    Total_compute_time=Total_compute_time+1
        
    #User's willingness to call
    call_attempt_decisions=np.random.choice(User_wants_to_calls,size=Total_available_Users,p=call_prob)
    call_attempt_yes = [x for x in call_attempt_decisions if x != 'No']
    
    # Iterating through all the users who wish to make a call
    for i in range(len(call_attempt_yes)):
        #user attempting to call
        r1 = radius*math.sqrt(np.random.uniform(0,1));
        theta1 = np.random.uniform(0,2*math.pi);

        #assigning position coordinates 
        x = r1*np.cos(theta1);
        y = r1*np.sin(theta1)
        BS_distance = BS_distance_calculation(x,y) #distance from BS
        shadow=shadow_value_computation(x,y) #shadow value for the user position
        
        call_attempt_user=0 # attempt count
        Number_call_attempts_no_retry=Number_call_attempts_no_retry+1
        #Number_call_attempts_with_retry=Number_call_attempts_with_retry+1    
        #RSL value computation and this is user's first attempt at making a call
               
        RSL_value = RSL_Calculation(EIRP_current,BS_distance,shadow)

        if(RSL_value>Minimum_Pilot_RSL_dbm):
            if(Number_Traffic_Channel>0and Number_Traffic_Channel<=56 ):
                ##User can make a call and add to active user list
                Total_available_Users=Total_available_Users-1
                Number_active_users=Number_active_users+1
                Number_Traffic_Channel=Number_Traffic_Channel-1
                SINR_drop_count=0
                call_duration=call_duration_cal()
                active_user.append([x,y,BS_distance,shadow,call_duration,SINR_drop_count])
            else:
                #No channel available
                #User blocked due to channel capacity
                Number_calls_blocked_Channel_Capacity=Number_calls_blocked_Channel_Capacity+1
                
        else:
            #As the User has made only one attempt uptil now
            #Number_call_attempts_no_retry=Number_call_attempts_no_retry+1
            #Number_call_attempts_with_retry=Number_call_attempts_with_retry+1    
            #Add user to call attempting users
            call_attempt_user=call_attempt_user+1
            call_attempt.append([x,y,BS_distance,shadow,call_attempt_user])
            Total_available_Users=Total_available_Users-1

# checking the attempting user's list if any user has cleared RSL or should be blocked due to RSL threshold
    if(len(call_attempt)>0):
        
        count=len(call_attempt)-1
        
        while(count>=0):
             
            #User parameters
            x=call_attempt[count][0]
            y=call_attempt[count][1]
            distance=call_attempt[count][2]
            shadow=call_attempt[count][3]
            attempts=call_attempt[count][4]
            if(attempts==3):
                #remove user from the call attempt list
                #Number of calls blocked due to RSL increased
                call_attempt.remove([x,y,distance,shadow,attempts])
                count=len(call_attempt)-1
                Total_available_Users=Total_available_Users+1
                Number_calls_blocked_RSL=Number_calls_blocked_RSL+1
            else:
                # again attempts to decode pilot channel          
                
                Number_call_attempts_with_retry=Number_call_attempts_with_retry+1
                RSL=RSL_Calculation(EIRP_current,distance,shadow)    
            
                if(RSL>Minimum_Pilot_RSL_dbm):
                   #User cleared the RSL in the next attempt
                   #remove user from the attempting user's list
                    call_attempt.remove([x,y,distance,shadow,attempts])
                    count=len(call_attempt)-1
                    if(Number_Traffic_Channel>=1 and Number_Traffic_Channel<=56 ):
                        #add to active user's list
                        active_user.append([x,y,distance,shadow,call_duration_cal(),0])
                        Number_active_users=Number_active_users+1
                        Number_Traffic_Channel=Number_Traffic_Channel-1
                        
                    else:
                        #User blocked due to channel Capacity
                        Number_calls_blocked_Channel_Capacity=Number_calls_blocked_Channel_Capacity+1
                        Total_available_Users=Total_available_Users+1
                        
                    
                else:
                    #user didn not clear the minimum RSL and the call attempt increased +1
                    call_attempt[count][4]=call_attempt[count][4]+1
                    #Number_call_attempts_with_retry=Number_call_attempts_with_retry+1   
                    count=count-1

#checking for the status of active users    
    if(len(active_user)>0):
        count=len(active_user)-1
      
        while(count>=0):

            #User parameters
            x=active_user[count][0]
            y=active_user[count][1]
            distance=active_user[count][2]
            shadow=active_user[count][3]
            call_duration=active_user[count][4]
            drop_count=active_user[count][5]
            
            if(drop_count==3):
                #User did not clear minimum SINR in 3 attempts
                #remove user from active user's list
                #Number of call due to SINR increased
                active_user.remove([x,y,distance,shadow,call_duration,drop_count])
                count=len(active_user)-1
                Number_active_users=Number_active_users-1
                Total_available_Users=Total_available_Users+1
                Number_Traffic_Channel=Number_Traffic_Channel+1
                Number_calls_dropped_SINR=Number_calls_dropped_SINR+1
            else:
                #test for SINR again
                SINR=SINR_cal(distance,shadow,Number_active_users,EIRP)
     
                if(SINR>Required_SINR_dB):
                    if(call_duration==0):
                        #call ended and user removed from active user list
                        Number_success_calls=Number_success_calls+1
                        active_user.remove([x,y,distance,shadow,call_duration,drop_count])
                        count=len(active_user)-1
                        Number_Traffic_Channel=Number_Traffic_Channel+1
                        Number_active_users=Number_active_users-1
                        Total_available_Users=Total_available_Users+1
                    else:
                        #call duration decreased by a second
                        active_user[count][4]=active_user[count][4]-1
                        count=count-1
            
                else:
                    #SINR drop count for the user incremented
                    active_user[count][5]=active_user[count][5]+1
                    count=count-1

    
            
    Number_calls_in_progress= Number_active_users
    Number_failed_calls=Number_calls_blocked_RSL+Number_calls_dropped_SINR+Number_calls_blocked_Channel_Capacity
    Number_of_Channels_in_use=56-Number_Traffic_Channel
    EIRP_current=EIRP_current+cal_EIRP_admission_control(EIRP_current,Cd,Ci,Number_of_Channels_in_use)    
    if(len(active_user)>0):
        Current_cell_radius=max(map(lambda x: x[2], active_user))

    #printing the statistics
    if(Total_compute_time==n*120):
        print('=========================================================================================')
        print('Total Call attempts with no retry: ',Number_call_attempts_no_retry)
        print('Total Call attempts with retries: ',Number_call_attempts_with_retry)
        print('Total calls dropped due to SINR: ',Number_calls_dropped_SINR)
        print('Total calls blocked due to signal strength: ',Number_calls_blocked_RSL)
        print('Total calls blocked due to channel not available: ',Number_calls_blocked_Channel_Capacity)
        print('Total successful calls: ',Number_success_calls)
        print('Total calls in progress: ',Number_calls_in_progress)
        print('Total failed calls: ',Number_failed_calls)
        print('Current Cell radius: ',Current_cell_radius)
        print('=========================================================================================')
        n=n+1
stop=time.time()#stop time for the modutation
print('Duration:', stop-start)
    
    
                
                
