import RPi.GPIO as GPIO
import pygame
import time
import random
import os
from datetime import datetime

# GPIO pinlerinin tanımlanması
TRIG_PIN = 23       # HC-SR04 Trig pini
ECHO_PIN = 24       # HC-SR04 Echo pini
LED_PIN = 17        # Mavi LED pini
BUZZER_PIN = 16     # Buzzer pini
RED_LED_PIN = 12    # Kırmızı LED pini

# GPIO ayarları
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)

# Pygame başlatma
pygame.mixer.init()

# Playlist dosyasını yükleme
def playlist_yukle(dosya_adi):
    try:
        with open(dosya_adi, 'r') as file:
            playlist = [line.strip() for line in file.readlines()]
            valid_playlist = [song for song in playlist if os.path.isfile(song) and song.endswith(".mp3")]
            if not valid_playlist:
                raise Exception("Playlist'te geçerli MP3 dosyası yok.")
            return valid_playlist
    except FileNotFoundError:
        print(f"{dosya_adi} dosyası bulunamadı.")
        return []

# Mesafe ölçümü
def mesafe_olc():
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        pulse_start = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        pulse_end = time.time()
    return (pulse_end - pulse_start) * 34300 / 2  # cm cinsinden mesafe

# Alarm kontrolü
def alarm_kontrol():
    simdi = datetime.now()
    if simdi.hour == 18 and simdi.minute == 0:
        print("Alarm çalıyor! Buzzer ve kırmızı LED aktif.")
        GPIO.output(BUZZER_PIN, GPIO.HIGH)  # Buzzer'ı aktif et
        GPIO.output(RED_LED_PIN, GPIO.HIGH)  # Kırmızı LED'i aktif et
        time.sleep(10)  # Alarm süresi
        GPIO.output(BUZZER_PIN, GPIO.LOW)  # Buzzer'ı kapat
        GPIO.output(RED_LED_PIN, GPIO.LOW)  # Kırmızı LED'i kapat
        time.sleep(60)  # Alarmın yeniden tetiklenmemesi için 1 dakika bekle

# Ana program
try:
    # Playlist yükle
    playlist = playlist_yukle("aaaplaylist.txt")
    if not playlist:
        raise Exception("Playlist boş veya geçerli şarkı bulunamadı. Lütfen 'aaaplaylist.txt' dosyasını kontrol edin.")

    print("Sistem çalışıyor. Ultrasonik sensör ve alarm aktif.")
    
    led_zaman = None
    music_zaman = None
    music_caliyor = False
    current_song_index = 0

    while True:
        # Alarm kontrolü
        alarm_kontrol()

        # Mesafe ölçümü
        mesafe = mesafe_olc()
        print(f"Mesafe: {mesafe:.2f} cm")

        if mesafe < 50:  # 50 cm içinde bir nesne algılandıysa
            print("Hedef algılandı, süreler sıfırlanıyor!")

            # LED'i yak
            GPIO.output(LED_PIN, GPIO.HIGH)
            led_zaman = time.time()  # LED süresini sıfırla

            # Müzik çalıyorsa süreyi sıfırla
            if music_caliyor:
                music_zaman = time.time()

            # Müziği ilk kez başlatıyorsa
            if not music_caliyor:
                pygame.mixer.music.load(playlist[current_song_index])
                pygame.mixer.music.play()
                music_zaman = time.time()
                music_caliyor = True

        # Süreleri kontrol et
        if led_zaman and time.time() - led_zaman > 1800:
            GPIO.output(LED_PIN, GPIO.LOW)  # LED'i kapat
            led_zaman = None

        if music_caliyor:
            if not pygame.mixer.music.get_busy():  # Şarkı bittiğinde sıradaki şarkıya geç
                current_song_index = (current_song_index + 1) % len(playlist)
                pygame.mixer.music.load(playlist[current_song_index])
                pygame.mixer.music.play()

            if music_zaman and time.time() - music_zaman > 1800:  # 30 dakika dolduysa müziği durdur
                pygame.mixer.music.stop()
                music_caliyor = False
                music_zaman = None

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Çıkış yapılıyor...")
    GPIO.cleanup()
    pygame.mixer.quit()
except Exception as e:
    print(f"Hata: {e}")
    GPIO.cleanup()
    pygame.mixer.quit()
