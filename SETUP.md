# 🕹️ Profile Setup — 3 Step (5 minute)

## Step 1 — Files upload karo
1. GitHub pe `irfaaan` naam ka repo kholo (agar nahi bana to banao — naam **bilkul** username jaisa hona chahiye).
2. **Add file → Upload files** pe click karo.
3. Is zip ki **saari files** drag-drop karo — `README.md`, `games/` folder, `.github/` folder — phir **Commit changes**.

## Step 2 — Actions ko likhne ki permission do (warna board update nahi hoga)
1. Repo me **Settings → Actions → General** kholo.
2. Neeche **Workflow permissions** me **"Read and write permissions"** select karo.
3. **Save** dabao.

## Step 3 — Test karo
1. Apni profile kholo: `github.com/irfaaan`
2. **Terminal Arcade** section me kisi khaali cell pe click karo → ek issue page khulega → **Submit** dabao (kuch likhne ki zaroorat nahi).
3. 20–30 second me board update ho jayega, machine apni chaal chalegi, aur issue khud **auto-close** ho jayega.

## Optional — Snake animation
Snake wali line ke liye [Platane/snk](https://github.com/Platane/snk) workflow lagana parega (ek workflow file + `output` branch). Chaho to baad me laga lena — uske baghair bhi sab kuch chalega, bas snake ki jagah khaali hogi.

## Games kaise kaam karti hain
- Har click ek **prefilled issue** kholta hai (title me move chhupa hota hai, tumhe kuch type nahi karna).
- GitHub Action issue dekhte hi `games/tictactoe.py` / `games/connect4.py` chalata hai.
- Script board update karke README me **commit** karta hai, phir issue **close** kar deta hai taake issues ki list saaf rahe.
- **Tic-Tac-Toe** bot minimax khelta hai (25% chance thoda "cocky" ho jata hai taake jeetna mumkin ho).
- **Connect 4** bot jeetne wali chaal pakarta hai, tumhari jeet block karta hai, aur center pasand karta hai.
