from ESP_uNetwork import ESP_uNetwork
from ESP_MyMQTT import ESP_MyMQTT
from machine import Pin, Timer
import btree

# Tematy mqtt
topic_availability = "home/water/availability"
topic_state = "home/water/state"

# Konfiguracja pinów
led = Pin(2, Pin.OUT)
count_pin = Pin(5, Pin.IN, Pin.PULL_UP)

# Obiekt timera do cyklicznego wywoływania callbacku
timer = Timer(0)

# Zmienne globalne
key_lock = 0
counter = 0
sum = 0

# Konfiguracja i uruchomienie WiFi
myNet = ESP_uNetwork("config.json")
myNet.connect_to_AP()

# Konfiguracja i uruchomienie clienta mqtt
Water_meter = ESP_MyMQTT("config.json")
Water_meter.connect_and_subscribe()
Water_meter.send_state(topic_availability, "online")


# Funkcja odczytująca dane zapisane lokalnie
def get_data_local(id):
    print("Pobieram z lokalnej bazy danych...")
    f = open("myData.txt", "r")
    db = btree.open(f)
    value = db[id]
    db.flush()
    db.close()
    f.close()
    return value


# Funkcja zapisująca dane do pamięci (baza danych)
def save_data_local(id, data):
    print("Zapisuje do lokalnej bazy danych...")
    f = open("myData.txt", "w+b")
    db = btree.open(f)
    db[id] = str(data)
    db.flush()
    db.close()
    f.close()


def save_data_remote(data):
    print("Zapisuje do zdalnej bazy danych...")
    Water_meter.send_state(topic_availability, "online")
    Water_meter.send_state(topic_state, bytes(str(data), 'utf-8'))


# Funkcja zliczająca impulsy kontaktronu (eliminacja drgań styków)
def check_count_pin():
    global key_lock, counter, sum
    if ((not key_lock) and (not count_pin.value())):
        key_lock = 300

        counter += 1
        sum += 1
    elif (key_lock and count_pin.value()):
        key_lock -= 1


# Callback od przerwania timera 0
def timer_callback(timer):
    global counter, sum
    led.value(0)

    save_data_local("value_sum", sum)
    save_data_remote(sum)

    print("counter")
    print(counter)
    print("sum")
    print(sum)
    print("")

    counter = 0
    led.value(1)


sum = int(get_data_local("value_sum").decode("utf-8"))
print("Pobrana wartosc: ")
print(sum)

timer.init(period=60000, mode=Timer.PERIODIC, callback=timer_callback)
led.value(1)                # Led off when ready

while True:
    check_count_pin()




