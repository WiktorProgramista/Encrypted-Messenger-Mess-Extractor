Oto plik `README.md`, który opisuje wymagania, instalację, uruchomienie oraz działanie skryptu.

```markdown
# Media Extractor z czatów Facebook Messenger

Skrypt ten wyodrębnia wszystkie zdjęcia, filmy i GIF-y z plików JSON eksportu czatów Facebook Messenger (lub innych czatów o podobnej strukturze) i kopiuje je do uporządkowanego katalogu `output`, nadając im czytelne nazwy oraz ustawiając oryginalne daty utworzenia.

## Wymagania

- **Python 3.6+** (skrypt testowany na Python 3.9+)
- Zainstalowane biblioteki:
  - `filedate` – do zmiany metadanych plików (daty utworzenia, modyfikacji, dostępu)

### Instalacja zależności

```bash
pip install filedate
```

Żadne inne zewnętrzne biblioteki nie są wymagane (wszystkie pozostałe moduły są w standardowej bibliotece Pythona).

## Przygotowanie plików

1. **Pliki JSON** – muszą znajdować się w tym samym katalogu co skrypt (lub w podkatalogach, ale skrypt automatycznie je odnajdzie, pomijając foldery `output`, `done`, `error`, `media`).  
   Każdy plik JSON powinien mieć strukturę podobną do eksportu z Facebook Messenger, zawierającą:
   - `threadName` lub `title` – nazwa rozmowy (używana do nazewnictwa plików)
   - `messages` – lista wiadomości
   - W każdej wiadomości:
     - `timestamp` (w milisekundach)
     - opcjonalnie lista `media` z obiektami posiadającymi pole `uri` (ścieżka względna lub bezwzględna do pliku medialnego)

   Przykładowy fragment JSON:
   ```json
   {
     "threadName": "Michalina Knaś_30",
     "messages": [
       {
         "timestamp": 1747568151510,
         "media": [
           { "uri": "./media/dcfe3dfd-ad6e-477c-b38d-dc625a7a4f92.jpeg" }
         ]
       }
     ]
   }
   ```

2. **Pliki medialne** – muszą znajdować się w katalogu `media` (obok skryptu) lub w ścieżkach wskazanych w `uri`. Skrypt najpierw szuka plików w katalogu `media` (również w podfolderach), a następnie w całym drzewie bieżącego katalogu.

3. **Struktura katalogów** (przykład):
   ```
   .
   ├── main.py
   ├── media/
   │   ├── dcfe3dfd-ad6e-477c-b38d-dc625a7a4f92.jpeg
   │   ├── 34747aea-b22b-4aef-bbe7-ecf54f88c6e4.mp4
   │   └── ...
   ├── Michalina Knaś_30.json
   ├── Adam Chlebowski_26.json
   └── ...
   ```

## Uruchomienie

W terminalu, będąc w katalogu zawierającym skrypt oraz pliki JSON i folder `media`, wykonaj:

```bash
python main.py
```

lub (w zależności od systemu)

```bash
python3 main.py
```

## Co robi skrypt?

1. **Odczytuje wszystkie pliki `.json`** z bieżącego katalogu (pomijając foldery `output`, `done`, `error`, `media`).
2. Dla każdego JSON-a pobiera nazwę wątku (`threadName` lub `title`).
3. Przechodzi przez wszystkie wiadomości, a w nich przez listę `media`.
4. Dla każdego medium:
   - Lokalizuje fizyczny plik (najpierw w katalogu `media`, potem w całym drzewie).
   - Na podstawie rozszerzenia pliku określa typ: `photos` (`.jpg`, `.jpeg`, `.png`, `.heic`, itp.), `videos` (`.mp4`, `.mov`, `.avi`, itp.) lub `gifs` (`.gif`).
   - Kopiuje plik do odpowiedniego podkatalogu:
     - `output/photos/`
     - `output/videos/`
     - `output/gifs/`
   - Nadaje nową nazwę w formacie:
     ```
     [nazwa wątku]_[YYYYMMDDHHMMSS]_[UUID].[rozszerzenie]
     ```
     gdzie `YYYYMMDDHHMMSS` to data i czas wiadomości (na podstawie `timestamp` z JSON).
   - Ustawia daty **utworzenia**, **modyfikacji** i **dostępu** skopiowanego pliku na tę samą datę (zgodną z timestampem wiadomości).
5. Informuje o postępie w konsoli – ile plików przetworzono dla każdej rozmowy.

## Katalogi pomocnicze

Skrypt automatycznie tworzy następujące foldery (jeśli nie istnieją):

- `output/` – główny katalog wyjściowy
- `output/photos/` – dla zdjęć
- `output/videos/` – dla filmów
- `output/gifs/` – dla GIF-ów
- `done/` – (nieużywany w obecnej wersji, ale tworzony dla kompatybilności)
- `error/` – (jw.)

## Uwagi

- Skrypt **kopiuje** pliki, nie przenosi – oryginalne pliki w katalogu `media` pozostają nietknięte.
- Jeśli plik o podanym `uri` nie zostanie znaleziony, skrypt wyświetli ostrzeżenie i przejdzie dalej.
- `timestamp` w JSON musi być podany w **milisekundach** (standardowy format Facebooka). Skrypt automatycznie konwertuje go na sekundy.
- Jeśli wiadomość nie zawiera pola `media` lub `media` jest pustą listą, jest pomijana.
- Nazwy plików wynikowych są bezpieczne dla systemów plików (usuwane są znaki niedozwolone, jak `<>:"/\|?*`).

## Przykład działania

Wejście:
- `Michalina Knaś_30.json` – zawiera wiadomość z timestampem `1747568151510` i `uri: "./media/dcfe3dfd-ad6e-477c-b38d-dc625a7a4f92.jpeg"`

Wyjście:
- `output/photos/Michalina Knaś_30_20250518223551_abc12345.jpeg`  
  (data: 18 maja 2025, 22:35:51)  
  Metadane pliku ustawione na tę samą datę.

## Rozwiązywanie problemów

| Problem | Możliwe rozwiązanie |
|---------|---------------------|
| `ModuleNotFoundError: No module named 'filedate'` | Zainstaluj `filedate`: `pip install filedate` |
| Pliki medialne nie są znajdowane | Sprawdź, czy ścieżka `uri` w JSON zgadza się z rzeczywistą lokalizacją pliku (najlepiej umieść wszystkie pliki w folderze `media` obok skryptu). |
| Błędy przy zmianie dat na macOS/Linux | Skrypt używa `filedate`, który powinien działać na większości systemów. Jeśli nie, uruchom z `sudo` (rzadko potrzebne). |
| JSON nie zawiera `threadName` | Skrypt użyje wtedy `title` lub domyślnie `"unknown"`. |

## Licencja

Skrypt jest udostępniany bez żadnej gwarancji. Możesz go dowolnie modyfikować i używać.
```

Plik należy zapisać jako `README.md` (lub `README.me`, ale standardowo `.md`). Zawiera on wszystkie niezbędne informacje dla użytkownika końcowego.
