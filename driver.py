import yaml,math,time
from contraption.Lecroy import LecroyWavepro725zi

class LecroySSRL(LecroyWavepro725zi):
    CONFIG="config.yaml"
    V=True
    
    def __init__(self,runNumber=0):
        #Get config
        self.config=LecroySSRL.getConfig()
        self.runNumber=runNumber
        self.runPrefix=r"ssrl\%s"%self.config['runName']
        #Connect to lecroy
        super(LecroySSRL,self).__init__(self.config['ip'])
        self.inst.timeout=5*60*1000
        self.inst.write("STST ALL_DISPLAYED,HDD,AUTO,WRAP,FORMAT,BINARY")
        self.createDir(r"ssrl")
        self.createDir(self.runPrefix)
        #self.local_store_setup("WRAP")
        self.inst.query("*OPC?")
        #Start on motor tigger or beam trigger?
        self.getMotor()

    def createDir(self,name):
        self.inst.write(r'DIR DISK,HDD,ACTION,CREATE,"C:\Users\lecroy\Desktop\%s"'%name)
        self.changeDir(name)
    def changeDir(self,name):
        self.inst.write(r'DIR DISK,HDD,ACTION,SWITCH,"C:\Users\lecroy\Desktop\%s"'%name)
    
        
    #Under the unfortunate cercumtstance that the motor trigger is never recieved
    #This function is run in an attempt to recover the program.
    def motorTriggerMissing(self):
        #TODO: Some way to recover upon a missed motor trigger.
        print("MISSING BEAM!")
        self.getBeam() #Assuming we are late to the beam.

    #Waiting for motor trigger
    def getMotor(self):
        self._armMotorTrigger()
        directory=r"%s\run%d"%(self.runPrefix,self.runNumber)
        self.createDir(directory)
        self.changeDir(directory)
        if self.config['time']['unit'].lower() == 'min':
            sec=int(self.config['time']['motor']*60) #Config time to sec
        else:
            sec=int(self.config['time']['motor'])
                    
        start=time.time()
        print("Will wait %d sec for trigger."%sec)
        done=self.inst.query("ARM;WAIT %d;*OPC?"%sec)
        duration=time.time()-start
        if str(1) in done:
            print("Recieved motor trigger within %.01f seconds."%duration)
            self.getBeam()
        else:
            print("Missed the motor trigger. Waited for %.01f seconds."%duration)
            print("Trigger response: %s"%done)
            self.motorTriggerMissing()

    #Collect waveforms and save to disk
    def getBeam(self,runTime=None):
        if runTime is None:
            if self.config['time']['unit'].lower() == 'min':
                runTime=self.config['time']['beam']*60
            else:
                runTime=self.config['time']['beam']
        self.safePrint("Collecting beam data.")
        start=time.time()
        self._armBeamTrigger()
        events=0
        self.inst.write("STO ALL_DISPLAYED,FILE;")
        while time.time()-start < runTime:
            self.inst.write("ARM;WAIT;")
            self.inst.query("*OPC?")
            events+=1
            if events==10: break
            if events%1000==0:
                duration=time.time()-start
                print("In %.01f seconds we have recorded %d events at a rate of %.01f Hz."%(duration,events,events/duration))
        duration=time.time()-start
        print("Collected %d events in %.01f seconds (%.01f Hz)."%(events,duration,events/duration))
        #self.getMotor()
        
        
    def safePrint(self,text):
        if self.V: print(text)

    def getConfig(filename=CONFIG):
        with open(filename) as f:
            return yaml.load(f.read())
    
    def _armMotorTrigger(self):
        self.safePrint("\nRun #%d"%self.runNumber)
        self.runNumber+=1
        trigger=self.config['trigger']['motor']
        chan=trigger['channel']
        if chan.upper() == "AUX": chan="EX"
        volt=trigger['threshold']
        self.arm_trigger(chan,volt,"POS","AUTO")
        self.safePrint("Trigger armed on Ch%s for %sV"%(chan,volt))
        
    def _armBeamTrigger(self):
        trigger=self.config['trigger']['beam']
        chan=str(trigger['channel'])
        if chan.upper() == "AUX": chan="EX"
        volt=trigger['threshold']
        self.arm_trigger(chan,volt,"NEG","AUTO")
        self.safePrint("Trigger armed on Ch%s for %sV"%(chan,volt))
        self.safePrint("Listening for beam trigger.")

    #Arm the trigger, wait and save waveform to disk
    def _armAndSaveToDisk(self):
        self.inst.write("ARM;WAIT %d;STO ALL_DISPLAYED,FILE;"%self.config['time']['beam'])

if __name__ == '__main__':
    daq=LecroySSRL()
    
