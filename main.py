import os
import json
import re
from datetime import datetime
import filedate
import shutil
import uuid
import string
import time

# Wzorzec dla plików JSON – wszystkie .json
pattern = re.compile(r'.*\.json')

# Katalogi wyjściowe
output_dir = 'output'
output_dir_photos = os.path.join(output_dir, "photos")
output_dir_videos = os.path.join(output_dir, "videos")
output_dir_gifs = os.path.join(output_dir, "gifs")
done_dir = 'done'
error_dir = 'error'

# Katalog z mediami (w tym samym miejscu co skrypt)
MEDIA_DIR = os.path.join(os.getcwd(), 'media')

# ---------- Funkcje pomocnicze ----------
def find_json_files():
    """Zwraca listę ścieżek do plików JSON w bieżącym katalogu (pomijając katalogi systemowe)."""
    json_files = []
    exclude_dirs = {output_dir, done_dir, error_dir, 'media'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in files:
            if pattern.match(filename):
                full_path = os.path.join(root, filename)
                json_files.append(full_path)
    return json_files

def get_media_type_from_extension(file_path):
    """Określa typ medium na podstawie rozszerzenia pliku."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.heic', '.bmp', '.tiff']:
        return 'photos'
    elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        return 'videos'
    elif ext == '.gif':
        return 'gifs'
    else:
        return 'photos'  # domyślnie zdjęcie

def move_to_output(old_path, media_type, thread_name, timestamp_ms):
    """Kopiuje plik do odpowiedniego podkatalogu output i nadaje nową nazwę."""
    # timestamp_ms to milisekundy, zamieniamy na sekundy
    creation_timestamp = timestamp_ms // 1000
    creation_date = datetime.fromtimestamp(creation_timestamp)
    creation_date_str = creation_date.strftime('%Y%m%d%H%M%S')
    file_extension = os.path.splitext(old_path)[1]
    # Oczyszczenie nazwy wątku z niedozwolonych znaków
    clean_name = re.sub(r'[<>:"/\\|?*]', '', thread_name)
    clean_name = clean_name.strip()
    if not clean_name:
        clean_name = "unknown"
    new_file_name = f"{clean_name}_{creation_date_str}_{uuid.uuid4()}{file_extension}"

    if media_type == "photos":
        output_path = output_dir_photos
    elif media_type == "videos":
        output_path = output_dir_videos
    elif media_type == "gifs":
        output_path = output_dir_gifs
    else:
        output_path = output_dir

    new_path = os.path.join(output_path, new_file_name)
    shutil.copy(old_path, new_path)
    return new_path, creation_timestamp

def change_metadata_date(new_path, creation_timestamp):
    """Ustawia daty created, modified, accessed na podstawie timestampa (w sekundach)."""
    try:
        creation_date = datetime.fromtimestamp(creation_timestamp)
        file_path = filedate.File(new_path)
        file_path.set(
            created=creation_date,
            modified=creation_date,
            accessed=creation_date
        )
        print(f"   Zmieniono metadane dla {os.path.basename(new_path)} -> {creation_date}")
    except Exception as e:
        print(f"   Ostrzeżenie: nie można zmienić dat dla {new_path}: {e}")

def find_media_file(uri, json_file_path):
    """
    Odnajduje fizyczny plik medialny na podstawie uri z JSON.
    Priorytet:
    1. Bezpośrednie rozwinięcie ścieżki względem katalogu skryptu (np. ./media/plik.jpg)
    2. Wyszukiwanie po nazwie pliku w katalogu 'media'
    3. Wyszukiwanie po nazwie pliku w całym bieżącym drzewie (pomijając katalogi wykluczone)
    """
    # Normalizacja: usuwamy wiodące './' jeśli występuje
    if uri.startswith('./'):
        uri = uri[2:]
    
    # Próba 1: ścieżka względem katalogu roboczego
    abs_path = os.path.join(os.getcwd(), uri)
    if os.path.exists(abs_path):
        return abs_path
    
    # Próba 2: szukamy w katalogu 'media' po samej nazwie pliku
    filename = os.path.basename(uri)
    if os.path.exists(MEDIA_DIR):
        for root, _, files in os.walk(MEDIA_DIR):
            if filename in files:
                return os.path.join(root, filename)
    
    # Próba 3: przeszukanie całego drzewa (ale pomijając katalogi wykluczone)
    exclude_dirs = {output_dir, done_dir, error_dir, 'media'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        if filename in files:
            return os.path.join(root, filename)
    
    return None

# ---------- Tworzenie niezbędnych katalogów ----------
for d in [output_dir, output_dir_photos, output_dir_videos, output_dir_gifs, done_dir, error_dir]:
    os.makedirs(d, exist_ok=True)

# ---------- Główna pętla ----------
json_files = find_json_files()
print(f"Znaleziono {len(json_files)} plików JSON do przetworzenia")

for file_path in json_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Błąd ładowania {file_path}: {e}")
        continue

    # Pobranie nazwy wątku (threadName) lub title jako fallback
    thread_name = data.get('threadName') or data.get('title') or 'unknown'
    # Usunięcie niedrukowalnych znaków
    printable_chars = set(string.printable)
    thread_name = ''.join(filter(lambda x: x in printable_chars, thread_name))

    print(f"\n-> Przetwarzanie: {thread_name}")
    print(f"   Plik JSON: {file_path}")
    count = 0

    try:
        messages = data.get('messages', [])
        for message in messages:
            # Sprawdzamy, czy wiadomość zawiera jakieś media
            media_list = message.get('media')
            if not media_list:
                continue
            timestamp_ms = message.get('timestamp')
            if not timestamp_ms:
                print(f"   Ostrzeżenie: wiadomość bez timestamp, pomijam media: {media_list}")
                continue

            for media_item in media_list:
                uri = media_item.get('uri')
                if not uri:
                    continue

                actual_path = find_media_file(uri, file_path)
                if not actual_path:
                    print(f"   Ostrzeżenie: nie znaleziono pliku dla uri: {uri}")
                    continue

                # Określamy typ mediów na podstawie rozszerzenia
                media_type = get_media_type_from_extension(actual_path)
                new_path, creation_ts = move_to_output(actual_path, media_type, thread_name, timestamp_ms)
                change_metadata_date(new_path, creation_ts)
                count += 1
                print(f"   Przetworzono {media_type}: {os.path.basename(actual_path)}")

        print(f"-> Zakończono: {thread_name} – {count} plików medialnych")
    except Exception as ex:
        print(f"-> Błąd podczas przetwarzania {thread_name}: {ex}")
        import traceback
        traceback.print_exc()

print("\nPrzetwarzanie zakończone!")