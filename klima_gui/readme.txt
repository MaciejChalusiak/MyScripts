Adres IP RPi zero W: ssh maciek@192.168.1.124
haslo: na bitwarden

Folder: Desktop/klima

Architektura:
- my_secrets.py    - dane dostępowe (adres IP, token, key) do każdej klimatyzacji Midea
- midea_client.py  - komunikacja z klimatyzacją bezpośrednio przez bibliotekę midea-beautiful-air
                      (bez odpalania subprocess z CLI - lżejsze dla RPi Zero)
- device_controller.py - pętla kontrolna z zewnętrzną histerezą (co 60s mierzy temperaturę
                      w pokoju i przestawia wewnętrzny target klimatyzacji, żeby wymusić
                      chłodzenie albo je zatrzymać; trzyma temperaturę w paśmie ~1 stopnia
                      zamiast domyślnych ~4 stopni klimatyzacji)
- app.py           - serwer Flask z GUI, jeden proces obsługujący wszystkie klimatyzacje
- templates/index.html - strona sterująca (włącz/wyłącz, +/- temperatura), otwierana
                      z telefonu/laptopa pod adresem http://192.168.1.124:5000
- state.json       - zapisywany automatycznie stan (włączone urządzenia + zadana temp),
                      żeby restart usługi (np. po zaniku prądu) przywrócił poprzedni stan

Instalacja na RPi Zero:
  cd /home/maciek/Desktop/klima
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

Uruchomienie jako usługa systemd (autostart + restart po awarii):
  sudo cp klima.service /etc/systemd/system/klima.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now klima.service
  sudo systemctl status klima.service
  journalctl -u klima -f     # podgląd logów

Dostęp z telefonu spoza sieci RPi (Tailscale):
  RPi Zero (sieć IoT) i telefon (inna sieć/inne WiFi) są odizolowane na routerze
  celowo (izolacja klientów), więc zwykłe lokalne IP nie zadziała między nimi.
  Tailscale robi prywatny VPN mesh między urządzeniami przez internet, bez
  zmiany ustawień routera i bez otwierania portów na świat. Plan darmowy
  (Personal) wystarcza w zupełności - do 6 użytkowników, bez limitu urządzeń.

  Na RPi Zero:
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up
    (skrypt pokaże link - zaloguj się w przeglądarce kontem Google/GitHub/Microsoft
    i autoryzuj urządzenie)
    tailscale ip -4        # pokazuje adres RPi w sieci Tailscale, np. 100.x.y.z

  Na telefonie:
    zainstaluj appkę "Tailscale" (App Store / Google Play) i zaloguj się tym
    samym kontem co na RPi

  Potem w przeglądarce na telefonie wchodzisz na:
    http://<tailscale-ip-RPi>:5000
  albo przez MagicDNS (nazwa urządzenia zamiast IP, widoczna w panelu
  https://login.tailscale.com/admin/machines), np.:
    http://klima-pi:5000

  Warunek: sieć, w której siedzi RPi, musi mieć dostęp do internetu (nawet
  jeśli jest odizolowana od innych sieci lokalnych) - Tailscale łączy się
  na zewnątrz, a nie po LAN.
