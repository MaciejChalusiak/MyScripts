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

Dostęp z telefonu spoza sieci RPi (Cloudflare Tunnel + Access):
  RPi Zero (sieć IoT) i telefon (inna sieć/inne WiFi) są odizolowane na routerze
  celowo (izolacja klientów), więc zwykłe lokalne IP nie zadziała między nimi.
  Zamiast VPN-a (Tailscale) - który wymaga stałej apki działającej w tle na
  telefonie - używamy Cloudflare Tunnel: RPi łączy się WYCHODZĄCO do sieci
  Cloudflare (bez otwierania portów na routerze, bez zmiany jego ustawień),
  a appka jest dostępna pod zwykłym adresem https:// w przeglądarce, bez
  żadnej dodatkowej apki na telefonie. Logowanie (żeby appka nie była
  publicznie dostępna dla całego internetu) załatwia Cloudflare Access -
  ekran logowania (np. kod na e-mail) pokazuje się PRZED dotarciem ruchu do
  RPi, więc w app.py nie trzeba nic dopisywać.

  Wymagana własna domena (jakikolwiek TLD, ~10-15$/rok u dowolnego
  rejestratora, np. Namecheap/Porkbun/Cloudflare Registrar) - Cloudflare sam
  w sobie jest darmowy (Free plan), ale musi mieć jakąś domenę podpiętą do
  konta, żeby wystawić na niej stały adres i regułę logowania.

  1. Kup domenę u dowolnego rejestratora (jeśli jeszcze nie masz).
  2. Załóż darmowe konto na https://dash.cloudflare.com i dodaj tę domenę
     (Cloudflare poda 2 nameservery - podmień je u rejestratora domeny na te
     wskazane przez Cloudflare; propagacja to zwykle kilkadziesiąt minut do
     kilku godzin).
  3. Na RPi Zero zainstaluj cloudflared:
       curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm.deb -o cloudflared.deb
       sudo dpkg -i cloudflared.deb
  4. Zaloguj i utwórz tunel:
       cloudflared tunnel login      # otworzy link do zalogowania w przeglądarce
       cloudflared tunnel create klima
       cloudflared tunnel route dns klima klima.twojadomena.pl
  5. Skonfiguruj plik ~/.cloudflared/config.yml:
       tunnel: klima
       credentials-file: /home/maciek/.cloudflared/<tunnel-id>.json
       ingress:
         - hostname: klima.twojadomena.pl
           service: http://localhost:5000
         - service: http_status:404
  6. Uruchom jako usługę systemd (autostart + restart po awarii):
       sudo cloudflared service install
       sudo systemctl enable --now cloudflared
       sudo systemctl status cloudflared
  7. W panelu https://one.dash.cloudflare.com (Zero Trust) -> Access ->
     Applications -> dodaj aplikację dla hostname klima.twojadomena.pl,
     z polityką logowania np. "e-mail w liście dozwolonych adresów" (kod
     jednorazowy wysyłany na e-mail, bez hasła do zapamiętania).

  Potem w przeglądarce na telefonie (dowolna sieć, bez żadnej dodatkowej
  apki) wchodzisz na:
    https://klima.twojadomena.pl
  pierwsze logowanie poprosi o kod z e-maila, kolejne wizyty pamiętają sesję
  przez czas ustawiony w polityce Access (np. 24h).
