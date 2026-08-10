"""Download screenshots and HTML code for CyberGuard-ID Stitch project screens."""

import json
import ssl
import urllib.request
from pathlib import Path

# Ignore SSL verification issues if any
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "stitch_designs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCREENS = [
    {
        "index": 1,
        "id": "08f6733d6e094e92b23c3f9665c9401b",
        "title": "Ringkasan - CyberGuard-ID (Refined)",
        "slug": "01_ringkasan",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLul-rh-P1If8PYhtlnSw4jg8BW-hrxK7bNnetfEBp8zrGU7bbx5KnyJvQGC5cW-sTDuWOJv8sZHi0NYS7qoyIxjoiy5AASEmMSYvba4rREKrqLS440jESkzSOoRjfJ2uUc3OGce12sn1XmdeRjuWiuBsZy4p_fVpTuuYjSFKao-AroqD9ATiinQdvcO-JVOpJEOw5eWgVUcjvQoqBRUxPsjTLXpc-V9rCLFTxPab0m_QPz6dgWOH_n_GthM",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YTNmNGEyZjcwNzc5OWIzODVjMDU2ZjRiEgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
    {
        "index": 2,
        "id": "61f46755e407401aa19b07e3ea1571d8",
        "title": "Hasil Analisis - CyberGuard-ID (Refined)",
        "slug": "02_hasil_analisis",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLsnlu3NGVZIwTCdZgcuBy8DKV6TWLiqD_I2HMcapzsMAqOMNtC9aqXRKMUMZafeGdjYj0v1BVzHH_4qyn8HaF_A67lmueCsW1osoqTivfHTszT1XWxrDatf5_NOXyXbKV5kdue4O3_Zcp7oWIk0PwjO9MbhyaZ6AEJIexJhd156-CRcpTslamKKREDTdXa70Fv73vsCWfDcgLQXSSv3A41KH169XYvxB7kHSWi0joupQJsJSh9v0h5NFelk",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YWQyZjMxMjEwMzM4NWFkZWViMmI5NzUxEgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
    {
        "index": 3,
        "id": "3b8316ae66e14669a9a3217a0f575e82",
        "title": "Tinjauan Manual - CyberGuard-ID (Refined)",
        "slug": "03_tinjauan_manual",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLvvATRaGdxx0ykQHHlKPUWTBlfea1GhkQQ19PGcyRNsmG-OgldLVohv9XN3vjDF_XMUBZY4Qq8ZfDmYIReahTNEz6_ZezCkKk3ILH9C165dHyU3_NG9zIUvOZJC7zKnrVYjVjeQRvxZgfOvjT0u6UERk9HOW47TGHaGcq4VnSo6O_ksKbn3K72fv99B3p2BSNGsX9sW2BSGBEVyI1Wlf_2tx1K4Z2eAxh2jYyfMkFtW35oxGrYH2uezD-4w",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YWIyN2E4NWYwNzc5YjA3ZGI3MWZjMmExEgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
    {
        "index": 4,
        "id": "129ccf5df93147449d70c88a7a309323",
        "title": "Proses Analisis - CyberGuard-ID (Refined)",
        "slug": "04_proses_analisis",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLuucW5v-q1knaKeCdkuZmNUKhYhGlHSNXnBSUAJGJUaGsOyHdUAEtZOOwFw8NC4eb1lYlsLWBEmSDvYBwZP6neA_ybae8B2tYx_T4F6S09iSTJ1AqeKBLV_D23Gd07yabRQRvtUft81v8jVcndOZGkqqxZoIcq5Vm3BuwVoGfbhWtdEKTtadqDa_buGMAG4yUPTIYJ6tGXMoKh9qgeyfQm7plTbztXzPVxO6EAzfCxk02QW0W8UkD8JigI",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YTNkMWU4OTEwMmE5YmQ2YjMwMGQwZDhiEgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
    {
        "index": 5,
        "id": "09b05e3ede324b2297868dc331883355",
        "title": "Laporan - CyberGuard-ID (Refined)",
        "slug": "05_laporan",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLte-00hv-8KfkoPx8yTIevjTEFQw0K5WAIJXFP7H0dntU5hZGkqlEo13Z4kX-4cBlYEnWuL_YUtjroqpyB_NTPTobYlJhF8SDcwIrjhZ4VIKwUj4rglGy3mEPYvsejBi1VnXx52ozE9e3EqPaYONfH8rpNVmz-D8XgoUxX6Ck5WqhicEz25ycAX60eu2w003ACsWViIkBw1Q3UtRc-MLi3b2YROW8WcrBhqqLau1GbLT08RLCtCczMEIOU",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YWIxY2Y0MzYwNzc5OTNkZTRkMDNiMjYxEgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
    {
        "index": 6,
        "id": "193cffc7168a47cd85d88f85efe9855e",
        "title": "Status Sistem - CyberGuard-ID (Refined)",
        "slug": "06_status_sistem",
        "screenshot_url": "https://lh3.googleusercontent.com/aida/AP1WRLtCAihR_sqKg2en5nG-la_ByQDSASBtXpfrtj6f8FF7Dx8YjdTF1XT5v1odl3JXjkS5HvnnZk2GEiV42nQvotVbBkIIeKQ0kgv0Wec88jIiAVx9JxMoz2-jRRGT5JtZxjyzDOxH5IO8QfKQFbfiy9bdpCi1fNjNc030gmx_8QbSwBBU45bjBj2y4tUg9xc9GAI98aFqwglrFrlGkx9GuZlSKo5mmpM7uiKHSCnx0FL6OwtaNUkejSz5GaDM",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAwMDY1ODg4YWExNzI5NWUwMmE5ODA1YzFiMDc1OTI5EgsSBxDYoOyg8wwYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTU2MjAyNDE4NjUxNjczMTUyNA&filename=&opi=89354086",
    },
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for s in SCREENS:
    print(f"Downloading [{s['index']}/6] {s['title']}...")

    # Download Screenshot
    img_path = OUTPUT_DIR / f"{s['slug']}.png"
    req_img = urllib.request.Request(s["screenshot_url"], headers=headers)
    with urllib.request.urlopen(req_img, context=ctx) as response, open(img_path, "wb") as out_file:
        out_file.write(response.read())
    print(f"  -> Saved Image: {img_path.name} ({img_path.stat().st_size / 1024:.1f} KB)")

    # Download HTML
    html_path = OUTPUT_DIR / f"{s['slug']}.html"
    req_html = urllib.request.Request(s["html_url"], headers=headers)
    with urllib.request.urlopen(req_html, context=ctx) as response, open(html_path, "wb") as out_file:
        out_file.write(response.read())
    print(f"  -> Saved HTML: {html_path.name} ({html_path.stat().st_size / 1024:.1f} KB)")

# Save Metadata JSON
meta_file = OUTPUT_DIR / "metadata.json"
meta_file.write_text(json.dumps(SCREENS, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nAll 6 screens downloaded successfully to: {OUTPUT_DIR}")
