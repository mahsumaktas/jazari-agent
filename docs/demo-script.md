# Jazari Demo — Sessiz Ekran Kaydi + AI Seslendirme

Ses dosyalari: `docs/demo-audio/` (m4a)
Sen hic konusmuyorsun. Sadece ekran kaydini cek, sonra sesleri timeline'a yerlestir.

---

## ADIM 1: Ekran Kaydini Cek (QuickTime, ~4 dk)

QuickTime > File > New Screen Recording > mikrofon KAPALI

### Sahne 1 — Giris [~15 sn]
- Jazari acik beklesin, 3 saniye dur
- Ses: `01-intro.m4a` (sonra eklenecek)

### Sahne 2 — Onboarding [~55 sn]
- Incognito tab ac, Jazari'ye baglan
- Jazari greeting yapar, bekle
- Yaz: `My name is Mehmet` → cevap bekle
- Ses: `02-onboarding-start.m4a`
- Yaz: `I'm a software engineer` → cevap bekle
- Ses: `02b-onboarding-icf.m4a`
- Jazari Wheel of Life sorarsa yaz: `Career 7, Health 4, Finances 6, Relationships 8`
- Ses: `02c-wheel-of-life.m4a`

### Sahne 3 — Voice Mode [~40 sn]
- Mikrofon butonuna tikla
- Ingilizce soyle (veya bu sahneyi atla ve text'te kal):
  "I want to start running. My goal is five K by next month."
- Cevap bekle, mikrofonu kapat
- Ses: `03-voice.m4a`
- NOT: Voice'ta konusmak istemezsen bu sahneyi ATLA, diger sahneler yeterli

### Sahne 4 — Memory Recall [~30 sn]
- Text mode'a gec
- Yaz: `What do you know about me?`
- Cevap gelince sag panelleri goster (mouse ile uzerine gel)
- Ses: `04-memory.m4a` + `04b-dashboard.m4a`

### Sahne 5 — Sub-Agents [~25 sn]
- Yaz: `How many calories should I eat for 5K training?`
- "Consulting search..." yazisini goster
- Cevap bekle
- Ses: `05-subagents.m4a`

### Sahne 6 — Cloud Run [~25 sn]
- Yeni tab: Google Cloud Console > Cloud Run > jazari-agent
- Service'in calistigini goster
- Ses: `06-architecture.m4a`

### Sahne 7 — Kapanis [~15 sn]
- Jazari tab'ina geri don
- 3 saniye bekle
- Ses: `07-closing.m4a`

Kaydi durdur.

---

## ADIM 2: Video Editi (iMovie veya CapCut)

1. iMovie ac > New Movie
2. Ekran kaydini timeline'a surukle
3. Ses dosyalarini (m4a) sirasyla dogru sahnelere yerlestir
4. Gereksiz bekleme/hata kisimlarini kes
5. Export: 1080p, YouTube'a yukle (Unlisted)

---

## ADIM 3: Devpost Submit

1. YouTube linkini al
2. devpost.com > Jazari projesi > Submit
3. SUBMISSION.md icerigini yapistir
4. Video linkini ekle
5. Kategori: Live Agents
6. "Built with": Google ADK, Gemini, Cloud Run, Firestore, LanceDB

---

## SES DOSYALARI LISTESI

| Dosya | Sure | Sahne |
|-------|------|-------|
| 01-intro.m4a | ~8sn | Giris |
| 02-onboarding-start.m4a | ~4sn | Onboarding baslangic |
| 02b-onboarding-icf.m4a | ~5sn | ICF aciklama |
| 02c-wheel-of-life.m4a | ~3sn | Wheel of Life |
| 03-voice.m4a | ~6sn | Voice mode |
| 04-memory.m4a | ~7sn | Memory recall |
| 04b-dashboard.m4a | ~4sn | Dashboard |
| 05-subagents.m4a | ~8sn | Sub-agents |
| 06-architecture.m4a | ~9sn | Architecture |
| 07-closing.m4a | ~6sn | Kapanis |
