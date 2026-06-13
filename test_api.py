import requests
import json

base_url = "http://127.0.0.1:8000"

def test_api():
    print("Test 1: GET /")
    try:
        res = requests.get(base_url + "/")
        print(res.json())
    except Exception as e:
        print("API no iniciada o falló:", e)
        return

    print("\nTest 2: POST /songs")
    payload = {
        "title": "Wonderwall",
        "artist": "Oasis",
        "bpm": 87,
        "sections": [
            {
                "name": "Intro",
                "order": 1,
                "lines": [
                    {
                        "order": 1,
                        "type": "lyric",
                        "content": "Today is gonna be the day",
                        "chords": [
                            {"chord_name": "Em7", "char_position": 0},
                            {"chord_name": "G", "char_position": 14}
                        ]
                    }
                ]
            }
        ]
    }
    
    res = requests.post(base_url + "/songs/", json=payload)
    if res.status_code == 201:
        song = res.json()
        print(f"Canción creada con ID: {song.get('id')}")
        
        print("\nTest 3: GET /songs/{id}")
        res2 = requests.get(f"{base_url}/songs/{song['id']}")
        print(json.dumps(res2.json(), indent=2))
    else:
        print(f"Error creando canción: {res.status_code} - {res.text}")

if __name__ == "__main__":
    test_api()
