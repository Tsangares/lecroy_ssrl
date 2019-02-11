import yaml,math,time
from contraption.Lecroy import LecroyWavepro725zi

class LecroySSRL(LecroyWavepro725zi):
    CONFIG="config.yaml"
    LECROY=False
    V=True
    
    def init(self,runNumber=0):
        #Get config
        self.config=self.getConfig()
        self.runNumber=runNumber
        
        #Connect to lecroy
        if LECROY:
            super(LecroySSRL,self).__init__(config['ip'])
            self.inst.timeout(15000)
            self.local_store_setup("FILL")

        #Start on motor tigger or beam trigger?
        self.getMotor()
        
    #Under the unfortunate cercumtstance that the motor trigger is never recieved
    #This function is run in an attempt to recover the program.
    def motorTriggerMissing(self):
        #TODO: Some way to recover upon a missed motor trigger.
        pass

    #Waiting for motor trigger
    def getMotor(self):
        self._armMotorTrigger()
        sec=int(self.conf['time']['signal']*60) #Config time to sec
        
        start=time.time()
        done=self.inst.query("ARM;WAIT %d;*OPC?"%sec)
        duration=time.time()-start
        if done == 1:
            print("Recieved motor trigger within %.01f seconds."%duration)
            self.getBeam()
        else:
            print("Missed the motor trigger. Waited for %.01f seconds."%duration)
            print("Trigger response: %s"%done)
            self.motorTriggerMissing()

    #Collect waveforms and save to disk
    def getBeam(self):
        self.safePrint("Collecting beam data.")
        start=time.time()
        self._armBeamTrigger()
        events=0
        while time.time()-start < self.conf['time']['run']*60:
            self._armAndSaveToDisk()
            events+=1
        duration=time.time()-start
        print("Collected %d events in %.01f seconds (%.01f Hz)."%(events,duration,events/duration))
        self.getMotor()
        
    def safePrint(self,text):
        if V: print(text)

    def getConfig(filename=CONFIG):
        with open(filename) as f:
            return yaml.load(f.read())
    
    def _armMotorTrigger(self):
        trigger=self.config['trigger']['motor']
        self.arm_trigger(conf['channel'],conf['threshold'],"POS","SINGLE")
        safePrint("Waiting for motor trigger. Run #%d"%self.runNumber)
        self.runNumber+=1
        
    def _armBeamTrigger(self):
        conf=self.config['trigger']['beam']
        self.arm_trigger(conf['channel'],conf['threshold'],"NEG","SINGLE")
        self.safePrint("Waiting for beam trigger.")

    #Arm the trigger, wait and save waveform to disk
    def _armAndSaveToDisk(self):
        self.inst.write("ARM;WAIT;STO ALL_DISPLAYED,FILE;")

if __name__ == '__main__':
    daq=LecroySSRL()
    daq.init()
    
