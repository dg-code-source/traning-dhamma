import json

manifest_path = 'AjhanSumedho/playlist_manifest.json'
with open(manifest_path, 'r', encoding='utf-8') as f:
    videos = json.load(f)

for v in videos:
    v['url'] = f"https://www.youtube.com/watch?v={v['video_id']}"

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(videos, f, indent=2, ensure_ascii=False)

print(f"Updated all {len(videos)} entries with pre-fetched explicit URLs in {manifest_path}.")
