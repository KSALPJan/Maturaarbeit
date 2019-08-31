# -*- coding: utf-8 -*
# Jan Aebersold, 2019, Maturaarbeit
#! Informations:
#! -  muss als sudo(Administrator) ausgefuehrt werden
#! -  Die Anschlüsse muessen Serial-Anschlüsse sein!


#Bibliotheken
import RPi.GPIO as GPIO
import datetime
import os
import csv
from picamera import PiCamera
import math
import time

#Anschlüsse
US1TRIG = 9
US1ECHO = 11
US2TRIG = 7
US2ECHO = 8
BUTTONPIN = 26
ROT = 13
GRUN = 19
GELB = 6


#initialcommands
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
camera = PiCamera()
camera.resolution = (3280, 2464)


#Variabeln und Konstanten
etime = 4
emtime = 0

uberhol1 = False
uberhol2 = False

time1 = 0
time2 = 0

car = 0
distanz1 = 0
distanz2 = 0

s1 = []
s2 = []
aktuell = [0,0,0,0,0,0]

winkel = 79
abstand = 0.88 #meter
limit = 300 #zentimeter
anpassung1 = 0
anpassung2 = 0

#KLassen
class SENSOR1:
  #Sensor 1 wird initialisiert
  def __init__(self, US1TRIG,US1ECHO):
    self.US1ECHO = US1ECHO
    self.US1TRIG = US1TRIG
    GPIO.setup(self.US1ECHO, GPIO.IN)
    GPIO.setup(self.US1TRIG, GPIO.OUT)
    GPIO.add_event_detect(self.US1ECHO, GPIO.RISING, self.event_callback)

  #Eventfunktion, die aktiviert wird, sobald der Ultraschallsensor Wellen sendet
  def event_callback(self, channel):
    global uberhol1         #Wahr/Falsch -> wird überholt?
    global emtime           #Zeit, die seit dem Überholstart vergangen ist
    global time1            #Zeitpunkt Überholstart (Geschwindigkeit)
    global distanz1         #errechnete Distanz
    global car              #Anzahl Autos
    global s1               #Zum Errechnen der Durchschnittswerte beim Überholen
    global aktuell          #Fasst s1 und s2 zusammen
    global distanz2         #Distanz des Sensor 2
    global uberhol2         #Erkennt Sensor 2 ein Objekt?

    try:
      #Messung der Zeit der Ultraschallwellen
      starttime = time.time()
      dauer = 0

      while GPIO.input(self.US1ECHO)==1 and dauer < 0.39: #die zweite Bedingung hilft, Errors bei Reichweiteüberschreitung zu verhindern. 
          stoptime = time.time()
          dauer = stoptime - starttime

      distanz1 = round(dauer*17150 + anpassung1) #Berechnung der Distanz

      if distanz1 < 5 or distanz1 > 400: #Beurteilung ob Distanz in Reichweite
        distanz1 = 500

      csvprint.data(distanz1, 0)
      csvprint.data(uberhol1, 0)

      if (time.time()-emtime) >= etime and emtime !=0 and not uberhol2: #Hilft fehler zu Vermeiden
        uberhol1 = False
        led.off(GELB)
        time1 = 0
        emtime = 0

      if distanz1 <= limit and distanz2 > limit and uberhol1 == False:
        csvprint.data('switsch',0)
        time1 = time.time()
        emtime = time.time()
        uberhol1 = True
        led.on(GELB)
        s1.append(distanz1)
      elif distanz1 > limit and uberhol1 and not uberhol2:
	uberhol1 = False
        led.off(GELB)
        del s1[:]
        emtime = 0
      elif distanz1 > limit and uberhol1  and uberhol2:
        uberhol1 = False
        led.off(GELB)
        car = car + 1
        aktuell[0] = car
        aktuell[1] = aver(s1)
        aktuell[2] = min(s1)
        del s1[:]
        emtime = 0

      if uberhol1 == True:
        s1.append(distanz1)
        if uberhol2:
          emtime = 0
    except Exception as e:
      csvprint.error(e)

  def sendt(self,US1TRIG):
    GPIO.output(US1TRIG, True)
    time.sleep(0.00001)
    GPIO.output(US1TRIG, False)


class SENSOR2:
  #Sensor 2 wird initialisiert
  def __init__(self, US2TRIG,US2ECHO):
    self.US2ECHO = US2ECHO
    self.US2TRIG = US2TRIG
    GPIO.setup(self.US2ECHO, GPIO.IN)
    GPIO.setup(self.US2TRIG, GPIO.OUT)
    GPIO.add_event_detect(self.US2ECHO, GPIO.RISING, self.event_callback)

  #Eventfunktion, die aktiviert wird, sobald der Ultraschallsensor Wellen sendet
  def event_callback(self, channel):
    global aktuell
    global uberhol2
    global time2
    global distanz2

    try:

      starttime = time.time()
      dauer = 0

      while GPIO.input(self.US2ECHO)==1 and dauer < 0.39:
          stoptime = time.time()
          dauer = stoptime - starttime

      distanz2 = round(dauer*17150 + anpassung2)

      if distanz2 < 5 or distanz2 > 400:
        distanz2 = 500
#      else:
 #       csvprint.data(0, 'oho')

      csvprint.data(0,distanz2)

      if distanz2 <= limit and uberhol1 and not uberhol2:
        csvprint.data(0,'switsch')
        time2 = time.time()
        uberhol2 = True
        s2.append(distanz2)

        aktuell[5]= abstand/(time2 - time1)
        foto()

      elif distanz2 > limit and uberhol2 and uberhol1 == False:
        uberhol2 = False
        aktuell[3] = aver(s2)
        aktuell[4] = min(s2)
        csvprint.error('print')
        csvprint.datei(aktuell[0], (aktuell[1]+aktuell[3])/2, (aktuell[2]+aktuell[4])/2, aktuell[5])
        aktuell=[0,0,0,0,0,0]
        del s2[:]

      if uberhol2:
        s2.append(distanz2)

    except Exception as e:
      csvprint.error(e)

  def sendt(self,US2TRIG):
    GPIO.output(US2TRIG, True)
    time.sleep(0.00001)
    GPIO.output(US2TRIG, False)


class BUTTON:
  def __init__(self, BUTTONPIN):
    self.BUTTONPIN = BUTTONPIN
    GPIO.setup(self.BUTTONPIN, GPIO.IN)
    GPIO.add_event_detect(self.BUTTONPIN, GPIO.RISING, self.event_callback)

  def event_callback(self, channel):
    self.butthandling()
  def butthandling(self):
    led.on(ROT)
    time.sleep(1)
    led.off(ROT)
    csvprint.feeling(car)
    camera.capture(dirname + 'Fotos/'+ str(datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'))+'.jpg')

    
class LED:
  def __init__(self, ROT,GRUN,GELB):
    self.ROT = ROT
    self.GRUN = GRUN
    self.GELB = GELB
    GPIO.setup(self.ROT, GPIO.OUT)
    GPIO.setup(self.GRUN, GPIO.OUT)
    GPIO.setup(self.GELB, GPIO.OUT)
  def on(self, f):
    GPIO.output(f, True)
  def off(self,f):
    GPIO.output(f, False)

#Diese Klasse ist für das Speichern der Daten zuständig
class CSVPRINT:
  def __init__(self, ERROR, DATEI, DATA):
    self.ERROR = ERROR
    self.DATEI = DATEI
    self.DATA = DATA

#Alle Init-Funktionen schreiben in den 3 Dokumenten die Titel
  def initerror(self):
    with open(ERROR, 'a') as csvfile:
      fieldnames = ['LOG', 'Datum']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames = fieldnames, dialect=dialect)
      writer.writeheader()
      writer.writerow({'LOG': "System erfolgreich gestartet ", 'Datum': datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S')})

  def initdatei(self):
    with open(DATEI, 'a') as csvfile:
      fieldnames = ['LOG','Datum', 'Auto','durchschnittliche Distanz','minimale Distanz','Geschwindigkeit','Gefühl']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect= dialect)
      writer.writeheader()

  def initdata(self):
    with open(DATA, 'a') as csvfile:
      fieldnames = ['Datum','SENSOR1','SENSOR2']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect= dialect)
      writer.writeheader()

#Diese Funktionen werden aufgerufen, um Daten in die Dateien zu schreiben
  def error(self, text):
    with open(ERROR, 'a') as csvfile:
      fieldnames = ['LOG', 'Datum']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames = fieldnames, dialect=dialect)
      writer.writerow({'LOG': text, 'Datum': datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S')})

  def datei(self, auto, durchschnitt, minimal, geschwindigkeit):
    with open(DATEI, 'a') as csvfile:
      fieldnames = ['LOG','Datum', 'Auto','durchschnittliche Distanz','minimale Distanz','Geschwindigkeit', 'Gefühl']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect= dialect)
      writer.writerow({'Datum': datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'),'Auto': auto, 'durchschnittliche Distanz': durchschnitt,
        'minimale Distanz': minimal, 'Geschwindigkeit': geschwindigkeit})

  def feeling(self, auto):
    with open(DATEI, 'a') as csvfile:
      fieldnames = ['LOG','Datum', 'Auto','durchschnittliche Distanz','minimale Distanz','Geschwindigkeit', 'Gefühl']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect= dialect)
      writer.writerow({'Datum': datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'),'Auto': auto, 'Gefühl': 1})


  def data(self, s1, s2):
    with open(DATA, 'a') as csvfile:
      fieldnames = ['DATUM','SENSOR1','SENSOR2']
      dialect = csv.excel()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect= dialect)
      writer.writerow({'DATUM': datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'),'SENSOR1': s1, 'SENSOR2': s2})


#some functions
def foto():
  time.sleep((math.tan(winkel)*aktuell[1])/aktuell[5])
  camera.capture(dirname + 'Fotos/'+ str(datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'))+'.jpg')
  led.on(ROT)
  time.sleep(1)
  led.off(ROT)

def aver(l):
  return sum(l)/len(l)

if __name__ == '__main__':
  x = datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S')
  dirname = '/home/shares/data/' + str(x) +'/'
  os.makedirs(dirname)
  os.makedirs(dirname + 'Fotos/')
  DATA = dirname + 'data.csv'
  DATEI = dirname + 'values.csv'
  ERROR = dirname + 'error.csv'

    #objekte erschaffen
  sensor1 = SENSOR1(US1TRIG,US1ECHO)
  sensor2 = SENSOR2(US2TRIG,US2ECHO)
  button = BUTTON(BUTTONPIN)
  led = LED(ROT,GRUN,GELB)
  csvprint = CSVPRINT(ERROR, DATEI, DATA)
  try:
    #threading
    f = Process(target = foto) #Foto
    led.on(GRUN)

    csvprint.initerror()
    csvprint.initdata()
    csvprint.initdatei()
    while True:
      sensor1.sendt(US1TRIG)
      time.sleep(0.1)
      sensor2.sendt(US2TRIG)
      time.sleep(0.1)
  except KeyboardInterrupt:
    GPIO.cleanup()
    camera.close()
  except Exception as e:
    csvprint.error(e)
  finally :
    GPIO.cleanup()
    camera.close()
