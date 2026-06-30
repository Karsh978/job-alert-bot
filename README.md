# Job Alert Bot — Setup Guide (Hindi + English)

Yeh bot har 30 minute me naye internship/fresher jobs check karta hai aur
naya match milne par tumhare WhatsApp pe message bhej deta hai.

## ⚠️ Important — Imandari se limitation samjho

- **LinkedIn, Naukri, Indeed, Glassdoor, Foundit** — ye sites bots ko block
  karti hain (anti-scraping protection + login wall). Inhe is free script se
  reliably automate nahi kiya ja sakta. Bot har run pe in sites ke direct
  search links print karega taaki tum manually 30 sec me check kar sako.
- **Internshala** — search pages scrape ho sakte hain (no login needed),
  isliye yeh primary auto-source hai.
- **Company career pages** — sirf wahi companies jo Greenhouse/Lever jaisa
  public job-board API use karte hain (Razorpay, Postman, Groww abhi add
  kiye hain — tum aur companies easily add kar sakte ho, README ke last me
  bataya hai kaise).
- **WhatsApp** — Twilio ka FREE Sandbox use ho raha hai. Real WhatsApp
  Business API paid hai aur business verification maangta hai, isliye
  sandbox best free option hai. Limitation: sandbox session 72 hours me
  expire hota hai agar tum bot ko message na bhejo, isliye neeche "keep
  sandbox alive" wala step zaroor follow karo.

## Step-by-Step Setup

### 1. Twilio Account (Free)
1. https://www.twilio.com/try-twilio par free sign up karo.
2. Console me jaake "Messaging" → "Try it out" → "Send a WhatsApp message"
   open karo. Tumhe ek sandbox number milega jaise `+1 415 523 8886` aur
   ek join code jaise `join purple-tiger`.
3. Apne WhatsApp se us number ko message karo: `join purple-tiger`
   (exact code Twilio dashboard se copy karna).
4. Confirmation aa jayega — ab tumhara number sandbox se connected hai.
5. **Keep alive**: har 72 hours me ek baar dobara `join purple-tiger`
   bhejna padega, warna messages aana band ho jayenge. (Chaaho to ek
   phone reminder laga lo.)

### 2. Twilio Credentials nikalo
Twilio Console (https://console.twilio.com) ke main dashboard par:
- `Account SID` → copy karo
- `Auth Token` → copy karo (click "show" to reveal)
- Sandbox WhatsApp number → format: `whatsapp:+14155238886`
- Tumhara number → format: `whatsapp:+91XXXXXXXXXX` (apna number, country code ke saath)

### 3. GitHub Repo banao
1. GitHub par naya repo banao (e.g. `job-alert-bot`).
2. Is project ke saare files (`job_alert.py`, `.github/workflows/job-alert.yml`,
   `seen_jobs.json`, ye README) us repo me push karo.

### 4. GitHub Secrets add karo
Repo → Settings → Secrets and variables → Actions → "New repository secret"
4 secrets add karo:
- `TWILIO_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM` → `whatsapp:+14155238886`
- `TWILIO_TO` → `whatsapp:+91XXXXXXXXXX`

### 5. Done!
GitHub Actions automatically har 30 min me script run karega
(`.github/workflows/job-alert.yml` me schedule set hai). Tum chaaho to
"Actions" tab me jaake "Run workflow" button se manually bhi turant test
kar sakte ho.

## Naye companies add karna (Greenhouse/Lever)
`job_alert.py` me `GREENHOUSE_BOARDS` ya `LEVER_BOARDS` dictionary me
naam aur board-slug add karo. Slug pata karne ka tarika:
- Company ki careers page URL dekho — agar woh Greenhouse use karta hai to
  usually URL me `boards.greenhouse.io/<slug>` dikhega.
- Lever use karne wale companies ka URL `jobs.lever.co/<slug>` jaisa hota hai.

## Limitations (honestly likhi hui)
- Internshala scraping unka HTML structure change hone par toot sakta hai —
  agar bot kaam karna band kar de to selectors (`div.individual_internship`
  etc.) update karne padenge.
- Sirf un companies ke jobs aayenge jo Greenhouse/Lever use karte hain —
  Google, Microsoft, Amazon jaise bade companies apna custom ATS use karte
  hain jo easily scrape nahi hota, unke liye manual check zaroori hai.
- Free GitHub Actions ka schedule kabhi-kabhi 30 min se thoda delay ho sakta
  hai (GitHub ki free tier limitation, guarantee nahi hai exact time pe chale).
